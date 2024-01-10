import os
from csv import DictReader
from pathlib import Path

from numpy import ndarray
from pandas import DataFrame, read_csv

from annotation.model.database.DatabaseExceptions import DatabaseFieldError, DatabaseEntryError


class TextRangeCSVRepository:
    RANGE_ID_FIELD: str = "range_id"
    RANGE_START_FIELD: str = "start"
    RANGE_END_FIELD: str = "end"
    FIELD_DTYPES: dict = {RANGE_ID_FIELD: int, RANGE_START_FIELD: int, RANGE_END_FIELD: int}
    REQUIRED_FIELDS: list[str, ...] = [field for field in FIELD_DTYPES.keys()]

    def __init__(self, database_csv_path: Path):
        self._database_path: Path = database_csv_path
        self._database_cache: DataFrame = DataFrame(columns=TextRangeCSVRepository.REQUIRED_FIELDS)
        self._cache_updated: bool = False

        # If file does not exist, create parent directories and file with only headers
        if not os.path.exists(database_csv_path):
            database_csv_path.parent.mkdir(parents=True, exist_ok=True)
            database_csv_path.write_text(",".join(TextRangeCSVRepository.REQUIRED_FIELDS))

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
        with open(self._database_path, 'r') as csv_f:
            reader = DictReader(csv_f)
            for field in TextRangeCSVRepository.REQUIRED_FIELDS:
                if field not in reader.fieldnames:
                    raise DatabaseFieldError(f"Missing {field} column from text range database")

    def _read_database_into_cache(self):
        if self._cache_updated:
            return

        self._validate_database_fields()
        self._database_cache = read_csv(filepath_or_buffer=self._database_path,
                                        header=0,
                                        names=TextRangeCSVRepository.REQUIRED_FIELDS,
                                        dtype=TextRangeCSVRepository.FIELD_DTYPES)
        self._cache_updated = True

    def _write_cache_to_database(self):
        self._database_cache.to_csv(path_or_buf=self._database_path, index=False,
                                    columns=TextRangeCSVRepository.REQUIRED_FIELDS)
        self._cache_updated = True

    def read_all(self) -> ndarray:
        """
        Reads all text ranges from the database and returns an array of tuples.
        Each tuple contains:
         - integer id of the range
         - integer index of the start of the text range (inclusive)
         - integer index of the end of the text range (inclusive)
        Returns
        -------
        ndarray[tuple[int]] - all text ranges found in the database
        """
        self._read_database_into_cache()

        return self._database_cache.values

    def read_by_id(self, range_id: int) -> tuple:
        """
        Reads the text range from the database corresponding to the given range_id and returns a tuple.
        The tuple contains:
         - integer id of the range
         - integer index of the start of the text range (inclusive)
         - integer index of the end of the text range (inclusive)
        Parameters
        ----------
        range_id: int - integer id of the sequence

        Returns
        -------
        tuple - the corresponding text range as a tuple
        """
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
        """
        Creates a new text range in the database with the provided start and end ranges.
        Returns the integer id of the new text range. IDs automatically increment by 1 from the max ID
        Parameters
        ----------
        start: int - the integer index of the start of the text range (inclusive)
        end: int - the integer index of the end of the text range (inclusive)

        Returns
        -------
        int - The integer id of the new text range
        """
        id_field = TextRangeCSVRepository.RANGE_ID_FIELD
        start_field = TextRangeCSVRepository.RANGE_START_FIELD
        end_field = TextRangeCSVRepository.RANGE_END_FIELD

        self._read_database_into_cache()

        matches: ndarray = self._database_cache.loc[
            ((self._database_cache[start_field] == start) &
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
        """
        Updates the attributes for the text range in the database with the given range_id.
        Returns True if the operation succeeds, False if the operation fails or the text range is not found.
        Parameters
        ----------
        range_id: int - integer id of the text range
        start: int - the integer index of the start of the text range (inclusive)
        end: int - the integer index of the end of the text range (exclusive)

        Returns
        -------
        bool - True if the operation succeeds, False if the operation fails or the text range is not found.
        """
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

    def clear_database(self):
        """
        Deletes all contents from the database, except for column headers
        """
        self._database_cache = self._database_cache.iloc[0:0]
        self._write_cache_to_database()
