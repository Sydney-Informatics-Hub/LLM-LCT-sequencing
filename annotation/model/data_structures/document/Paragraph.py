from annotation.model.data_structures.document.Clause import Clause


class Paragraph:
    def __init__(self, text: str):
        self.text: str = text
        self.clauses: list[Clause] = []

    def get_text(self) -> str:
        return self.text

    def get_all_clauses(self) -> list[Clause]:
        return self.clauses.copy()

    def add_clause(self, start_idx: int, end_idx: int):
        new_clause: Clause = Clause(start_idx, end_idx)
        self.clauses.append(new_clause)
