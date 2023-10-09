from typing import Callable, Optional

from annotation.model import AnnotationService

# Type alias for complex tuples
ClauseTuple = tuple[int, int]
ClauseSequenceTuple = tuple[ClauseTuple, ClauseTuple]


class AnnotationController:
    def __init__(self, service: AnnotationService):
        self.annotation_service: AnnotationService = service
        self.curr_paragraph_id: int = 1
        self.curr_sequence_idx: int = 0

        self._update_display_callables: list[Callable] = []

    def add_update_text_display_callable(self, update_text_display_callable: Optional[Callable]):
        if (type(update_text_display_callable) is not None) and (not callable(update_text_display_callable)):
            raise TypeError("update_text_display_callable must be either None or a callable")
        self._update_display_callables.append(update_text_display_callable)

    def update_displays(self):
        for update_callable in self._update_display_callables:
            update_callable()

    # Data access methods

    def get_current_paragraph_id(self) -> int:
        return self.curr_paragraph_id

    def get_next_paragraph_text(self) -> str:
        return self.annotation_service.get_paragraph_text(self.curr_paragraph_id + 1)

    def get_prev_paragraph_text(self) -> str:
        return self.annotation_service.get_paragraph_text(self.curr_paragraph_id - 1)

    def get_curr_paragraph_text(self) -> str:
        return self.annotation_service.get_paragraph_text(self.curr_paragraph_id)

    def get_curr_sequence(self) -> ClauseSequenceTuple:
        return self.annotation_service.get_sequence_clause_ranges(self.curr_paragraph_id, self.curr_sequence_idx)

    def get_all_classifications(self) -> list[str]:
        return self.annotation_service.get_all_sequence_classifications()

    def get_predicted_classification(self) -> str:
        return self.annotation_service.get_sequence_predict_class(self.curr_paragraph_id, self.curr_sequence_idx)

    def get_correct_classification(self) -> str:
        return self.annotation_service.get_sequence_correct_class(self.curr_paragraph_id, self.curr_sequence_idx)

    # Data control methods

    def set_curr_paragraph(self, paragraph_id: int):
        if paragraph_id >= self.annotation_service.get_paragraph_count():
            self.curr_paragraph_id = self.annotation_service.get_paragraph_count()
            self.curr_sequence_idx = 0
        elif paragraph_id < 1:
            self.curr_paragraph_id = 1
            self.curr_sequence_idx = 0
        else:
            self.curr_paragraph_id = paragraph_id

        self.update_displays()

    def next_paragraph(self):
        if self.curr_paragraph_id < self.annotation_service.get_paragraph_count():
            self.curr_paragraph_id += 1
        self.curr_sequence_idx = 0

        self.update_displays()

    def prev_paragraph(self):
        if self.curr_paragraph_id > 1:
            self.curr_paragraph_id -= 1
        self.curr_sequence_idx = 0

        self.update_displays()

    def next_sequence(self):
        num_sequences: int = self.annotation_service.get_paragraph_sequence_count(self.curr_paragraph_id)
        if self.curr_sequence_idx < (num_sequences - 1):
            self.curr_sequence_idx += 1
        self.update_displays()

    def prev_sequence(self):
        if self.curr_sequence_idx > 0:
            self.curr_sequence_idx -= 1
        self.update_displays()

    def set_correct_classification(self, classification: str):
        self.annotation_service.set_sequence_correct_class(self.curr_paragraph_id, self.curr_sequence_idx,
                                                           classification)

    def add_sequence(self, clause_a_range: ClauseTuple, clause_b_range: ClauseTuple):
        pass

    def delete_curr_sequence(self):
        self.annotation_service.delete_sequence(self.curr_paragraph_id, self.curr_sequence_idx)

        # The sequence index must be decreased if the deleted sequence was not the first sequence
        if self.curr_sequence_idx > 0:
            self.curr_sequence_idx -= 1

        # The display must be updated to reflect the deletion
        self.update_displays()
