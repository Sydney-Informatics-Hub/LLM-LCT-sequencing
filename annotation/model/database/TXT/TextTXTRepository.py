import os

from annotation.model.database.DatabaseExceptions import DatabaseFileSizeError
from annotation.model.database.interfaces import TextRepository


class TextTXTRepository(TextRepository):
    MAX_SIZE_BYTES: int = 2000000

    def __init__(self, text_txt_filename: str):
        self._database_filename: str = text_txt_filename
        self._database_cache: str = ""
        self._cache_updated: bool = False

        # Validate the file can be opened with read permissions
        if not (os.access(self._database_filename, os.R_OK)):
            raise PermissionError(f"No permissions to read the file: {self._database_filename}")

        # Validate the file is not too large to be read into memory
        if os.path.getsize(self._database_filename) > TextTXTRepository.MAX_SIZE_BYTES:
            raise DatabaseFileSizeError(f"Database file is too large: {self._database_filename}")

        self._read_database_into_cache()

    def _read_database_into_cache(self):
        if self._cache_updated:
            return

        with open(self._database_filename) as f:
            self._database_cache = f.read()

        self._cache_updated = True

    def read_all(self) -> str:
        self._read_database_into_cache()

        return self._database_cache

    def read_by_range(self, start: int, end: int) -> str:
        if start < 0:
            raise ValueError(f"start argument cannot be less than 0. Provided start value: {start}")
        if end < start:
            raise ValueError(f"end argument must not be lower than start argument. "
                             f"Provided start value: {start}, provided end value: {end}")
        largest_index: int = self.get_end_index()
        if end > largest_index:
            raise ValueError(f"end argument cannot be greater than largest index in text file. "
                             f"Provided end argument: {end}, largest index: {largest_index}")

        if end == 0:
            return ""

        self._read_database_into_cache()

        return self._database_cache[start:end]

    def get_end_index(self) -> int:
        self._read_database_into_cache()

        return len(self._database_cache)
