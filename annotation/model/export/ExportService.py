from io import BytesIO
from typing import Callable

from pandas import DataFrame, ExcelWriter


class ExportService:
    def __init__(self):
        self.file_type_mapping: dict[str, Callable] = {
            "xlsx": self.export_to_excel,
            "csv": self.export_to_csv,
            "ods": self.export_to_open_document
        }

    def get_filetypes(self) -> list[str]:
        return list(self.file_type_mapping.keys())

    def export(self, filetype: str, df: DataFrame) -> BytesIO:
        if filetype not in self.file_type_mapping:
            raise ValueError(f"{filetype} is not a valid export format")
        file_object: BytesIO = self.file_type_mapping[filetype](df)
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
