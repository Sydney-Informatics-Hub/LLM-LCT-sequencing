import logging
import traceback
from typing import Callable, Optional

from annotation.model import AnnotationService
from annotation.view.notifications import NotifierService

# Type alias for complex tuples
ClauseTuple = tuple[int, int]
ClauseSequenceTuple = tuple[ClauseTuple, ClauseTuple]


class AnnotationController:
    MIN_SEQUENCE_ID: int = 1

    def __init__(self, annotation_service: AnnotationService, notifier_service: NotifierService,
                 log_file_path: str, debug: bool = False):
        AnnotationController.configure_logging(log_file_path, debug)

        self.annotation_service: AnnotationService = annotation_service
        self.notifier_service: NotifierService = notifier_service
        self.curr_sequence_id: int = 1

        self._update_display_callables: list[Callable] = []

    @staticmethod
    def configure_logging(log_file_path: str, debug: bool = False):
        with open(log_file_path, 'w') as log_f:
            log_f.write("")

        if debug:
            log_level = logging.DEBUG
        else:
            log_level = logging.WARN

        logging.basicConfig(
            filename=log_file_path,
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

    def add_update_text_display_callable(self, update_text_display_callable: Optional[Callable]):
        logging.debug(f"add_update_text_display_callable called. Args: update_text_display_callable: {str(update_text_display_callable)}")
        if (type(update_text_display_callable) is not None) and (not callable(update_text_display_callable)):
            raise TypeError("update_text_display_callable must be either None or a callable")
        self._update_display_callables.append(update_text_display_callable)

    def update_displays(self):
        for update_callable in self._update_display_callables:
            update_callable()

    # Data access methods

    def get_text(self) -> str:
        return self.annotation_service.get_text()

    def get_clauses(self) -> list[tuple[int, str]]:
        return self.annotation_service.get_clauses()

    def get_curr_sequence(self) -> Optional[ClauseSequenceTuple]:
        try:
            return self.annotation_service.get_sequence_clause_ranges(self.curr_sequence_id)
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

    # Data control methods

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

        # The display must be updated to reflect the deletion
        self.update_displays()
