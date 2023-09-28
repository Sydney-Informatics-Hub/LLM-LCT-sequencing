from annotation.model.data_structures.document.Clause import Clause, ClauseSequence


class Paragraph:
    def __init__(self, paragraph_id: int, text: str):
        self.paragraph_id: int = paragraph_id
        self.text: str = text

    def __eq__(self, other) -> bool:
        if type(other) is not Paragraph:
            return False
        return (self.paragraph_id == other.get_id()) and (self.text == other.get_text())

    def get_text(self) -> str:
        return self.text

    def get_id(self) -> int:
        return self.paragraph_id
