from typing import Optional

from numpy import ndarray

from annotation.model.data_structures.classification.Classification import Classification
from annotation.model.data_structures.document.Clause import ClauseSequence, Clause
from annotation.model.data_structures.document.Paragraph import Paragraph
from annotation.model.database.ClauseSequenceCSVRepository import ClauseSequenceCSVRepository
from annotation.model.database.ClauseSequenceRepository import ClauseSequenceRepository
from annotation.model.database.ParagraphCSVRepository import ParagraphCSVRepository
from annotation.model.database.ParagraphRepository import ParagraphRepository


class AnnotationDAO:
    def __init__(self, paragraph_database_fn: str, clause_database_fn: str):
        self.paragraph_repository: ParagraphRepository = ParagraphCSVRepository(paragraph_database_fn)
        self.clause_sequence_repository: ClauseSequenceRepository = ClauseSequenceCSVRepository(clause_database_fn)

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

    def get_paragraph_sequence_count(self, paragraph_id: int):
        paragraph_sequences = self.clause_sequence_repository.read_all_by_paragraph(paragraph_id)
        return paragraph_sequences.shape[0]

    def get_sequences_all_paragraph(self, paragraph_id: int) -> list[ClauseSequence]:
        paragraph_sequences = self.clause_sequence_repository.read_all_by_paragraph(paragraph_id)
        sequence_ls: list[ClauseSequence] = []
        sequence: ClauseSequence
        for sequence_data in paragraph_sequences:
            try:
                classification = Classification(sequence_data[4])
            except ValueError:
                classification = None
            sequence = ClauseSequence(Clause(sequence_data[0], sequence_data[1]),
                                      Clause(sequence_data[2], sequence_data[3]),
                                      classification)
            sequence_ls.append(sequence)

        return sequence_ls

    def get_sequence_by_paragraph_idx(self, paragraph_id: int, sequence_idx: int) -> Optional[ClauseSequence]:
        paragraph_sequences = self.get_sequences_all_paragraph(paragraph_id)
        if len(paragraph_sequences) == 0:
            return None
        return paragraph_sequences[sequence_idx]

    def update_sequence_classification_by_paragraph_idx(self, paragraph_id: int, sequence_idx: int, sequence: ClauseSequence):
        self.clause_sequence_repository.update(
            paragraph_id, sequence_idx, sequence.get_clause_ranges(), sequence.get_classification().value)
