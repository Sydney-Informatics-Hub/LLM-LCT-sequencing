from typing import Optional

from annotation.model.data_structures.classification.Classification import Classification
from annotation.model.data_structures.document.Clause import ClauseSequence
from annotation.model.data_structures.document.Paragraph import Paragraph
from annotation.model.database.AnnotationDAO import AnnotationDAO

# Type alias for complex tuples
ClauseTuple = tuple[int, int]
ClauseSequenceTuple = tuple[ClauseTuple, ClauseTuple]


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

    def get_all_paragraph_clauses(self, paragraph_id: int) -> list[tuple[int, str]]:
        paragraph: Paragraph = self.annotation_dao.get_paragraph_by_id(paragraph_id)
        if paragraph is None:
            return []
        paragraph_text = paragraph.get_text()

        clauses: list[tuple[int, str]] = []
        for clause in self.annotation_dao.get_all_clauses_by_paragraph(paragraph_id):
            clause_text = paragraph_text[clause.start: clause.end+1]
            data = (clause.clause_id, clause_text)
            clauses.append(data)
        return clauses

    def get_paragraph_sequence_count(self, paragraph_id: int):
        return self.annotation_dao.get_paragraph_sequence_count(paragraph_id)

    def get_sequence_clause_ranges(self, paragraph_id: int, sequence_idx: int) -> Optional[ClauseSequenceTuple]:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_paragraph_idx(paragraph_id, sequence_idx)
        if sequence is None:
            return None

        return sequence.get_clause_ranges()

    def get_all_sequence_classifications(self) -> list[str]:
        return [c.name for c in Classification]

    def get_sequence_predict_class(self, paragraph_id: int, sequence_idx: int) -> str:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_paragraph_idx(paragraph_id, sequence_idx)
        if sequence is None:
            return ""

        classification: Optional[Classification] = sequence.get_predicted_class()
        if classification is None:
            return ""
        else:
            return classification.name

    def get_sequence_correct_class(self, paragraph_id: int, sequence_idx: int) -> str:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_paragraph_idx(paragraph_id, sequence_idx)
        if sequence is None:
            return ""

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

    def create_sequence(self, clause_a_id: int, clause_b_id: int) -> int:
        return self.annotation_dao.create_sequence(clause_a_id, clause_b_id)

    def delete_sequence(self, paragraph_id: int, sequence_idx: int):
        self.annotation_dao.delete_sequence(paragraph_id, sequence_idx)
