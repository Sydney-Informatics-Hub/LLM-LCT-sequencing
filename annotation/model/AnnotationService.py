from typing import Optional

from annotation.model.data_structures.classification.Classification import Classification
from annotation.model.data_structures.document.Clause import ClauseSequence
from annotation.model.data_structures.document.Paragraph import Paragraph
from annotation.model.database.AnnotationDAO import AnnotationDAO


class AnnotationService:
    def __init__(self, paragraph_database_fn: str, clause_database_fn: str, sequence_db_path: str):
        self.annotation_dao: AnnotationDAO = AnnotationDAO(paragraph_database_fn, clause_database_fn, sequence_db_path)

    def get_paragraph_count(self) -> int:
        return self.annotation_dao.get_paragraph_count()

    def get_paragraph_text(self, paragraph_id: int) -> str:
        paragraph: Optional[Paragraph] = self.annotation_dao.get_paragraph_by_id(paragraph_id)
        if paragraph is None:
            return ""
        return paragraph.get_text()

    def get_paragraph_sequence_count(self, paragraph_id: int):
        return self.annotation_dao.get_paragraph_sequence_count(paragraph_id)

    def get_sequence_clause_ranges(self, paragraph_id: int, sequence_idx: int) -> tuple[tuple[int, int], tuple[int, int]]:
        sequence: ClauseSequence = self.annotation_dao.get_sequence_by_paragraph_idx(paragraph_id, sequence_idx)
        # TODO: Add check for None and handle at some point in the communication chain

        return sequence.get_clause_ranges()

    def get_all_sequence_classifications(self) -> list[str]:
        return [c.name for c in Classification]

    def get_sequence_predict_class(self, paragraph_id: int, sequence_idx: int) -> str:
        sequence: ClauseSequence = self.annotation_dao.get_sequence_by_paragraph_idx(paragraph_id, sequence_idx)
        classification: Optional[Classification] = sequence.get_predicted_class()
        if classification is None:
            return ""
        else:
            return classification.name

    def get_sequence_correct_class(self, paragraph_id: int, sequence_idx: int) -> str:
        sequence: ClauseSequence = self.annotation_dao.get_sequence_by_paragraph_idx(paragraph_id, sequence_idx)
        classification: Optional[Classification] = sequence.get_correct_class()
        if classification is None:
            return ""
        else:
            return classification.name

    def set_sequence_correct_class(self, paragraph_id: int, sequence_idx: int, classification: str):
        correct_class: int
        try:
            correct_class = Classification[classification].value
        except KeyError:
            correct_class = 0

        self.annotation_dao.update_sequence_classification_by_paragraph_idx(paragraph_id, sequence_idx, correct_class)
