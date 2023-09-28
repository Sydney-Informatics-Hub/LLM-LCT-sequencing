from typing import Optional

from numpy import ndarray

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
