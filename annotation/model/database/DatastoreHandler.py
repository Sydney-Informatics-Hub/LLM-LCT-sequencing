from typing import Optional

from pandas import DataFrame, Series

from annotation.model.data_structures import ClauseSequence, Classification
from annotation.model.database import AnnotationDAO


class DatastoreHandler:
    SEQ_ID_FIELD: str = "sequence_id"
    C1_TEXT_FIELD: str = "c1"
    C1_START_FIELD: str = "c1_start"
    C1_END_FIELD: str = "c1_end"
    C2_TEXT_FIELD: str = "c2"
    C2_START_FIELD: str = "c2_start"
    C2_END_FIELD: str = "c2_end"
    LINKAGE_FIELD: str = "linkage_words"
    PREDICTED_NAME_FIELD: str = "predicted_classes_name"
    PREDICTED_FIELD: str = "predicted_classes"
    CORRECTED_NAME_FIELD: str = "corrected_classes_name"
    CORRECTED_FIELD: str = "corrected_classes"
    WINDOW_START_FIELD: str = "window_start"
    WINDOW_END_FIELD: str = "window_end"
    REASONING_FIELD: str = "reasoning"
    FIELD_DTYPES: dict = {SEQ_ID_FIELD: int, C1_START_FIELD: int, C1_END_FIELD: int,
                          C2_START_FIELD: int, C2_END_FIELD: int, LINKAGE_FIELD: str,
                          PREDICTED_FIELD: str, CORRECTED_FIELD: str, REASONING_FIELD: str,
                          WINDOW_START_FIELD: int, WINDOW_END_FIELD: int}
    REQUIRED_FIELDS: list[str, ...] = [field for field in FIELD_DTYPES.keys()]

    def __init__(self, annotation_dao: AnnotationDAO):
        self.annotation_dao: AnnotationDAO = annotation_dao

    def _write_database_rows(self, row: Series):
        c1_start: int = row[DatastoreHandler.C1_START_FIELD]
        c1_end: int = row[DatastoreHandler.C1_END_FIELD]
        c2_start: int = row[DatastoreHandler.C2_START_FIELD]
        c2_end: int = row[DatastoreHandler.C2_END_FIELD]

        c1_id: int = self.annotation_dao.create_clause(c1_start, c1_end)
        c2_id: int = self.annotation_dao.create_clause(c2_start, c2_end)

        try:
            linkage_words: str | float = row[DatastoreHandler.LINKAGE_FIELD]
            if type(linkage_words) is float:
                linkage_words = ""
            predicted_classes: str = row[DatastoreHandler.PREDICTED_FIELD]
            correct_classes: str = row[DatastoreHandler.CORRECTED_FIELD]
            reasoning: str = row[DatastoreHandler.REASONING_FIELD]

            self.annotation_dao.create_sequence(c1_id, c2_id, linkage_words, predicted_classes,
                                                correct_classes, reasoning)
        except KeyError:
            self.annotation_dao.create_sequence(c1_id, c2_id)

    def _update_sequence_row(self, row: Series):
        sequence_id: int = row[DatastoreHandler.SEQ_ID_FIELD]
        linkage_words: str | float = row[DatastoreHandler.LINKAGE_FIELD]
        if type(linkage_words) is float:
            linkage_words = ""
        predicted_classes: str = row[DatastoreHandler.PREDICTED_FIELD]
        corrected_classes: str = row[DatastoreHandler.CORRECTED_FIELD]
        reasoning: str = row[DatastoreHandler.REASONING_FIELD]

        self.annotation_dao.update_sequence(sequence_id, linkage_words,
                                            predicted_classes, corrected_classes, reasoning)

    def build_text_datastore(self, text_file_content: str):
        self.annotation_dao.write_text_file(text_file_content)

    def build_clause_datastores(self, master_sequence_df: DataFrame):
        master_sequence_df.apply(self._write_database_rows, axis=1)

    def update_sequence_datastores(self, master_sequence_df: DataFrame):
        type_df = master_sequence_df.astype(DatastoreHandler.FIELD_DTYPES)
        type_df.apply(self._update_sequence_row, axis=1)

    def update_pre_llm_sequence_file(self, pre_llm_sequence_path: str):
        pre_llm_columns = [DatastoreHandler.SEQ_ID_FIELD,
                           DatastoreHandler.C1_START_FIELD, DatastoreHandler.C1_END_FIELD,
                           DatastoreHandler.C2_START_FIELD, DatastoreHandler.C2_END_FIELD]
        pre_llm_data: list[dict] = []

        sequences: list[ClauseSequence] = self.annotation_dao.get_all_sequences()
        for sequence in sequences:
            sequence_data: list = [sequence.get_id()]
            sequence_data.extend(sequence.get_first_clause().get_range())
            sequence_data.extend(sequence.get_second_clause().get_range())

            sequence_dict: dict = {col: data for col, data in zip(pre_llm_columns, sequence_data)}
            pre_llm_data.append(sequence_dict)

        pre_llm_df = DataFrame(pre_llm_data, columns=pre_llm_columns)
        pre_llm_df.to_csv(pre_llm_sequence_path, index=False, na_rep='')

    def build_export_dataframe(self) -> DataFrame:
        export_columns = [DatastoreHandler.SEQ_ID_FIELD, DatastoreHandler.C1_TEXT_FIELD,
                          DatastoreHandler.C1_START_FIELD, DatastoreHandler.C1_END_FIELD,
                          DatastoreHandler.C2_TEXT_FIELD, DatastoreHandler.C2_START_FIELD,
                          DatastoreHandler.C2_END_FIELD, DatastoreHandler.LINKAGE_FIELD,
                          DatastoreHandler.PREDICTED_FIELD, DatastoreHandler.PREDICTED_NAME_FIELD,
                          DatastoreHandler.CORRECTED_FIELD, DatastoreHandler.CORRECTED_NAME_FIELD,
                          DatastoreHandler.WINDOW_START_FIELD, DatastoreHandler.WINDOW_END_FIELD,
                          DatastoreHandler.REASONING_FIELD]
        export_data: list[dict] = []

        clause_texts: dict[int, str] = self.annotation_dao.get_all_clause_text()
        sequences: list[ClauseSequence] = self.annotation_dao.get_all_sequences()
        for sequence in sequences:
            sequence_data: list = [sequence.get_id()]

            clause_a_text: Optional[str] = clause_texts.get(sequence.get_first_clause().get_id())
            clause_a_text = "" if clause_a_text is None else clause_a_text
            sequence_data.append(clause_a_text)
            sequence_data.extend(sequence.get_first_clause().get_range())

            clause_b_text: Optional[str] = clause_texts.get(sequence.get_second_clause().get_id())
            clause_b_text = "" if clause_b_text is None else clause_b_text
            sequence_data.append(clause_b_text)
            sequence_data.extend(sequence.get_second_clause().get_range())

            linkage_words: str = ",".join(sequence.get_linkage_words())
            sequence_data.append(linkage_words)

            predicted_classes: Optional[list[Classification]] = sequence.get_predicted_classes()
            predicted_class_values: str = ''
            predicted_class_names: str = '-'
            if predicted_classes is not None:
                predicted_class_values = ','.join([str(c.value) for c in predicted_classes])
                predicted_class_names = ','.join([c.name for c in predicted_classes])
            sequence_data.append(predicted_class_values)
            sequence_data.append(predicted_class_names)

            correct_classes: Optional[list[Classification]] = sequence.get_correct_classes()
            corrected_class_values: str = ''
            corrected_class_names: str = '-'
            if correct_classes is not None:
                corrected_class_values = ','.join([str(c.value) for c in correct_classes])
                corrected_class_names = ','.join([c.name for c in correct_classes])
            sequence_data.append(corrected_class_values)
            sequence_data.append(corrected_class_names)

            window_start: int = sequence.get_first_clause().get_range()[0]
            window_end: int = sequence.get_second_clause().get_range()[1]
            sequence_data.append(window_start)
            sequence_data.append(window_end)

            reasoning: str = sequence.get_reasoning()
            sequence_data.append(reasoning)

            sequence_dict: dict = {col: data for col, data in zip(export_columns, sequence_data)}
            export_data.append(sequence_dict)

        df = DataFrame(export_data, columns=export_columns)
        return df.astype(DatastoreHandler.FIELD_DTYPES)

    def build_plot_dataframe(self) -> Optional[DataFrame]:
        sequence_position_field: str = "sequence_position"
        classification_field: str = "classification"
        plot_columns = [sequence_position_field, classification_field]
        plot_data: list[dict] = []
        default_class_name: str = 'NA'

        sequences: list[ClauseSequence] = self.annotation_dao.get_all_sequences()
        if len(sequences) == 0:
            return None
        for sequence in sequences:
            sequence_data: list = []
            clause_a_range, clause_b_range = sequence.get_clause_ranges()
            sequence_position: int = (sum(clause_a_range) + sum(clause_b_range)) // 4
            sequence_data.append(sequence_position)

            predicted_classes: Optional[list[Classification]] = sequence.get_predicted_classes()
            correct_classes: Optional[list[Classification]] = sequence.get_correct_classes()
            class_names: str
            if predicted_classes is not None:
                class_names = ','.join([c.name for c in predicted_classes])
            elif correct_classes is not None:
                class_names = ','.join([c.name for c in correct_classes])
            else:
                class_names = default_class_name
            sequence_data.append(class_names)

            sequence_dict: dict = {col: data for col, data in zip(plot_columns, sequence_data)}
            plot_data.append(sequence_dict)

        return DataFrame(plot_data, columns=plot_columns)
