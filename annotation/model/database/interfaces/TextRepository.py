from abc import ABC, abstractmethod


class TextRepository(ABC):
    @abstractmethod
    def read_all(self) -> str:
        """
        Reads all text in from the database file as a str

        text: str - A string of all text in the text database
        """
        raise NotImplementedError()

    @abstractmethod
    def read_by_range(self, start: int, end: int) -> str:
        """
        Reads text in from the database file as a str between the specified range.
        The range is inclusive of start and exclusive of end.

        Parameters
        ----------
        start: int - The start index to read from. Cannot be negative. The first character has index of 0.
        end: int - The end index to read to. Range is exclusive of end index.
        Cannot be lower than start and cannot be greater than the maximum range of the text

        Returns
        -------
        text_range: str - A string of the text between the specified range, inclusive of start and exclusive of end.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_end_index(self) -> int:
        """
        Returns the end range of the text. The text contains characters with indexes 0 to (end - 1).
        If the text is empty, will return 0.
        Returns
        -------
        end_index: int - The range end index.
        """
