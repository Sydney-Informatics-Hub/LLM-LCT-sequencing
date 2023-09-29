import os

from numpy import ndarray
from pandas import DataFrame, read_csv
from csv import DictReader
from typing import Optional

from annotation.model.database.DatabaseExceptions import DatabaseFieldError, DatabaseEntryError
from annotation.model.database.ParagraphRepository import ParagraphRepository


class ParagraphCSVRepository(ParagraphRepository):
    ID_FIELD: str = "paragraph_id"
    TEXT_FIELD: str = "paragraph_text"
    FIELD_DTYPES: dict = {ID_FIELD: int, TEXT_FIELD: 'string'}
    REQUIRED_FIELDS: list[str, ...] = [field for field in FIELD_DTYPES.keys()]

    def __init__(self, database_csv_filename: str):
        self._database_filename: str = database_csv_filename
        self._database_cache: DataFrame = DataFrame(columns=ParagraphCSVRepository.REQUIRED_FIELDS)
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
            for field in ParagraphCSVRepository.REQUIRED_FIELDS:
                if field not in reader.fieldnames:
                    raise DatabaseFieldError(f"Missing {field} column from paragraph database")

    def _read_database_into_cache(self):
        if self._cache_updated:
            return

        self._validate_database_fields()
        self._database_cache = read_csv(filepath_or_buffer=self._database_filename, header=0,
                                        names=ParagraphCSVRepository.REQUIRED_FIELDS,
                                        dtype=ParagraphCSVRepository.FIELD_DTYPES)

        self._cache_updated = True

    def _write_cache_to_database(self):
        self._database_cache.to_csv(path_or_buf=self._database_filename, index=False,
                                    columns=ParagraphCSVRepository.REQUIRED_FIELDS)

        self._cache_updated = True

    def read_all(self) -> ndarray:
        self._read_database_into_cache()

        return self._database_cache.values

    def read_by_id(self, paragraph_id: int) -> Optional[str]:
        id_field = ParagraphCSVRepository.ID_FIELD
        text_field = ParagraphCSVRepository.TEXT_FIELD

        self._read_database_into_cache()

        matches = self._database_cache.loc[(self._database_cache[id_field] == paragraph_id), [text_field]].values

        if len(matches) == 1:
            return str(matches[0][0])
        elif len(matches) > 1:
            raise DatabaseEntryError(f"There are more than one entries for the paragraph id: {paragraph_id}")

    def create(self, new_paragraph_text: str) -> int:
        id_field = ParagraphCSVRepository.ID_FIELD
        text_field = ParagraphCSVRepository.TEXT_FIELD

        self._validate_database_fields()

        existing_ids = self._database_cache[id_field].values
        if len(existing_ids) == 0:
            highest_id: int = 0
        else:
            highest_id: int = existing_ids.max()

        new_id: int = highest_id + 1
        new_entry = {ParagraphCSVRepository.ID_FIELD: new_id, text_field: new_paragraph_text}
        self._database_cache.add(new_entry)

        self._write_cache_to_database()

        return new_id

    def update(self, paragraph_id: int, updated_text: str) -> bool:
        id_field = ParagraphCSVRepository.ID_FIELD
        text_field = ParagraphCSVRepository.TEXT_FIELD

        self._validate_database_fields()

        matches = self._database_cache.loc[(self._database_cache[id_field] == paragraph_id), [text_field]].values

        if len(matches) == 0:
            return False
        elif len(matches) > 1:
            raise DatabaseEntryError(f"There are more than one entries for the paragraph id: {paragraph_id}")
        else:
            self._database_cache.loc[(self._database_cache[id_field] == paragraph_id), [text_field]] = updated_text
            self._write_cache_to_database()
            return True

    def delete(self, paragraph_id: int) -> bool:
        id_field = ParagraphCSVRepository.ID_FIELD
        text_field = ParagraphCSVRepository.TEXT_FIELD

        self._validate_database_fields()

        matches = self._database_cache.loc[(self._database_cache[id_field] == paragraph_id), [text_field]].values

        if len(matches) == 0:
            return False
        elif len(matches) > 1:
            raise DatabaseEntryError(f"There are more than one entries for the paragraph id: {paragraph_id}")
        else:
            self._database_cache = self._database_cache.loc[~(self._database_cache[id_field] == paragraph_id)]
            self._write_cache_to_database()
            return True
