from typing import Optional

from numpy import ndarray

from annotation.model.data_structures.classification.Classification import Classification
from annotation.model.data_structures.document.Clause import ClauseSequence, Clause
from annotation.model.database.interfaces import ClauseRepository, SequenceRepository, TextRepository
from annotation.model.database.CSV import ClauseCSVRepository, SequenceCSVRepository
from annotation.model.database.TXT import TextTXTRepository


class AnnotationDAO:
    def __init__(self, text_database_fn: str, clause_database_fn: str, sequence_db_path: str):
        self.text_repository: TextRepository = TextTXTRepository(text_database_fn)
        self.clause_repository: ClauseRepository = ClauseCSVRepository(clause_database_fn)
        self.sequence_repository: SequenceRepository = SequenceCSVRepository(sequence_db_path)

    def get_text(self) -> str:
        return self.text_repository.read_all()

    def get_all_clauses(self) -> list[Clause]:
        clause_data: ndarray = self.clause_repository.read_all()
        clauses: list[Clause] = [Clause(data[1], data[2], clause_id=data[0]) for data in clause_data]

        return clauses

    def get_sequence_count(self) -> int:
        sequence_data: ndarray = self.sequence_repository.read_all()
        return sequence_data.shape[0]

    def get_sequence_by_id(self, sequence_id: int) -> ClauseSequence:
        sequence_data: tuple = self.sequence_repository.read_by_id(sequence_id)
        if len(sequence_data) == 0:
            raise ValueError(f"Sequence database does not contain a sequence with id {sequence_id}")
        clause_a_id: int = sequence_data[1]
        clause_b_id: int = sequence_data[2]
        class_predict_id: int = sequence_data[3]
        class_correct_id: int = sequence_data[4]

        clause_a_data: tuple = self.clause_repository.read_by_id(clause_a_id)
        if len(clause_a_data) == 0:
            raise ValueError(f"Clause database does not contain a clause with id {clause_a_id}")
        clause_b_data: tuple = self.clause_repository.read_by_id(clause_b_id)
        if len(clause_b_data) == 0:
            raise ValueError(f"Clause database does not contain a clause with id {clause_b_id}")

        clause_a: Clause = Clause(clause_a_data[1], clause_a_data[2], clause_id=clause_a_id)
        clause_b: Clause = Clause(clause_b_data[1], clause_b_data[2], clause_id=clause_b_id)

        try:
            predicted_class = Classification(class_predict_id)
        except ValueError:
            predicted_class = None
        try:
            correct_class = Classification(class_correct_id)
        except ValueError:
            correct_class = None

        return ClauseSequence(sequence_id, clause_a, clause_b, predicted_class, correct_class)

    def get_all_sequences(self) -> list[ClauseSequence]:
        all_clauses: ndarray = self.clause_repository.read_all()
        clause_map: dict[int, Clause] = {}
        for clause_data in all_clauses:
            clause_id = clause_data[0]
            clause = Clause(clause_data[1], clause_data[2])
            clause_map[clause_id] = clause

        sequence_data: ndarray = self.sequence_repository.read_all()
        sequence_map: dict[int, ClauseSequence] = {}

        for data in sequence_data:
            sequence_id: int = data[0]
            clause_a_id: int = data[1]
            clause_b_id: int = data[2]
            class_predict_id: int = data[3]
            class_correct_id: int = data[4]

            clause_a: Optional[Clause] = clause_map.get(clause_a_id)
            clause_b: Optional[Clause] = clause_map.get(clause_b_id)
            if clause_a is None:
                raise ValueError(f"Clause ID {clause_a_id} is found in sequence database but is not present in clause database")
            if clause_b is None:
                raise ValueError(f"Clause ID {clause_b_id} is found in sequence database but is not present in clause database")

            try:
                predicted_class = Classification(class_predict_id)
            except ValueError:
                predicted_class = None
            try:
                correct_class = Classification(class_correct_id)
            except ValueError:
                correct_class = None

            sequence = ClauseSequence(sequence_id, clause_a, clause_b, predicted_class, correct_class)
            sequence_map[sequence_id] = sequence

        return list(sequence_map.values())

    def update_sequence_classification(self, sequence_id: int, correct_class: int):
        self.sequence_repository.update(sequence_id, correct_class)

    def create_sequence(self, clause_a_id: int, clause_b_id: int) -> int:
        return self.sequence_repository.create(clause_a_id, clause_b_id)

    def delete_sequence(self, sequence_id: int):
        self.sequence_repository.delete(sequence_id)
