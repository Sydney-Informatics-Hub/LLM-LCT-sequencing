import logging
import os
import time
import traceback
from io import BytesIO
from pathlib import Path
from typing import Callable, Optional

import openai
from openai.error import AuthenticationError, APIConnectionError
from pandas import DataFrame

from annotation.model import AnnotationService
from annotation.model.data_structures import SequenceTuple
from annotation.model.import_export import ImportExportService
from annotation.view.global_notifiers import NotifierService


class AnnotationController:
    MIN_SEQUENCE_ID: int = 1
    OPENAI_API_KEY_ENVIRON: str = 'OPENAI_API_KEY'

    def __init__(self, annotation_service: AnnotationService,
                 notifier_service: NotifierService,
                 import_export_service: ImportExportService,
                 llm_examples_path: Path,
                 llm_definitions_path: Path,
                 llm_zero_prompt_path: Path,
                 llm_cost_path: Path,
                 log_file_path: Path,
                 debug: bool = False):
        AnnotationController.configure_logging(log_file_path, debug)

        self.llm_examples_path: Path = llm_examples_path
        self.llm_definitions_path: Path = llm_definitions_path
        self.llm_zero_prompt_path: Path = llm_zero_prompt_path
        self.llm_cost_path: Path = llm_cost_path
        self.llm_post_process_path: Optional[str] = None

        self.llm_prepared: bool = False

        self.annotation_service: AnnotationService = annotation_service
        self.notifier_service: NotifierService = notifier_service
        self.import_export_service: ImportExportService = import_export_service

        self._update_display_callables: list[Callable] = []
        self.curr_sequence_id: int = 1

        # Stores the cost and time estimates of the LLM processing currently being done.
        self.cost_time_estimates: Optional[dict[str, float]] = None

        self.loading_msg: Optional[str] = None

        self.notifier_service.clear_all()

    @staticmethod
    def configure_logging(log_file_path: Path, debug: bool = False):
        with open(log_file_path, 'w') as log_f:
            log_f.write("")

        if debug:
            log_level = logging.DEBUG
        else:
            log_level = logging.WARN

        logging.basicConfig(
            filename=str(log_file_path.resolve()),
            filemode='w',
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def display_error(self, error_msg: str):
        logging.error(f"Error displayed: {error_msg}")
        self.notifier_service.notify_error(error_msg)

    def display_success(self, success_msg: str):
        logging.info(f"Success displayed: {success_msg}")
        self.notifier_service.notify_success(success_msg)

    def display_info(self, info_msg: str):
        logging.info(f"Info displayed: {info_msg}")
        self.notifier_service.notify_info(info_msg)

    def set_loading_msg(self, loading_msg: str, *args, **kwargs):
        self.loading_msg = loading_msg
        self.update_displays()

    def stop_loading_indicator(self):
        self.loading_msg = None
        self.update_displays()

    def get_loading_msg(self) -> Optional[str]:
        return self.loading_msg

    def add_update_text_display_callable(self, update_text_display_callable: Optional[Callable]):
        logging.debug(
            f"add_update_text_display_callable called. Args: update_text_display_callable: {str(update_text_display_callable)}")
        if (type(update_text_display_callable) is not None) and (not callable(update_text_display_callable)):
            raise TypeError("update_text_display_callable must be either None or a callable")
        self._update_display_callables.append(update_text_display_callable)

    def update_displays(self):
        for update_callable in self._update_display_callables:
            update_callable()

    # Data access methods

    def get_text(self) -> str:
        return self.annotation_service.get_text()

    def get_all_clause_text(self) -> dict[int, str]:
        return self.annotation_service.get_all_clause_text()

    def get_curr_sequence_ranges(self) -> Optional[SequenceTuple]:
        try:
            return self.annotation_service.get_sequence_clause_ranges(self.curr_sequence_id)
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            return None

    def get_curr_sequence_linkage_words(self) -> Optional[list[str]]:
        try:
            return self.annotation_service.get_sequence_linkage_words(self.curr_sequence_id)
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            return None

    def get_all_classifications(self) -> list[str]:
        return self.annotation_service.get_all_sequence_classifications()

    def get_predicted_classifications(self) -> list[str]:
        try:
            return self.annotation_service.get_sequence_predict_classes(self.curr_sequence_id)
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            return []

    def get_correct_classifications(self) -> list[str]:
        try:
            return self.annotation_service.get_sequence_correct_classes(self.curr_sequence_id)
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            return []

    def get_reasoning(self) -> str:
        try:
            return self.annotation_service.get_sequence_reasoning(self.curr_sequence_id)
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            return ""

    def get_sequence_count(self) -> int:
        try:
            return self.annotation_service.get_sequence_count()
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            return -1

    def get_cost_time_estimates(self) -> Optional[tuple[float, float]]:
        return self.cost_time_estimates

    # Data control methods

    def load_source_file(self, source_file_content: BytesIO, source_filetype: str):
        try:
            self.set_loading_msg("Loading source file")
            load_source_duration_start = time.time()
            self.annotation_service.load_source_file(source_file_content, source_filetype)
            load_source_duration_total = time.time() - load_source_duration_start
            logging.info(f"Source file loading time: {load_source_duration_total} s")
            self.display_success("File successfully loaded")
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            self.display_error(str(e))

        self.stop_loading_indicator()
        self.update_displays()

    def prepare_llm_processor(self, llm_definitions: Optional[BytesIO] = None,
                              llm_examples: Optional[BytesIO] = None,
                              llm_zero_prompt: Optional[BytesIO] = None):
        if llm_definitions is not None:
            with open(self.llm_definitions_path, 'wb') as f:
                f.write(llm_definitions.read())
        if llm_examples is not None:
            with open(self.llm_examples_path, 'wb') as f:
                f.write(llm_examples.read())
        if llm_zero_prompt is not None:
            with open(self.llm_zero_prompt_path, 'wb') as f:
                f.write(llm_zero_prompt.read())

        self.annotation_service.initialise_llm_processor(self.llm_examples_path, self.llm_definitions_path,
                                                         self.llm_zero_prompt_path, self.set_loading_msg)
        self.cost_time_estimates = self.annotation_service.calculate_llm_cost_time_estimates(self.llm_cost_path)

        self.llm_prepared = True

    def llm_process_sequences(self):
        if os.environ.get(AnnotationController.OPENAI_API_KEY_ENVIRON) is None:
            self.display_error("No valid OpenAI API key found. Please enter your OpenAI API key.")
            return

        try:
            self.set_loading_msg("Performing LLM sequence classification")
            llm_process_duration_start = time.time()

            self.llm_post_process_path = self.annotation_service.perform_llm_processing()

            llm_process_duration_total = time.time() - llm_process_duration_start
            logging.info(f"LLM process time: {llm_process_duration_total} s")

            sequence_df: DataFrame = self.import_export_service.import_file(self.llm_post_process_path, "csv")
            self.annotation_service.build_datastore(sequence_df)

            self.display_success("LLM classification complete")
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            self.display_error(str(e))

        self.cost_time_estimates = None
        self.stop_loading_indicator()
        self.update_displays()

    def load_preprocessed_sequences(self, preprocessed_content: Optional[BytesIO],
                                    preprocessed_filetype: Optional[str]):
        if preprocessed_content is None:
            self.display_error("No preprocessed file provided")
            return
        if preprocessed_filetype is None:
            self.display_error("Invalid filetype for preprocessed file")
            return

        try:
            self.set_loading_msg("Loading preprocessed file")
            preprocessed_load_duration_start = time.time()

            preprocessed_df: DataFrame = self.import_export_service.import_file(preprocessed_content, preprocessed_filetype)
            self.annotation_service.build_datastore(preprocessed_df)

            preprocessed_load__duration_total = time.time() - preprocessed_load_duration_start
            logging.info(f"Preprocessed file load time: {preprocessed_load__duration_total} s")
            self.display_success("Preprocessed file loading complete")
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            self.display_error(str(e))

        self.stop_loading_indicator()
        self.update_displays()

    def set_api_key(self, key: str) -> bool:
        try:
            openai.api_key = key
            _ = openai.Model.list()
            self.display_success("Valid API successfully loaded")
        except AuthenticationError as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            self.display_error(str(e))
            return False
        except APIConnectionError as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            self.display_error("Something is wrong with your network connection. Please try again.")
            return False
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            self.display_error("Something went wrong when validating API Key. Please try again.")
            return False

        os.environ[AnnotationController.OPENAI_API_KEY_ENVIRON] = key
        return True

    def next_sequence(self):
        logging.debug("next_sequence called")

        num_sequences: int = self.annotation_service.get_sequence_count()
        if self.curr_sequence_id < num_sequences:
            self.curr_sequence_id += 1
        self.update_displays()

    def prev_sequence(self):
        logging.debug("prev_sequence called")

        if self.curr_sequence_id > AnnotationController.MIN_SEQUENCE_ID:
            self.curr_sequence_id -= 1
        self.update_displays()

    def set_correct_classifications(self, classifications: list[str]):
        logging.debug(f"set_correct_classifications called. Args: classifications: {classifications}")

        try:
            self.annotation_service.set_sequence_correct_classes(self.curr_sequence_id, classifications)
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())

    def add_sequence(self, clause_a_id: int, clause_b_id: int) -> int:
        logging.debug(f"add_sequence called. Args: clause_a_id: {clause_a_id}, clause_b_id: {clause_b_id}")

        try:
            new_id: int = self.annotation_service.create_sequence(clause_a_id, clause_b_id)
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            new_id = -1

        if self.llm_prepared:
            # If the LLM has already been prepared, a change to the sequences will require preparing the LLM again
            self.prepare_llm_processor()

        self.update_displays()

        return new_id

    def delete_curr_sequence(self):
        logging.debug(f"delete_curr_sequence called. Curr sequence id: {self.curr_sequence_id}")

        try:
            self.annotation_service.delete_sequence(self.curr_sequence_id)
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            self.update_displays()
            return

        # The sequence index must be decreased if the deleted sequence was not the first sequence
        if self.curr_sequence_id > AnnotationController.MIN_SEQUENCE_ID:
            self.curr_sequence_id -= 1

        if self.llm_prepared:
            # If the LLM has already been prepared, a change to the sequences will require preparing the LLM again
            self.prepare_llm_processor()

        # The display must be updated to reflect the deletion
        self.update_displays()

    def export(self, filetype: str) -> Optional[BytesIO]:
        try:
            return self.import_export_service.export(self.annotation_service.get_dataframe_for_export(), filetype)
        except Exception as e:
            logging.error(str(e) + '\n' + traceback.format_exc())
            self.display_error(str(e))
            return

    def get_export_file_formats(self) -> list[str]:
        return self.import_export_service.get_filetypes()
