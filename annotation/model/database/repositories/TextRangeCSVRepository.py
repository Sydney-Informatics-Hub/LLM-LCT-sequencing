import os
from csv import DictReader

from numpy import ndarray
from pandas import DataFrame, read_csv

from annotation.model.database.repositories import TextRangeRepository
from annotation.model.database.DatabaseExceptions import DatabaseFieldError, DatabaseEntryError


class TextRangeCSVRepository(TextRangeRepository):
    RANGE_ID_FIELD: str = "range_id"
    RANGE_START_FIELD: str = "start"
    RANGE_END_FIELD: str = "end"
    FIELD_DTYPES: dict = {RANGE_ID_FIELD: int, RANGE_START_FIELD: int, RANGE_END_FIELD: int}
    REQUIRED_FIELDS: list[str, ...] = [field for field in FIELD_DTYPES.keys()]

    def __init__(self, database_csv_filename: str):
        self._database_filename: str = database_csv_filename
        self._database_cache: DataFrame = DataFrame(columns=TextRangeCSVRepository.REQUIRED_FIELDS)
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
            for field in TextRangeCSVRepository.REQUIRED_FIELDS:
                if field not in reader.fieldnames:
                    raise DatabaseFieldError(f"Missing {field} column from text range database")

    def _read_database_into_cache(self):
        if self._cache_updated:
            return

        self._validate_database_fields()
        self._database_cache = read_csv(filepath_or_buffer=self._database_filename,
                                        header=0,
                                        names=TextRangeCSVRepository.REQUIRED_FIELDS,
                                        dtype=TextRangeCSVRepository.FIELD_DTYPES)
        self._cache_updated = True

    def _write_cache_to_database(self):
        self._database_cache.to_csv(path_or_buf=self._database_filename, index=False,
                                    columns=TextRangeCSVRepository.REQUIRED_FIELDS)
        self._cache_updated = True

    def read_all(self) -> ndarray:
        self._read_database_into_cache()

        return self._database_cache.values

    def read_by_id(self, range_id: int) -> tuple:
        id_field = TextRangeCSVRepository.RANGE_ID_FIELD

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[(self._database_cache[id_field] == range_id)].values

        if len(matches) == 0:
            return tuple()
        elif len(matches) == 1:
            return tuple(matches[0])
        else:
            raise DatabaseEntryError(f"More than one entry found for range_id: {range_id}")

    def create(self, start: int, end: int) -> int:
        id_field = TextRangeCSVRepository.RANGE_ID_FIELD
        start_field = TextRangeCSVRepository.RANGE_START_FIELD
        end_field = TextRangeCSVRepository.RANGE_END_FIELD

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[
            ((self._database_cache[start_field] == start) |
             (self._database_cache[end_field] == end)), [id_field]].values

        if len(matches) == 1:
            return int(matches.item(0))
        elif len(matches) > 1:
            raise DatabaseEntryError(f"More than one entry found for text range with start: {start} and end: {end}")

        existing_ids: ndarray = self._database_cache[id_field]
        new_id: int = 1
        if len(existing_ids) > 0:
            new_id = int(existing_ids.max()) + 1

        new_entry = [new_id, start, end]

        if len(self._database_cache.index) > 0:
            self._database_cache.loc[max(self._database_cache.index) + 1] = new_entry
        else:
            self._database_cache.loc[len(self._database_cache)] = new_entry

        self._write_cache_to_database()

        return new_id

    def update(self, range_id: int, start: int, end: int) -> bool:
        id_field = TextRangeCSVRepository.RANGE_ID_FIELD
        start_field = TextRangeCSVRepository.RANGE_START_FIELD
        end_field = TextRangeCSVRepository.RANGE_END_FIELD

        self._read_database_into_cache()

        matches = self._database_cache.loc[(self._database_cache[id_field] == range_id)].values

        if len(matches) == 0:
            return False
        elif len(matches) == 1:
            self._database_cache.loc[self._database_cache[id_field] == range_id, [start_field, end_field]] = [start, end]

            self._write_cache_to_database()
            return True
        else:
            raise DatabaseEntryError(f"More than one entry found for range_id: {range_id}")

    def delete(self) -> bool:
        raise NotImplementedError()

    def clear_database(self):
        self._database_cache = self._database_cache.iloc[0:0]
        self._write_cache_to_database()