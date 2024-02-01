import os
from pathlib import Path

from annotation.model.database.DatabaseExceptions import DatabaseFileSizeError


class TextTXTRepository:
    MAX_SIZE_BYTES: int = 2000000

    def __init__(self, text_txt_path: Path):
        self._database_path: Path = text_txt_path
        self._database_cache: str = ""
        self._cache_updated: bool = False

        # If file does not exist, create parent directories and file with no content
        if not os.path.exists(text_txt_path):
            text_txt_path.parent.mkdir(parents=True, exist_ok=True)
            text_txt_path.write_text("")

        # Validate the file can be opened with read and write permissions
        if not os.access(text_txt_path, os.R_OK):
            raise PermissionError(f"No permissions to read the file: {text_txt_path}")
        if not os.access(text_txt_path, os.W_OK):
            raise PermissionError(f"No permissions to write to the file: {text_txt_path}")

        # Validate the file is not too large to be read into memory
        if os.path.getsize(text_txt_path) > TextTXTRepository.MAX_SIZE_BYTES:
            raise DatabaseFileSizeError(f"Database file is too large: {text_txt_path}")

        self._read_database_into_cache()

    def _read_database_into_cache(self):
        if self._cache_updated:
            return

        with open(self._database_path) as f:
            self._database_cache = f.read()

        self._cache_updated = True

    def _write_cache_to_database(self):
        with open(self._database_path, 'w') as f:
            f.write(self._database_cache)

        self._cache_updated = True

    def read_all(self) -> str:
        """
        Reads all text in from the database file as a str
        """
        self._read_database_into_cache()

        return self._database_cache

    def read_by_range(self, start: int, end: int) -> str:
        """
        Reads text in from the database file as a str between the specified range.
        The range is inclusive of start and exclusive of end.

        Parameters
        ----------
        start: int - The start index to read from. Cannot be negative. The first character has index of 0.
        end: int - The end index to read to. Range is exclusive of end index.
        Cannot be lower than start and cannot be greater than the maximum range of the text

        Returns
        -------
        A string of the text between the specified range, inclusive of start and exclusive of end.
        """
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
        """
        Returns the end range of the text. The text contains characters with indexes 0 to (end - 1).
        If the text is empty, will return 0.
        Returns
        -------
        The range end index as an integer.
        """
        self._read_database_into_cache()

        return len(self._database_cache)

    def write_file(self, text: str):
        """
        Accepts a string and writes the string to the database file.
        Parameters
        ----------
        text: str - Any string, can be empty.
        """
        self._database_cache = text
        self._write_cache_to_database()

    def clear_database(self):
        """
        Deletes all contents from the text database
        """
        self._database_cache = ""
        self._write_cache_to_database()
