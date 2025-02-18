```mermaid
---
title: annotation
---
classDiagram
    class Annotation {
        - __init__(self, debug) None
        + run(self)
    }

    class AnnotationController {
        + int MIN_SEQUENCE_ID
        + str OPENAI_API_KEY_ENVIRON
        - __init__(self, annotation_service, notifier_service, import_export_service, llm_examples_path, llm_definitions_path, llm_zero_prompt_path, llm_cost_path, log_file_path, debug) None
        + @staticmethod configure_logging(log_file_path, debug)
        + display_error(self, error_msg)
        + display_success(self, success_msg)
        + display_info(self, info_msg)
        + set_loading_msg(self, loading_msg, *args, **kwargs)
        + stop_loading_indicator(self)
        + get_loading_msg(self) Optional[str]
        + add_update_text_display_callable(self, update_text_display_callable)
        + update_displays(self)
        + get_text(self) str
        + get_all_clause_text(self) dict[int, str]
        + get_min_sequence_id(self) int
        + get_max_sequence_id(self) int
        + get_current_sequence_id(self) int
        + set_current_sequence_id(self, new_sequence_id)
        + get_curr_sequence_ranges(self) Optional[SequenceTuple]
        + get_curr_sequence_linkage_words(self) Optional[list[str]]
        + get_all_classifications(self) list[str]
        + get_predicted_classifications(self) list[str]
        + get_correct_classifications(self) list[str]
        + get_reasoning(self) str
        + get_sequence_count(self) int
        + get_cost_time_estimates(self) Optional[tuple[float, float]]
        + load_source_file(self, source_file_content, source_filetype)
        + prepare_llm_processor(self, llm_definitions, llm_examples, llm_zero_prompt)
        + llm_process_sequences(self)
        + load_preprocessed_sequences(self, preprocessed_content, preprocessed_filetype)
        + set_api_key(self, key) bool
        + next_sequence(self)
        + prev_sequence(self)
        + set_correct_classifications(self, classifications)
        + add_sequence(self, clause_a_id, clause_b_id) int
        + delete_curr_sequence(self)
        + export(self, filetype) Optional[BytesIO]
        + get_import_export_file_formats(self) list[str]
        + get_plot_data(self) Optional[DataFrame]
        + get_plot_weights_data(self) Optional[DataFrame]
    }

    class DatastoreHandler {
        + str SEQ_ID_FIELD
        + str C1_TEXT_FIELD
        + str C1_START_FIELD
        + str C1_END_FIELD
        + str C2_TEXT_FIELD
        + str C2_START_FIELD
        + str C2_END_FIELD
        + str LINKAGE_FIELD
        + str PREDICTED_NAME_FIELD
        + str PREDICTED_FIELD
        + str CORRECTED_NAME_FIELD
        + str CORRECTED_FIELD
        + str WINDOW_START_FIELD
        + str WINDOW_END_FIELD
        + str REASONING_FIELD
        + dict FIELD_DTYPES
        + list[str, ...] REQUIRED_FIELDS
        - __init__(self, annotation_dao) None
        - _write_database_rows(self, row)
        - _update_sequence_row(self, row)
        + build_text_datastore(self, text_file_content)
        + build_clause_datastores(self, master_sequence_df)
        + update_sequence_datastores(self, master_sequence_df)
        + update_pre_llm_sequence_file(self, pre_llm_sequence_path)
        + build_export_dataframe(self) DataFrame
        + build_plot_dataframe(self) Optional[DataFrame]
        + build_weights_plot_dataframe(self) Optional[DataFrame]
    }

    class DatabaseStateError

    class DatabaseFieldError

    class DatabaseEntryError

    class DatabaseFileSizeError

    class AnnotationDAO {
        - __init__(self, text_database_fn, clause_database_fn, sequence_database_fn) None
        - @staticmethod _split_to_int_list(sequence_data) list[int]
        - @staticmethod _join_str_from_int_list(int_list) str
        + write_text_file(self, text)
        + get_text(self) str
        + create_clause(self, start, end) int
        + get_all_clauses(self) list[TextRange]
        + get_all_clause_text(self) dict[int, str]
        + get_sequence_count(self) int
        - _read_sequence_from_sequence_data(self, sequence_data) ClauseSequence
        + get_sequence_by_id(self, sequence_id) Optional[ClauseSequence]
        + get_all_sequences(self) list[ClauseSequence]
        + update_sequence(self, sequence_id, linkage_words, predicted_classes, corrected_classes, reasoning) bool
        + update_sequence_classifications(self, sequence_id, correct_classes)
        + create_sequence(self, clause_a_id, clause_b_id, linkage_words, predicted_classes, correct_classes, reasoning) int
        + delete_sequence(self, sequence_id)
        + clear_all_data_stores(self)
    }

    class TextTXTRepository {
        + int MAX_SIZE_BYTES
        - __init__(self, text_txt_path) None
        - _read_database_into_cache(self)
        - _write_cache_to_database(self)
        + read_all(self) str
        + read_by_range(self, start, end) str
        + get_end_index(self) int
        + write_file(self, text)
        + clear_database(self)
    }

    class TextRangeCSVRepository {
        + str RANGE_ID_FIELD
        + str RANGE_START_FIELD
        + str RANGE_END_FIELD
        + dict FIELD_DTYPES
        + list[str, ...] REQUIRED_FIELDS
        - __init__(self, database_csv_path) None
        - _validate_database_fields(self)
        - _read_database_into_cache(self)
        - _write_cache_to_database(self)
        + read_all(self) ndarray
        + read_by_id(self, range_id) tuple
        + create(self, start, end) int
        + update(self, range_id, start, end) bool
        + clear_database(self)
    }

    class SequenceCSVRepository {
        + str SEQUENCE_ID_FIELD
        + str CLAUSE_A_ID_FIELD
        + str CLAUSE_B_ID_FIELD
        + str LINKAGE_FIELD
        + str PREDICTED_CLASSES
        + str CORRECTED_CLASSES
        + str REASONING_FIELD
        + dict FIELD_DTYPES
        + list[str, ...] REQUIRED_FIELDS
        + str CLASS_LS_DELIMITER
        + str LINKAGE_LS_DELIMITER
        - __init__(self, database_csv_path) None
        - _validate_database_fields(self)
        - _read_database_into_cache(self)
        - _write_cache_to_database(self)
        + read_all(self) ndarray
        + read_by_id(self, sequence_id) tuple
        + read_by_clause_id(self, clause_id) ndarray
        + create(self, clause_a_id, clause_b_id, linkage_words, predicted_classes, correct_classes, reasoning) int
        + update(self, sequence_id, linkage_words, predicted_classes, corrected_classes, reasoning) bool
        + delete(self, sequence_id) bool
        + clear_database(self)
    }

    class Classification {
        + int NA
        + int INC
        + int COH
        + int REP
        + int REI
        + int SEQ
        + int CON
        + int SUB
        + int INT
    }

    class ClauseSequence {
        - __init__(self, sequence_id, first_clause, second_clause, linkage_words, predicted_class, correct_class, reasoning) None
        - __eq__(self, other) bool
        - __hash__(self)
        + get_id(self) int
        + get_first_clause(self) TextRange
        + get_second_clause(self) TextRange
        + get_linkage_words(self) list[str]
        + get_clause_ranges(self) SequenceTuple
        + get_reasoning(self) str
        + get_predicted_classes(self) Optional[list[Classification]]
        + set_predicted_classes(self, predicted_classes)
        + get_correct_classes(self) Optional[list[Classification]]
        + set_correct_classes(self, correct_classes)
    }

    class TextRange {
        - __init__(self, start, end, range_id) None
        - __eq__(self, other) bool
        - __hash__(self)
        + get_id(self) Optional[int]
        + get_start(self) int
        + get_end(self) int
        + get_range(self) TextRangeTuple
    }

    class ImportExportService {
        + @staticmethod export_to_excel(df) BytesIO
        + @staticmethod export_to_csv(df) BytesIO
        + @staticmethod import_from_excel(file_path_or_object) DataFrame
        + @staticmethod import_from_csv(file_path_or_object) DataFrame
        - __init__(self) None
        + get_filetypes(self) list[str]
        + export(self, df, filetype) BytesIO
        + import_file(self, file_path_or_object, filetype) DataFrame
    }

    class SourceFileClauser {
        + NLP
        - __init__(self, source_file, filetype) None
        + get_text(self) str
        + @staticmethod read_docx(docx_file) str
        + @staticmethod read_txt(txt_file) str
        + generate_clause_dataframe(self) DataFrame
    }

    class SequencingTool {
        - __init__(self, clause_df) None
        - _generate_groupings(self, item_df, item_range) list[dict]
        + generate_initial_sequence_df(self) DataFrame
    }

    class AnnotationService {
        + str OPEN_AI_MODEL
        - __init__(self) None
        + load_source_file(self, source_file_content, filetype)
        + initialise_llm_processor(self, llm_examples_path, llm_definitions_path, llm_zero_prompt_path, progress_update_fn)
        + calculate_llm_cost_time_estimates(self, llm_cost_path) tuple[float, float]
        + perform_llm_processing(self) str
        + build_datastore(self, master_sequence_df)
        + get_dataframe_for_export(self) DataFrame
        + get_dataframe_for_plot(self) Optional[DataFrame]
        + get_weights_dataframe_for_plot(self) Optional[DataFrame]
        + get_text(self) str
        + get_all_clause_text(self) dict[int, str]
        + get_sequence_count(self) int
        + get_sequence_clause_ranges(self, sequence_id) Optional[SequenceTuple]
        + get_sequence_linkage_words(self, sequence_id) Optional[list[str]]
        + get_all_sequence_classifications(self) list[str]
        + get_sequence_predict_classes(self, sequence_id) list[str]
        + get_sequence_correct_classes(self, sequence_id) list[str]
        + set_sequence_correct_classes(self, sequence_id, classifications)
        + get_sequence_reasoning(self, sequence_id) str
        + create_sequence(self, clause_a_id, clause_b_id) int
        + delete_sequence(self, sequence_id)
    }

    class AnnotationViewWrapper {
        - __init__(self, controller) None
        + get_layout(self)
    }

    class LoadingIndicator {
        - __init__(self, controller) None
        + get_component(self)
        + update_display(self)
    }

    class NotifierService {
        - __init__(self) None
        + notify_error(self, error_msg, duration)
        + notify_success(self, success_msg, duration)
        + notify_info(self, info_msg, duration)
        + clear_all(self)
    }

    class ClauseSequenceControls {
        - __init__(self, controller, add_sequence_controls_fn) None
        + @staticmethod format_first_clause_str(clause_range) str
        + @staticmethod format_second_clause_str(clause_range) str
        + @staticmethod format_overlap_str(overlap_range) str
        + @staticmethod format_linkage_str(linkage_words) str
        + @staticmethod get_clause_overlap(clause_a_range, clause_b_range) Optional[tuple[int, int]]
        + get_component(self)
        + set_visibility(self, is_visible)
        + toggle_visibility(self)
        + update_display(self)
        + next_sequence(self, event)
        + prev_sequence(self, event)
        + toggle_show_manage_sequence_pane(self, *_)
        + reset_manage_sequence_pane(self)
        + show_add_sequence_pane(self, *_)
        + delete_sequence(self, event)
        + set_sequence_id(self, sequence_id)
    }

    class AddSequenceControls {
        - __init__(self, controller, reset_visibility_fn) None
        + get_component(self)
        + update_display(self)
        + set_visibility(self, is_visible)
        + toggle_visibility(self)
        + save_sequence(self, *_)
        + exit_pane(self, *_)
    }

    class SequenceClassificationControls {
        - __init__(self, controller) None
        + get_component(self)
        + set_visibility(self, is_visible)
        + toggle_visibility(self)
        + update_display(self)
        + revert_to_prediction(self, *_)
        + set_correct_classification(self, classifications)
    }

    class Controls {
        - __init__(self, controller) None
        + update_display(self)
        + get_component(self)
        + add_sequence_controls(self)
        + reset_visibility(self)
    }

    class ExportControls {
        + str FILENAME
        - __init__(self, controller) None
        + get_component(self)
        + set_button_disabled(self, is_disabled)
        + export(self, filetype, *_)
        + toggle_options_visibility(self, *_)
    }

    class FileUploadWidget {
        - __init__(self, file_description, filetypes_ls) None
        + get_component(self)
        + get_file_content(self) Optional[BytesIO]
        + get_filetype(self) Optional[str]
    }

    class UnprocessedModeLoader {
        - __init__(self, controller) None
        + get_component(self)
        + get_visible(self) bool
        + set_visible(self, visible)
        + update_display(self)
        + write_api_key(self, key) str
        - _format_time_from_seconds(self, seconds) str
        + set_cost_time_estimate(self)
        + load_files(self, *_)
        + llm_process_sequences(self, *_)
    }

    class PreprocessedModeLoader {
        - __init__(self, controller) None
        + get_component(self)
        + get_visible(self) bool
        + set_visible(self, visible)
        + load_files(self, *_)
    }

    class SourceLoader {
        - __init__(self, controller) None
        + get_component(self)
        + toggle_unprocessed_mode(self, *_)
        + toggle_preprocessed_mode(self, *_)
    }

    class FigureGenerator {
        + list[str] CLASS_ORDER
        + @staticmethod create_scatterplot(df) Figure
        + @staticmethod create_weighted_scatterplot(df, window) Figure
        + @staticmethod create_bar_chart(df) Figure
    }

    class DataDisplay {
        - __init__(self, controller) None
        + update_display(self)
        - _rolling_average_slider_update(self, *_)
        + get_component(self)
    }

    class TextRender {
        + int CONTEXT_CHAR_COUNT
        - __init__(self, text) None
        + set_text(self, text)
        + get_clause_overlap(self) Optional[tuple[int, int]]
        - _repr_html_(self) str
        + set_clause_a_range(self, clause_a_range)
        + set_clause_b_range(self, clause_b_range)
        + update_linkage_word_ranges(self, linkage_words)
    }

    class TextDisplay {
        - __init__(self, controller) None
        + update_display(self)
        + get_component(self)
        + set_text(self, text)
    }

    DatabaseStateError --|> Exception

    DatabaseFieldError --|> DatabaseStateError

    DatabaseEntryError --|> DatabaseStateError

    DatabaseFileSizeError --|> DatabaseStateError

    Classification --|> `enum.Enum`

    Annotation *-- AnnotationController
    Annotation *-- AnnotationViewWrapper
    Annotation *-- AnnotationService
    Annotation *-- NotifierService
    Annotation *-- ImportExportService
    
    AnnotationController --> AnnotationService
    AnnotationController --> NotifierService
    AnnotationController --> ImportExportService
    AnnotationController o-- TextRange
    
    AnnotationService *-- DatastoreHandler
    AnnotationService *-- AnnotationDAO
    AnnotationService *-- llm.LLMProcess
    AnnotationService o-- SourceFileClauser
    AnnotationService o-- SequencingTool
    AnnotationService o-- ClauseSequence
    AnnotationService o-- Classification
    AnnotationService o-- SequenceTuple

    DatastoreHandler --> AnnotationDAO
    DatastoreHandler ..> ClauseSequence
    DatastoreHandler ..> Classification

    AnnotationDAO --* TextTXTRepository
    AnnotationDAO --* TextRangeCSVRepository
    AnnotationDAO --* SequenceCSVRepository
    AnnotationDAO ..> TextRange
    AnnotationDAO ..> ClauseSequence
    AnnotationDAO ..> Classification
    
    ClauseSequence o-- Classification
    ClauseSequence o-- TextRange

    TextRangeCSVRepository ..> DatabaseFieldError
    TextRangeCSVRepository ..> DatabaseEntryError

    SequenceCSVRepository ..> DatabaseFieldError
    SequenceCSVRepository ..> DatabaseEntryError

    TextTXTRepository ..> DatabaseFileSizeError

    AnnotationViewWrapper --> AnnotationController
    AnnotationViewWrapper *-- LoadingIndicator
    AnnotationViewWrapper *-- SourceLoader
    AnnotationViewWrapper *-- TextDisplay
    AnnotationViewWrapper *-- DataDisplay
    AnnotationViewWrapper *-- Controls
    
    LoadingIndicator --> AnnotationController

    SourceLoader --> AnnotationController
    SourceLoader *-- UnprocessedModeLoader
    SourceLoader *-- PreprocessedModeLoader

    PreprocessedModeLoader --> AnnotationController
    PreprocessedModeLoader *-- FileUploadWidget

    UnprocessedModeLoader --> AnnotationController
    UnprocessedModeLoader *-- FileUploadWidget
    UnprocessedModeLoader *-- ExportControls

    ExportControls --> AnnotationController
```
