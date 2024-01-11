from io import BytesIO
from typing import Callable

from pandas import DataFrame, ExcelWriter, read_excel, read_csv


class ImportExportService:
    """
    A converter between DataFrame objects and table-like file types.
    Supported filetypes include xlsx and csv.
    """
    def __init__(self):
        self.export_type_mapping: dict[str, Callable] = {
            "xlsx": self.export_to_excel,
            "csv": self.export_to_csv
        }
        self.import_type_mapping: dict[str, Callable] = {
            "xlsx": self.import_from_excel,
            "csv": self.import_from_csv
        }

    def get_filetypes(self) -> list[str]:
        return list(self.export_type_mapping.keys())

    def export(self, df: DataFrame, filetype: str) -> BytesIO:
        if filetype not in self.export_type_mapping:
            raise ValueError(f"{filetype} is not a valid export format")
        file_object: BytesIO = self.export_type_mapping[filetype](df)
        file_object.seek(0)

        return file_object

    def export_to_excel(self, df: DataFrame) -> BytesIO:
        excel_object = BytesIO()
        df.to_excel(excel_object, index=False)

        return excel_object

    def export_to_csv(self, df: DataFrame) -> BytesIO:
        csv_object = BytesIO()
        df.to_csv(csv_object, index=False)

        return csv_object

    def import_file(self, file_path_or_object: BytesIO | str, filetype: str) -> DataFrame:
        if filetype not in self.export_type_mapping:
            raise ValueError(f"{filetype} is not a valid import format")
        if isinstance(file_path_or_object, BytesIO):
            file_path_or_object.seek(0)

        df: DataFrame = self.import_type_mapping[filetype](file_path_or_object)
        return df

    def import_from_excel(self, file_path_or_object: BytesIO | str) -> DataFrame:
        return read_excel(file_path_or_object, na_filter=False)

    def import_from_csv(self, file_path_or_object: BytesIO | str) -> DataFrame:
        return read_csv(file_path_or_object, na_filter=False)
