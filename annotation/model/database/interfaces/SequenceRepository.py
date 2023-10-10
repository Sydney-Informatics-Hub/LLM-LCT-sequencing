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
         - the predicted class as an integer
         - the corrected class as an integer
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
         - the predicted class as an integer
         - the corrected class as an integer
        Parameters
        ----------
        sequence_id: int - integer id of the sequence

        Returns
        -------
        sequence: tuple[int, int, int, int] - the sequence to write as a tuple with the following values:
         - integer id of the sequence
         - integer id of the first clause
         - integer id of the second clause
         - the predicted class as an integer
         - the corrected class as an integer
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
         - the predicted class as an integer
         - the corrected class as an integer
        Parameters
        ----------
        clause_id: int - the id of the specified clause

        Returns
        -------
        matches: ndarray[tuple[int]] - all sequences found in the database
        """
        raise NotImplementedError()

    @abstractmethod
    def create(self, clause_a_id: int, clause_b_id: int) -> int:
        """
        Creates a new sequence in the database with the provided clause ids.
        Returns the integer id of the new sequence. IDs automatically increment by 1 from the max ID
        Parameters
        ----------
        clause_a_id: int - the id of the first specified clause
        clause_b_id: int - the id of the second specified clause

        Returns
        -------
        sequence_id: int - The integer id of the new sequence
        """
        raise NotImplementedError()

    @abstractmethod
    def update(self, sequence_id: int, class_correct: int) -> bool:
        """
        Updates the corrected class for the sequence in the database with the given sequence id.
        Returns True if the operation succeeds, False if the operation fails or the sequence is not found.
        Parameters
        ----------
        sequence_id: int - integer id of the sequence
        class_correct: int - the corrected class as an integer

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
