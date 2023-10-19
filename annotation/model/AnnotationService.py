from typing import Optional

from annotation.model.data_structures.classification.Classification import Classification
from annotation.model.data_structures.document.Clause import ClauseSequence, Clause
from annotation.model.database.AnnotationDAO import AnnotationDAO

# Type alias for complex tuples
ClauseTuple = tuple[int, int]
ClauseSequenceTuple = tuple[ClauseTuple, ClauseTuple]


class AnnotationService:
    def __init__(self, text_database_fn: str, clause_database_fn: str, sequence_db_path: str):
        self.annotation_dao: AnnotationDAO = AnnotationDAO(text_database_fn, clause_database_fn, sequence_db_path)

    def get_text(self) -> str:
        return self.annotation_dao.get_text()

    def get_clauses(self) -> list[tuple[int, str]]:
        text: str = self.get_text()
        clauses: list[Clause] = self.annotation_dao.get_all_clauses()

        clause_str_ls: list[tuple[int, str]] = []
        for clause in clauses:
            clause_text = text[clause.start: clause.end+1]
            data = (clause.clause_id, clause_text)
            clause_str_ls.append(data)

        return clause_str_ls

    def get_sequence_count(self) -> int:
        return self.annotation_dao.get_sequence_count()

    def get_sequence_clause_ranges(self, sequence_id: int) -> Optional[ClauseSequenceTuple]:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_id(sequence_id)
        if sequence is None:
            return None

        return sequence.get_clause_ranges()

    def get_all_sequence_classifications(self) -> list[str]:
        return [c.name for c in Classification]

    def get_sequence_predict_class(self, sequence_id: int) -> str:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_id(sequence_id)
        if sequence is None:
            return ""

        classification: Optional[Classification] = sequence.get_predicted_class()
        if classification is None:
            return ""
        else:
            return classification.name

    def get_sequence_correct_class(self, sequence_id: int) -> str:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_id(sequence_id)
        if sequence is None:
            return ""

        classification: Optional[Classification] = sequence.get_correct_class()
        if classification is None:
            return ""
        else:
            return classification.name

    def set_sequence_correct_class(self, sequence_id: int, classification: str):
        correct_class: int
        try:
            correct_class = Classification[classification].value
        except KeyError:
            correct_class = 0

        self.annotation_dao.update_sequence_classification(sequence_id, correct_class)

    def create_sequence(self, clause_a_id: int, clause_b_id: int) -> int:
        return self.annotation_dao.create_sequence(clause_a_id, clause_b_id)

    def delete_sequence(self, sequence_id: int):
        self.annotation_dao.delete_sequence(sequence_id)
