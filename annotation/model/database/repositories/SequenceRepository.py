from abc import ABC, abstractmethod

from numpy import ndarray


class SequenceRepository(ABC):
    @abstractmethod
    def read_all(self) -> ndarray:
        """
        Reads all sequences from the database and returns an array of tuples.
        Each tuple contains:
         - integer id of the sequence
         - integer id of the first clause
         - integer id of the second clause
         - the predicted classes as a str structured as delimited digits, e.g. '1,2,3'
         - the corrected classes as a str structured as delimited digits, e.g. '1,2,3'
         - the LLM reasoning for the classification as a str
        Returns
        -------
        all_sequences: ndarray[tuple[int]] - all sequences found in the database
        """
        raise NotImplementedError()

    @abstractmethod
    def read_by_id(self, sequence_id: int) -> tuple:
        """
        Reads the sequence from the database corresponding to the given sequence_id and returns a tuple.
        The tuple contains:
         - integer id of the sequence
         - integer id of the first clause
         - integer id of the second clause
         - the predicted classes as a str structured as delimited digits, e.g. '1,2,3'
         - the corrected classes as a str structured as delimited digits, e.g. '1,2,3'
         - the LLM reasoning for the classification as a str
        Parameters
        ----------
        sequence_id: int - integer id of the sequence

        Returns
        -------
        sequence: tuple - the sequence to write as a tuple with the following values
        """
        raise NotImplementedError()

    @abstractmethod
    def read_by_clause_id(self, clause_id: int) -> ndarray:
        """
        Reads all sequences that contain the specified clause and returns an array of tuples.
        Each tuple contains:
         - integer id of the sequence
         - integer id of the first clause
         - integer id of the second clause
         - the predicted classes as a str structured as delimited digits, e.g. '1,2,3'
         - the corrected classes as a str structured as delimited digits, e.g. '1,2,3'
         - the LLM reasoning for the classification as a str
        Parameters
        ----------
        clause_id: int - the id of the specified clause

        Returns
        -------
        matches: ndarray[tuple[int]] - all sequences found in the database
        """
        raise NotImplementedError()

    @abstractmethod
    def create(self, clause_a_id: int, clause_b_id: int, linkage_words: str = "",
            predicted_classes: str = "0", correct_classes: str = "-1", reasoning: str = "") -> int:
        """
        Creates a new sequence in the database with the provided clause ids.
        Returns the integer id of the new sequence. IDs automatically increment by 1 from the max ID
        Parameters
        ----------
        clause_a_id: int - the id of the first specified clause
        clause_b_id: int - the id of the second specified clause
        linkage_words: str - the linkage words for the sequence, as a list of words separated by a delimiter
        predicted_classes: str - the predicted classes for the sequence, as a list of digits separated by a delimiter
        correct_classes: str - the corrected classes as a str structured as delimited digits, e.g. '1,2,3'
        reasoning: str - the LLM reasoning for the classification as a str

        Returns
        -------
        sequence_id: int - The integer id of the new sequence
        """
        raise NotImplementedError()

    @abstractmethod
    def update(self, sequence_id: int, correct_classes: str) -> bool:
        """
        Updates the corrected class for the sequence in the database with the given sequence id.
        Returns True if the operation succeeds, False if the operation fails or the sequence is not found.
        Parameters
        ----------
        sequence_id: int - integer id of the sequence
        correct_classes: str - the corrected classes as a str structured as delimited digits, e.g. '1,2,3'

        Returns
        -------
        success: bool - True if the operation succeeds, False if the operation fails or the sequence is not found.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete(self, sequence_id: int) -> bool:
        """
        Deletes the sequence entry corresponding to the given sequence id.
        Returns True if the operation succeeds, False if the operation fails or the sequence is not found.
        Parameters
        ----------
        sequence_id: int - integer id of the sequence

        Returns
        -------
        success: bool - True if the operation succeeds, False if the operation fails or the sequence is not found.
        """
        raise NotImplementedError()

    @abstractmethod
    def clear_database(self):
        """
        Deletes all contents from the database, except for column headers
        """
        raise NotImplementedError()
