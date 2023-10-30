from pandas import DataFrame, read_csv, Series

from annotation.model.database import AnnotationDAO


class DatastoreBuilder:
    SEQ_ID_FIELD: str = "sequence_id"
    C1_START_FIELD: str = "c1_start"
    C1_END_FIELD: str = "c1_end"
    C2_START_FIELD: str = "c2_start"
    C2_END_FIELD: str = "c2_end"
    LINKAGE_FIELD: str = "linkage_words"
    PREDICTED_FIELD: str = "classes_predict"
    REASONING_FIELD: str = "reasoning"
    CONFIDENCE_FIELD: str = "confidence"
    WINDOW_START_FIELD: str = "window_start"
    WINDOW_END_FIELD: str = "window_end"
    FIELD_DTYPES: dict = {SEQ_ID_FIELD: int, C1_START_FIELD: int, C1_END_FIELD: int,
                          C2_START_FIELD: int, C2_END_FIELD: int, LINKAGE_FIELD: str,
                          PREDICTED_FIELD: str, REASONING_FIELD: str, CONFIDENCE_FIELD: float,
                          WINDOW_START_FIELD: int, WINDOW_END_FIELD: int}
    REQUIRED_FIELDS: list[str, ...] = [field for field in FIELD_DTYPES.keys()]

    def __init__(self, annotation_dao: AnnotationDAO):
        self.annotation_dao: AnnotationDAO = annotation_dao

    def _write_database_row(self, row: Series):
        c1_start: int = row[DatastoreBuilder.C1_START_FIELD]
        c1_end: int = row[DatastoreBuilder.C1_END_FIELD]
        c2_start: int = row[DatastoreBuilder.C2_START_FIELD]
        c2_end: int = row[DatastoreBuilder.C2_END_FIELD]

        c1_id: int = self.annotation_dao.create_clause(c1_start, c1_end)
        c2_id: int = self.annotation_dao.create_clause(c2_start, c2_end)

        linkage_words: str | float = row[DatastoreBuilder.LINKAGE_FIELD]
        if type(linkage_words) is float:
            linkage_words = ""
        predicted_classes: str = row[DatastoreBuilder.PREDICTED_FIELD]

        self.annotation_dao.create_sequence(c1_id, c2_id, linkage_words, predicted_classes)

    def build_data_stores(self, text_file_content: str, master_sequence_df: DataFrame):
        self.annotation_dao.write_text_file(text_file_content)
        master_sequence_df.apply(self._write_database_row, axis=1)
