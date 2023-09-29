import os
from csv import DictReader

from numpy import ndarray
from pandas import DataFrame, read_csv

from annotation.model.database.ClauseSequenceRepository import ClauseSequenceRepository
from annotation.model.database.DatabaseExceptions import DatabaseFieldError


class ClauseSequenceCSVRepository(ClauseSequenceRepository):
    PARAGRAPH_ID_FIELD: str = "paragraph_id"
    CLAUSE_A_START: str = "c1_start"
    CLAUSE_A_END: str = "c1_end"
    CLAUSE_B_START: str = "c2_start"
    CLAUSE_B_END: str = "c2_end"
    PREDICTED_CLASS: str = "class_predict"
    CORRECTED_CLASS: str = "class_correct"
    FIELD_DTYPES: dict = {PARAGRAPH_ID_FIELD: int, CLAUSE_A_START: int,
                          CLAUSE_A_END: int, CLAUSE_B_START: int,
                          CLAUSE_B_END: int, PREDICTED_CLASS: int,
                          CORRECTED_CLASS: int}
    REQUIRED_FIELDS: list[str, ...] = [field for field in FIELD_DTYPES.keys()]

    def __init__(self, database_csv_filename: str):
        self._database_filename: str = database_csv_filename
        self._database_cache: DataFrame = DataFrame(columns=ClauseSequenceCSVRepository.REQUIRED_FIELDS)
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
            for field in ClauseSequenceCSVRepository.REQUIRED_FIELDS:
                if field not in reader.fieldnames:
                    raise DatabaseFieldError(f"Missing {field} column from paragraph database")

    def _read_database_into_cache(self):
        if self._cache_updated:
            return

        self._validate_database_fields()
        self._database_cache = read_csv(filepath_or_buffer=self._database_filename,
                                        header=0,
                                        names=ClauseSequenceCSVRepository.REQUIRED_FIELDS,
                                        dtype=ClauseSequenceCSVRepository.FIELD_DTYPES)

        self._cache_updated = True

    def _write_cache_to_database(self):
        self._database_cache.to_csv(path_or_buf=self._database_filename, index=False,
                                    columns=ClauseSequenceCSVRepository.REQUIRED_FIELDS)

        self._cache_updated = True

    def read_all(self) -> ndarray:
        self._read_database_into_cache()

        return self._database_cache.values

    def read_all_by_paragraph(self, paragraph_id: int) -> ndarray:
        id_field = ClauseSequenceCSVRepository.PARAGRAPH_ID_FIELD
        fields_to_retrieve = [f for f in ClauseSequenceCSVRepository.REQUIRED_FIELDS if f is not id_field]

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[(self._database_cache[id_field] == paragraph_id), fields_to_retrieve].values

        return matches

    def create(self) -> bool:
        pass

    def update(self) -> bool:
        pass

    def delete(self) -> bool:
        pass
