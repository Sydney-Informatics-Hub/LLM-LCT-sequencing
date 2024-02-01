import os
from csv import DictReader
from pathlib import Path
from typing import Optional

from numpy import ndarray
from pandas import DataFrame, read_csv

from annotation.model.database.DatabaseExceptions import DatabaseFieldError, DatabaseEntryError


class SequenceCSVRepository:
    SEQUENCE_ID_FIELD: str = "sequence_id"
    CLAUSE_A_ID_FIELD: str = "c1_id"
    CLAUSE_B_ID_FIELD: str = "c2_id"
    LINKAGE_FIELD: str = "linkage_words"
    PREDICTED_CLASSES: str = "predicted_classes"
    CORRECTED_CLASSES: str = "corrected_classes"
    REASONING_FIELD: str = "reasoning"
    FIELD_DTYPES: dict = {SEQUENCE_ID_FIELD: int, CLAUSE_A_ID_FIELD: int, CLAUSE_B_ID_FIELD: int,
                          LINKAGE_FIELD: str, PREDICTED_CLASSES: str, CORRECTED_CLASSES: str, REASONING_FIELD: str}
    REQUIRED_FIELDS: list[str, ...] = [field for field in FIELD_DTYPES.keys()]

    CLASS_LS_DELIMITER: str = ','
    LINKAGE_LS_DELIMITER: str = ','

    def __init__(self, database_csv_path: Path):
        self._database_filename: Path = database_csv_path
        self._database_cache: DataFrame = DataFrame(columns=SequenceCSVRepository.REQUIRED_FIELDS)
        self._cache_updated: bool = False

        # If file does not exist, create parent directories and file with only headers
        if not os.path.exists(database_csv_path):
            database_csv_path.parent.mkdir(parents=True, exist_ok=True)
            database_csv_path.write_text(",".join(SequenceCSVRepository.REQUIRED_FIELDS))

        # Validate the file can be opened with read and write permissions
        if not os.access(database_csv_path, os.R_OK):
            raise PermissionError(f"No permissions to read the file: {database_csv_path}")
        if not os.access(database_csv_path, os.W_OK):
            raise PermissionError(f"No permissions to write to the file: {database_csv_path}")

        self._read_database_into_cache()

    def _validate_database_fields(self):
        """
        Checks the database contains all the required fields.
        Additional unnecessary fields are ignored. Does not validate the data itself.
        If all fields are present, returns None. If a field is missing, the method raises a DatabaseFieldError
        """
        with open(self._database_filename, 'r') as csv_f:
            reader = DictReader(csv_f)
            for field in SequenceCSVRepository.REQUIRED_FIELDS:
                if field not in reader.fieldnames:
                    raise DatabaseFieldError(f"Missing {field} column from sequence database")

    def _read_database_into_cache(self):
        if self._cache_updated:
            return

        self._validate_database_fields()
        self._database_cache = read_csv(filepath_or_buffer=self._database_filename,
                                        header=0,
                                        names=SequenceCSVRepository.REQUIRED_FIELDS,
                                        dtype=SequenceCSVRepository.FIELD_DTYPES,
                                        keep_default_na=False,
                                        na_filter=False)
        self._database_cache.fillna('')

        self._cache_updated = True

    def _write_cache_to_database(self):
        self._database_cache.to_csv(path_or_buf=self._database_filename, index=False, na_rep='',
                                    columns=SequenceCSVRepository.REQUIRED_FIELDS)

        self._cache_updated = True

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
        ndarray[tuple[int]] - all sequences found in the database
        """
        self._read_database_into_cache()

        return self._database_cache.values

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
        tuple - the corresponding sequence as a tuple
        """
        id_field = SequenceCSVRepository.SEQUENCE_ID_FIELD

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[(self._database_cache[id_field] == sequence_id)].values

        if len(matches) == 0:
            return tuple()
        elif len(matches) == 1:
            return tuple(matches[0])
        else:
            raise DatabaseEntryError(f"More than one entry found for sequence_id: {sequence_id}")

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
        clause_a_id_field = SequenceCSVRepository.CLAUSE_A_ID_FIELD
        clause_b_id_field = SequenceCSVRepository.CLAUSE_B_ID_FIELD

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[
            ((self._database_cache[clause_a_id_field] == clause_id) |
             (self._database_cache[clause_b_id_field] == clause_id))].values

        return matches

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
        int - The integer id of the new sequence
        """
        if ((type(clause_a_id) is not int) or (type(clause_b_id) is not int) or
                (type(linkage_words) is not str) or (type(predicted_classes) is not str)):
            return -1

        self._read_database_into_cache()

        sequence_id_field = SequenceCSVRepository.SEQUENCE_ID_FIELD
        clause_a_id_field = SequenceCSVRepository.CLAUSE_A_ID_FIELD
        clause_b_id_field = SequenceCSVRepository.CLAUSE_B_ID_FIELD
        matches: ndarray = self._database_cache.loc[
            ((self._database_cache[clause_a_id_field] == clause_a_id) &
             (self._database_cache[clause_b_id_field] == clause_b_id))].values

        if len(matches) > 0:
            return -1

        existing_ids: ndarray = self._database_cache[sequence_id_field]
        new_id: int = 1
        if len(existing_ids) > 0:
            new_id = existing_ids.max() + 1

        new_entry = [new_id, clause_a_id, clause_b_id, linkage_words, predicted_classes, correct_classes, reasoning]

        if len(self._database_cache.index) > 0:
            self._database_cache.loc[max(self._database_cache.index) + 1] = new_entry
        else:
            self._database_cache.loc[len(self._database_cache)] = new_entry

        self._write_cache_to_database()

        return new_id

    def update(self, sequence_id: int, linkage_words: Optional[str] = None, predicted_classes: Optional[str] = None,
               corrected_classes: Optional[str] = None, reasoning: Optional[str] = None) -> bool:
        """
        Updates the attributes for the sequence in the database with the given sequence_id.
        Returns True if the operation succeeds, False if the operation fails or the sequence is not found.
        Parameters
        ----------
        sequence_id: int - integer id of the sequence
        linkage_words: str - the linkage words for the sequence, as a list of words separated by a delimiter
        predicted_classes: str - the predicted classes for the sequence, as a list of digits separated by a delimiter
        corrected_classes: str - the corrected classes as a str structured as delimited digits, e.g. '1,2,3'
        reasoning: str - the LLM reasoning for the classification as a str

        Returns
        -------
        bool - True if the operation succeeds, False if the operation fails or the sequence is not found.
        """
        id_field = SequenceCSVRepository.SEQUENCE_ID_FIELD
        linkage_field = SequenceCSVRepository.LINKAGE_FIELD
        predicted_field = SequenceCSVRepository.PREDICTED_CLASSES
        corrected_field = SequenceCSVRepository.CORRECTED_CLASSES
        reasoning_field = SequenceCSVRepository.REASONING_FIELD

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[(self._database_cache[id_field] == sequence_id)].values

        if len(matches) == 0:
            return False
        elif len(matches) == 1:
            if linkage_words is not None:
                self._database_cache.loc[(self._database_cache[id_field] == sequence_id), [linkage_field]] = linkage_words
            if predicted_classes is not None:
                self._database_cache.loc[(self._database_cache[id_field] == sequence_id), [predicted_field]] = predicted_classes
            if corrected_classes is not None:
                self._database_cache.loc[(self._database_cache[id_field] == sequence_id), [corrected_field]] = corrected_classes
            if reasoning is not None:
                self._database_cache.loc[(self._database_cache[id_field] == sequence_id), [reasoning_field]] = reasoning

            self._write_cache_to_database()
            return True
        else:
            raise DatabaseEntryError(f"More than one entry found for sequence_id: {sequence_id}")

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
        id_field = SequenceCSVRepository.SEQUENCE_ID_FIELD

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[(self._database_cache[id_field] == sequence_id)].values

        if len(matches) == 0:
            return False
        elif len(matches) == 1:
            self._database_cache = self._database_cache.loc[~(self._database_cache[id_field] == sequence_id)]
            self._database_cache[id_field] = self._database_cache[id_field].apply(
                lambda x: x - 1 if x > sequence_id else x)

            self._write_cache_to_database()
            return True
        else:
            raise DatabaseEntryError(f"More than one entry found for sequence_id: {sequence_id}")

    def clear_database(self):
        """
        Deletes all contents from the database, except for column headers
        """
        self._database_cache = self._database_cache.iloc[0:0]
        self._write_cache_to_database()
