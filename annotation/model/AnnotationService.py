class AnnotationService:
    def __init__(self):
        pass

    def get_paragraph_text(self, paragraph_id: int) -> str:
        return ""

    def get_clause_sequence(self, paragraph_id: int, sequence_id: int) -> tuple[tuple[int, int], tuple[int, int]]:
        return (0, 1), (2, 3)

    def get_sequence_classifications(self, paragraph_id: int, sequence_id: int) -> list[str]:
        pass
