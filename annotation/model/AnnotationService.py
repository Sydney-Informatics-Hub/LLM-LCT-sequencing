from typing import Optional

from pandas import DataFrame

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

    def get_clauses(self) -> dict[int, str]:
        text: str = self.get_text()
        clauses: list[Clause] = self.annotation_dao.get_all_clauses()

        clause_str_dict: dict[int, str] = {}
        for clause in clauses:
            clause_text = text[clause.start: clause.end+1]
            clause_str_dict[clause.clause_id] = clause_text

        return clause_str_dict

    def get_sequence_count(self) -> int:
        return self.annotation_dao.get_sequence_count()

    def get_sequence_clause_ranges(self, sequence_id: int) -> Optional[ClauseSequenceTuple]:
        sequence: Optional[ClauseSequence] = self.annotation_dao.get_sequence_by_id(sequence_id)
        if sequence is None:
            return None

        return sequence.get_clause_ranges()

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
        if len(correct_classes) == 0:
            correct_classes = [0]

        self.annotation_dao.update_sequence_classifications(sequence_id, correct_classes)

    def create_sequence(self, clause_a_id: int, clause_b_id: int) -> int:
        return self.annotation_dao.create_sequence(clause_a_id, clause_b_id)

    def delete_sequence(self, sequence_id: int):
        self.annotation_dao.delete_sequence(sequence_id)

    def get_dataframe_for_export(self) -> DataFrame:
        export_columns = ["Clause A", "Clause B", "Predicted Classes", "Corrected Classes"]
        export_data: list[dict[str, str]] = []

        clause_texts: dict[int, str] = self.get_clauses()
        sequences: list[ClauseSequence] = self.annotation_dao.get_all_sequences()
        for sequence in sequences:
            clause_a_text: Optional[str] = clause_texts.get(sequence.get_first_clause().get_id())
            clause_a_text = "" if clause_a_text is None else clause_a_text
            clause_b_text: Optional[str] = clause_texts.get(sequence.get_second_clause().get_id())
            clause_b_text = "" if clause_b_text is None else clause_b_text

            predicted_classes: Optional[list[Classification]] = sequence.get_predicted_classes()
            predicted_classes_str: str = ""
            if predicted_classes is not None:
                predicted_classes_str = ','.join([c.name for c in predicted_classes])
            correct_classes: Optional[list[Classification]] = sequence.get_correct_classes()
            corrected_classes_str: str = ""
            if correct_classes is not None:
                corrected_classes_str = ','.join([c.name for c in correct_classes])

            sequence_dict: dict[str, str] = {export_columns[0]: clause_a_text,
                                             export_columns[1]: clause_b_text,
                                             export_columns[2]: predicted_classes_str,
                                             export_columns[3]: corrected_classes_str}
            export_data.append(sequence_dict)

        return DataFrame(export_data, columns=export_columns)
