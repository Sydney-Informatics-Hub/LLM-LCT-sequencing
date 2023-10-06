from typing import Optional

from numpy import ndarray

from annotation.model.data_structures.classification.Classification import Classification
from annotation.model.data_structures.document.Clause import ClauseSequence, Clause
from annotation.model.data_structures.document.Paragraph import Paragraph
from annotation.model.database.CSV.ClauseCSVRepository import ClauseCSVRepository
from annotation.model.database.CSV.SequenceCSVRepository import SequenceCSVRepository
from annotation.model.database.interfaces.ClauseRepository import ClauseRepository
from annotation.model.database.CSV.ParagraphCSVRepository import ParagraphCSVRepository
from annotation.model.database.interfaces.ParagraphRepository import ParagraphRepository
from annotation.model.database.interfaces.SequenceRepository import SequenceRepository


class AnnotationDAO:
    def __init__(self, paragraph_database_fn: str, clause_database_fn: str, sequence_db_path: str):
        self.paragraph_repository: ParagraphRepository = ParagraphCSVRepository(paragraph_database_fn)
        self.clause_repository: ClauseRepository = ClauseCSVRepository(clause_database_fn)
        self.sequence_repository: SequenceRepository = SequenceCSVRepository(sequence_db_path)

    def get_paragraph_count(self) -> int:
        paragraph_data: ndarray = self.paragraph_repository.read_all()
        nrows: int = paragraph_data.shape[0]
        return nrows

    def get_all_paragraphs(self) -> list[Paragraph]:
        paragraph_data: ndarray = self.paragraph_repository.read_all()
        paragraph_ls: list[Paragraph] = [Paragraph(p_id, p_text) for (p_id, p_text) in paragraph_data]

        return paragraph_ls

    def get_paragraph_by_id(self, paragraph_id: int) -> Optional[Paragraph]:
        paragraph_text: Optional[str] = self.paragraph_repository.read_by_id(paragraph_id)
        if paragraph_text is None:
            return None
        return Paragraph(paragraph_id, paragraph_text)

    def get_paragraph_sequence_count(self, paragraph_id: int) -> int:
        return len(self.get_all_sequences_by_paragraph(paragraph_id))

    def get_all_sequences_by_paragraph(self, paragraph_id: int) -> list[ClauseSequence]:
        all_paragraph_clauses: ndarray = self.clause_repository.read_all_by_paragraph(paragraph_id)
        clause_map: dict[int, Clause] = {}
        for clause_data in all_paragraph_clauses:
            clause_id = clause_data[0]
            clause = Clause(clause_data[2], clause_data[3])
            clause_map[clause_id] = clause

        sequence_map: dict[int, ClauseSequence] = {}
        for clause_id in clause_map:
            sequence_data_ls = self.sequence_repository.read_by_clause_id(clause_id)
            for sequence_data in sequence_data_ls:
                sequence_id = sequence_data[0]
                if sequence_map.get(sequence_id) is not None:
                    continue

                clause_a_id = sequence_data[1]
                clause_a = clause_map.get(clause_a_id)
                if clause_a is None:
                    clause_data = self.clause_repository.read_by_id(clause_a_id)
                    clause = Clause(clause_data[2], clause_data[3])
                    clause_map[clause_a_id] = clause
                    clause_a = clause

                clause_b_id = sequence_data[2]
                clause_b = clause_map.get(clause_b_id)
                if clause_b is None:
                    clause_data = self.clause_repository.read_by_id(clause_b_id)
                    clause = Clause(clause_data[2], clause_data[3])
                    clause_map[clause_b_id] = clause
                    clause_b = clause

                try:
                    predicted_class = Classification(sequence_data[3])
                except ValueError:
                    predicted_class = None
                try:
                    correct_class = Classification(sequence_data[4])
                except ValueError:
                    correct_class = None

                sequence = ClauseSequence(sequence_id, clause_a, clause_b, predicted_class, correct_class)

                sequence_map[sequence_id] = sequence

        return list(sequence_map.values())

    def get_sequence_by_paragraph_idx(self, paragraph_id: int, sequence_idx: int) -> Optional[ClauseSequence]:
        paragraph_sequences = self.get_all_sequences_by_paragraph(paragraph_id)
        if len(paragraph_sequences) == 0:
            return None
        return paragraph_sequences[sequence_idx]

    def update_sequence_classification_by_paragraph_idx(self, paragraph_id: int, sequence_idx: int, correct_class: int):
        sequence = self.get_sequence_by_paragraph_idx(paragraph_id, sequence_idx)
        if sequence is None:
            return
        self.sequence_repository.update(sequence.get_id(), correct_class)
