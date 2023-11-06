from typing import Optional

TextRangeTuple = tuple[int, int]


class TextRange:
    """
    Represents a sub-string of a text.
    This object contains a start index and end index of the substring relative to the start of the text
    """

    def __init__(self, start: int, end: int, range_id: Optional[int] = None):
        """
        Parameters
        ----------
        start: int - the start index of the text range relative to the text, beginning at 0
        end: int - the end index of the text range relative to the text
        range_id: int - The database integer id of the text range. Can be None
        """
        self.start: int = int(start)
        self.end: int = int(end)
        self.range_id: Optional[int] = range_id

    def __eq__(self, other) -> bool:
        if type(other) is not TextRange:
            return False
        return (self.start == other.start) and (self.end == other.end)

    def __hash__(self):
        return hash((self.start, self.end))

    def get_id(self) -> Optional[int]:
        return self.range_id

    def get_start(self) -> int:
        return self.start

    def get_end(self) -> int:
        return self.end

    def get_range(self) -> TextRangeTuple:
        return self.start, self.end
