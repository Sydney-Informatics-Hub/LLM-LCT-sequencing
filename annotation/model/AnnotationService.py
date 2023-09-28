from typing import Optional

from annotation.model.data_structures.document.Paragraph import Paragraph
from annotation.model.database.AnnotationDAO import AnnotationDAO


class AnnotationService:
    def __init__(self, paragraph_database_fn: str, clause_database_fn: str):
        self.annotation_dao: AnnotationDAO = AnnotationDAO(paragraph_database_fn, clause_database_fn)

    def get_paragraph_count(self) -> int:
        return self.annotation_dao.get_paragraph_count()

    def get_paragraph_text(self, paragraph_id: int) -> str:
        paragraph: Optional[Paragraph] = self.annotation_dao.get_paragraph_by_id(paragraph_id)
        if paragraph is None:
            return ""
        return paragraph.get_text()

    def get_clause_sequence(self, paragraph_id: int, sequence_id: int) -> tuple[tuple[int, int], tuple[int, int]]:
        return (0, 1), (2, 3)

    def get_sequence_classifications(self, paragraph_id: int, sequence_id: int) -> list[str]:
        pass
