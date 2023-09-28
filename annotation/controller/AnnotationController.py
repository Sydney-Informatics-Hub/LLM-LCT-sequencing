from typing import Callable, Optional

from annotation.model import AnnotationService

# Type alias for complex tuples - only applies for this document
ClauseTuple = tuple[int, int]
ClauseSequenceTuple = tuple[ClauseTuple, ClauseTuple]
ClassificationTuple = tuple[str, ...]


class AnnotationController:
    def __init__(self, service: AnnotationService):
        self.annotation_service: AnnotationService = service
        self.curr_paragraph_id: int = 1
        self.curr_sequence_id: int = 0

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
        return (0, 1), (2, 3)

    def get_curr_set_classifications(self) -> ClassificationTuple:
        return "INT", "SUB"

    def get_curr_unset_classifications(self) -> ClassificationTuple:
        return "SEQ", "REI", "REP", "COH", "INC"

    # Data control methods

    def next_paragraph(self):
        if self.curr_paragraph_id < self.annotation_service.get_paragraph_count():
            self.curr_paragraph_id += 1

        self.update_displays()

    def prev_paragraph(self):
        if self.curr_paragraph_id > 1:
            self.curr_paragraph_id -= 1

        self.update_displays()

    def next_sequence(self):
        self.update_displays()

    def prev_sequence(self):
        self.update_displays()

    def set_curr_classifications(self, classifications: ClassificationTuple):
        pass

    def add_sequence(self, clause_a_range: ClauseTuple, clause_b_range: ClauseTuple):
        pass

    def delete_curr_sequence(self):
        pass
