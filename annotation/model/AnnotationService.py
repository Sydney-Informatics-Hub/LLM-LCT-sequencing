from io import BytesIO
from pathlib import Path
from typing import Optional, Callable

from pandas import DataFrame

from annotation.model.clausing.SequencingTool import SequencingTool
from annotation.model.data_structures import ClauseSequence, Classification, SequenceTuple
from annotation.model.database import AnnotationDAO, DatastoreHandler
from annotation.model.database import (llm_data_store_dir, ref_text_ds_path, clauses_ds_path,
                                       sequences_ds_path, pre_llm_sequence_path)
from annotation.model.clausing import SourceFileClauser
from llm import LLMProcess


class AnnotationService:
    def __init__(self):
        self.annotation_dao: AnnotationDAO = AnnotationDAO(ref_text_ds_path, clauses_ds_path, sequences_ds_path)
        self.annotation_dao.clear_all_data_stores()
        self.datastore_handler: DatastoreHandler = DatastoreHandler(self.annotation_dao)

        self.llm_processor: Optional[LLMProcess] = None

    def load_source_file(self, source_file_content: BytesIO, filetype: str):
        self.annotation_dao.clear_all_data_stores()

        source_loader: SourceFileClauser = SourceFileClauser(source_file_content, filetype)
        text_content: str = source_loader.get_text()
        self.datastore_handler.build_text_datastore(text_content)

        clause_df: DataFrame = source_loader.generate_clause_dataframe()
        sentence_df: DataFrame = source_loader.generate_sentence_dataframe()
        sequence_generator = SequencingTool(clause_df, sentence_df)
        sequence_df = sequence_generator.generate_initial_sequence_df()
        self.datastore_handler.build_clause_datastores(sequence_df)

    def initialise_llm_processor(self, llm_examples_path: Path,
                                 llm_definitions_path: Path,
                                 llm_zero_prompt_path: Path,
                                 progress_update_fn: Callable):
        self.datastore_handler.update_pre_llm_sequence_file(str(pre_llm_sequence_path.resolve()))
        self.llm_processor = LLMProcess(filename_pairs=str(pre_llm_sequence_path.resolve()),
                                        filename_text=str(ref_text_ds_path.resolve()),
                                        filename_examples=str(llm_examples_path.resolve()),
                                        filename_definitions=str(llm_definitions_path.resolve()),
                                        filename_zero_prompt=str(llm_zero_prompt_path.resolve()),
                                        outpath=str(llm_data_store_dir.resolve()),
                                        progress_update_fn=progress_update_fn)

    def calculate_llm_cost_time_estimates(self, llm_cost_path: Path) -> tuple[float, float]:
        if self.llm_processor is None:
            raise ValueError("LLM process called but no LLM processor is set")

        estimates = self.llm_processor.estimate_compute_cost(str(llm_cost_path.resolve()))

        if (estimates['compute_time'] is None) or (estimates['costs'] is None):
            raise ValueError("Error calculating LLM process time and costs")

        return float(estimates['costs']), float(estimates['compute_time'])

    def perform_llm_processing(self) -> str:
        if self.llm_processor is None:
            raise ValueError("LLM process called but no LLM processor is set")

        return self.llm_processor.run()

    def build_datastore(self, master_sequence_df: DataFrame):
        self.datastore_handler.update_sequence_datastores(master_sequence_df)

    def get_dataframe_for_export(self) -> DataFrame:
        return self.datastore_handler.build_export_dataframe()

    def get_text(self) -> str:
        return self.annotation_dao.get_text()

    def get_all_clause_text(self) -> dict[int, str]:
        return self.annotation_dao.get_all_clause_text()

    def get_sequence_count(self) -> int:
        return self.annotation_dao.get_sequence_count()

    def get_sequence_clause_ranges(self, sequence_id: int) -> Optional[SequenceTuple]:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_id(sequence_id)
        if sequence is None:
            return None

        return sequence.get_clause_ranges()

    def get_sequence_linkage_words(self, sequence_id: int) -> Optional[list[str]]:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_id(sequence_id)
        if sequence is None:
            return None

        return sequence.get_linkage_words()

    def get_all_sequence_classifications(self) -> list[str]:
        return [c.name for c in Classification]

    def get_sequence_predict_classes(self, sequence_id: int) -> list[str]:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_id(sequence_id)
        if sequence is None:
            return []

        classifications: Optional[list[Classification]] = sequence.get_predicted_classes()
        if classifications is None:
            return []
        else:
            return [c.name for c in classifications]

    def get_sequence_correct_classes(self, sequence_id: int) -> list[str]:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_id(sequence_id)
        if sequence is None:
            return []

        classifications: Optional[list[Classification]] = sequence.get_correct_classes()
        if classifications is None:
            return []
        else:
            return [c.name for c in classifications]

    def set_sequence_correct_classes(self, sequence_id: int, classifications: list[str]):
        correct_classes: list[int] = []
        for class_str in classifications:
            try:
                correct_class = Classification[class_str].value
            except KeyError:
                continue
            correct_classes.append(correct_class)

        self.annotation_dao.update_sequence_classifications(sequence_id, correct_classes)

    def get_sequence_reasoning(self, sequence_id: int) -> str:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_id(sequence_id)
        if sequence is None:
            return ''

        return sequence.get_reasoning()

    def create_sequence(self, clause_a_id: int, clause_b_id: int) -> int:
        return self.annotation_dao.create_sequence(clause_a_id, clause_b_id)

    def delete_sequence(self, sequence_id: int):
        self.annotation_dao.delete_sequence(sequence_id)
