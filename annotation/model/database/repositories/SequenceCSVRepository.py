import os
from csv import DictReader

from numpy import ndarray
from pandas import DataFrame, read_csv

from annotation.model.database.DatabaseExceptions import DatabaseFieldError, DatabaseEntryError
from annotation.model.database.repositories.SequenceRepository import SequenceRepository


class SequenceCSVRepository(SequenceRepository):
    SEQUENCE_ID_FIELD: str = "sequence_id"
    CLAUSE_A_ID_FIELD: str = "c1_id"
    CLAUSE_B_ID_FIELD: str = "c2_id"
    LINKAGE_FIELD: str = "linkage_words"
    PREDICTED_CLASSES: str = "classes_predict"
    CORRECTED_CLASSES: str = "classes_correct"
    FIELD_DTYPES: dict = {SEQUENCE_ID_FIELD: int, CLAUSE_A_ID_FIELD: int, CLAUSE_B_ID_FIELD: int,
                          LINKAGE_FIELD: str, PREDICTED_CLASSES: str, CORRECTED_CLASSES: str}
    REQUIRED_FIELDS: list[str, ...] = [field for field in FIELD_DTYPES.keys()]

    CLASS_LS_DELIMITER: str = ','
    LINKAGE_LS_DELIMITER: str = ','

    def __init__(self, database_csv_filename: str):
        self._database_filename: str = database_csv_filename
        self._database_cache: DataFrame = DataFrame(columns=SequenceCSVRepository.REQUIRED_FIELDS)
        self._cache_updated: bool = False

        # Validate the file can be opened with read and write permissions
        if not os.access(self._database_filename, os.R_OK):
            raise PermissionError(f"No permissions to read the file: {self._database_filename}")
        if not os.access(self._database_filename, os.W_OK):
            raise PermissionError(f"No permissions to write to the file: {self._database_filename}")

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
                                        dtype=SequenceCSVRepository.FIELD_DTYPES)

        self._cache_updated = True

    def _write_cache_to_database(self):
        self._database_cache.to_csv(path_or_buf=self._database_filename, index=False,
                                    columns=SequenceCSVRepository.REQUIRED_FIELDS)

        self._cache_updated = True

    def read_all(self) -> ndarray:
        self._read_database_into_cache()

        return self._database_cache.values

    def read_by_id(self, sequence_id: int) -> tuple:
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
        clause_a_id_field = SequenceCSVRepository.CLAUSE_A_ID_FIELD
        clause_b_id_field = SequenceCSVRepository.CLAUSE_B_ID_FIELD

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[
            ((self._database_cache[clause_a_id_field] == clause_id) |
             (self._database_cache[clause_b_id_field] == clause_id))].values

        return matches

    def create(self, clause_a_id: int, clause_b_id: int,
               linkage_words: str = "", predicted_classes: str = "0") -> int:
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

        new_entry = [new_id, clause_a_id, clause_b_id, linkage_words, predicted_classes, "0"]

        if len(self._database_cache.index) > 0:
            self._database_cache.loc[max(self._database_cache.index) + 1] = new_entry
        else:
            self._database_cache.loc[len(self._database_cache)] = new_entry

        self._write_cache_to_database()

        return new_id

    def update(self, sequence_id: int, correct_classes: str) -> bool:
        id_field = SequenceCSVRepository.SEQUENCE_ID_FIELD
        corrected_field = SequenceCSVRepository.CORRECTED_CLASSES

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[(self._database_cache[id_field] == sequence_id)].values

        if len(matches) == 0:
            return False
        elif len(matches) == 1:
            self._database_cache.loc[(self._database_cache[id_field] == sequence_id), [corrected_field]] = correct_classes

            self._write_cache_to_database()
            return True
        else:
            raise DatabaseEntryError(f"More than one entry found for sequence_id: {sequence_id}")

    def delete(self, sequence_id: int) -> bool:
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
        self._database_cache = self._database_cache.iloc[0:0]
        self._write_cache_to_database()
