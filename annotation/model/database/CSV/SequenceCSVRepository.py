import os
from csv import DictReader

from numpy import ndarray
from pandas import DataFrame, read_csv

from annotation.model.database.DatabaseExceptions import DatabaseFieldError, DatabaseEntryError
from annotation.model.database.interfaces.SequenceRepository import SequenceRepository


class SequenceCSVRepository(SequenceRepository):
    SEQUENCE_ID_FIELD: str = "sequence_id"
    CLAUSE_A_ID_FIELD: str = "c1_id"
    CLAUSE_B_ID_FIELD: str = "c2_id"
    PREDICTED_CLASS: str = "class_predict"
    CORRECTED_CLASS: str = "class_correct"
    FIELD_DTYPES: dict = {SEQUENCE_ID_FIELD: int, CLAUSE_A_ID_FIELD: int, CLAUSE_B_ID_FIELD: int,
                          PREDICTED_CLASS: int, CORRECTED_CLASS: int}
    REQUIRED_FIELDS: list[str, ...] = [field for field in FIELD_DTYPES.keys()]

    def __init__(self, database_csv_filename: str):
        self._database_filename: str = database_csv_filename
        self._database_cache: DataFrame = DataFrame(columns=SequenceCSVRepository.REQUIRED_FIELDS)
        self._cache_updated: bool = False

        # Validate the file can be opened with read and write permissions
        if not (os.access(self._database_filename, os.R_OK)):
            raise PermissionError(f"No permissions to read the file: {self._database_filename}")
        if not (os.access(self._database_filename, os.W_OK)):
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
                    raise DatabaseFieldError(f"Missing {field} column from paragraph database")

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

    def create(self, new_sequence: tuple[int, int, int, int]) -> bool:
        raise NotImplementedError()

    def update(self, sequence_id: int, class_correct: int) -> bool:
        id_field = SequenceCSVRepository.SEQUENCE_ID_FIELD
        corrected_field = SequenceCSVRepository.CORRECTED_CLASS

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[(self._database_cache[id_field] == sequence_id)].values

        if len(matches) == 0:
            return False
        elif len(matches) == 1:
            self._database_cache.loc[(self._database_cache[id_field] == sequence_id), [corrected_field]] = class_correct

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

            self._write_cache_to_database()
            return True
        else:
            raise DatabaseEntryError(f"More than one entry found for sequence_id: {sequence_id}")
