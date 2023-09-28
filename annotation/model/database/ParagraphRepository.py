from abc import ABC, abstractmethod
from typing import Optional

from numpy import ndarray


class ParagraphRepository(ABC):
    @abstractmethod
    def read_all(self) -> ndarray:
        """
        Reads all paragraphs from the database into a list tuples.
        Each tuple contains the integer id of the paragraph and the text as a string.
        Returns
        -------
        all_paragraphs: list[tuple[int, str], ...] - all paragraphs found in the database
        """
        raise NotImplementedError()

    @abstractmethod
    def read_by_id(self, paragraph_id: int) -> Optional[str]:
        """
        Reads the paragraph text in the database with the given id
        Parameters
        ----------
        paragraph_id: int - the unique id of the paragraph to be read

        Returns
        -------
        paragraph_text: str - returns the text as a str if the paragraph with the given id is found, None otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def create(self, new_paragraph: str) -> int:
        """
        Creates a new paragraph in the database, according to the provided argument.
        If the operation succeeds, the id of the newly created paragraph is returned.
        If the operation fails for any reason, the method will return -1.
        Parameters
        ----------
        new_paragraph: str - the paragraph text to write to the database

        Returns
        -------
        paragraph_id: int - the id of the newly created paragraph. Returns -1 if the operation fails
        """
        raise NotImplementedError()

    @abstractmethod
    def update(self, paragraph_id: int, updated_text: str) -> bool:
        """
        Overwrites the text in the existing paragraph (the method is idempotent).
        If the operation is successful the method returns True, otherwise False. The method returns False and will not
        write to the database if the paragraph_id cannot be found in the database
        Parameters
        ----------
        paragraph_id: int - the unique id of the paragraph to be updated
        updated_text: str - the text that will overwrite the existing values

        Returns
        -------
        success: bool - True if the operation is successful, False otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete(self, paragraph_id: int) -> bool:
        """
        Deletes the paragraph entry corresponding to the given paragraph_id.
        If the operation is successful the method returns True, otherwise False. The method returns False and will not
        write to the database if the paragraph_id cannot be found in the database
        Parameters
        ----------
        paragraph_id: int - the unique id of the paragraph to be updated

        Returns
        -------
        success: bool - True if the operation is successful, False otherwise.
        """
        raise NotImplementedError()
