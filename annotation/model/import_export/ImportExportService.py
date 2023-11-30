from io import BytesIO
from typing import Callable

from pandas import DataFrame, ExcelWriter, read_excel, read_csv


class ImportExportService:
    """
    A converter between DataFrame objects and table-like file types.
    Supported filetypes include xlsx, csv, and ods.
    """
    def __init__(self):
        self.export_type_mapping: dict[str, Callable] = {
            "xlsx": self.export_to_excel,
            "csv": self.export_to_csv,
            "ods": self.export_to_open_document
        }
        self.import_type_mapping: dict[str, Callable] = {
            "xlsx": self.import_from_excel,
            "csv": self.import_from_csv,
            "ods": self.import_from_open_document
        }

    def get_filetypes(self) -> list[str]:
        return list(self.export_type_mapping.keys())

    def export(self, filetype: str, df: DataFrame) -> BytesIO:
        if filetype not in self.export_type_mapping:
            raise ValueError(f"{filetype} is not a valid export format")
        file_object: BytesIO = self.export_type_mapping[filetype](df)
        file_object.seek(0)

        return file_object

    def export_to_excel(self, df: DataFrame) -> BytesIO:
        excel_object = BytesIO()
        with ExcelWriter(excel_object, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        return excel_object

    def export_to_open_document(self, df: DataFrame) -> BytesIO:
        open_doc_object = BytesIO()
        with ExcelWriter(open_doc_object, engine="odf") as writer:
            df.to_excel(writer, index=False)

        return open_doc_object

    def export_to_csv(self, df: DataFrame) -> BytesIO:
        csv_object = BytesIO()
        df.to_csv(csv_object, index=False)

        return csv_object

    def import_file(self, filetype: str, file_object: BytesIO) -> DataFrame:
        if filetype not in self.export_type_mapping:
            raise ValueError(f"{filetype} is not a valid import format")
        file_object.seek(0)
        df: DataFrame = self.import_type_mapping[filetype](file_object)

        return df

    def import_from_excel(self, file_object: BytesIO) -> DataFrame:
        return read_excel(file_object, engine="openpyxl")

    def import_from_open_document(self, file_object: BytesIO) -> DataFrame:
        return read_excel(file_object, engine="odf")

    def import_from_csv(self, file_object: BytesIO) -> DataFrame:
        return read_csv(file_object)
