from typing import Callable, Optional

from annotation.model import AnnotationService

# Type alias for complex tuples - only applies for this document
ClauseTuple = tuple[int, int]
ClauseSequenceTuple = tuple[ClauseTuple, ClauseTuple]
ClassificationTuple = tuple[str, ...]


class AnnotationController:
    def __init__(self, service: AnnotationService):
        self.annotation_service = service
        self.curr_paragraph_id: int = 0
        self.curr_sequence_id: int = 0

        self._update_text_display_callable: Optional[Callable] = None

    def set_update_text_display_callable(self, update_text_display_callable: Optional[Callable]):
        if (type(update_text_display_callable) is not None) and (not callable(update_text_display_callable)):
            raise TypeError("update_text_display_callable must be either None or a callable")
        self._update_text_display_callable = update_text_display_callable

    def update_text_display(self):
        if self._update_text_display_callable is not None:
            self._update_text_display_callable()

    # Data access methods

    def get_next_paragraph_text(self) -> str:
        return ""

    def get_prev_paragraph_text(self) -> str:
        return ""

    def get_curr_paragraph_text(self) -> str:
        return ""

    def get_curr_sequence(self) -> ClauseSequenceTuple:
        return (0, 1), (2, 3)

    def get_curr_set_classifications(self) -> ClassificationTuple:
        return "INT", "SUB"

    def get_curr_unset_classifications(self) -> ClassificationTuple:
        return "SEQ", "REI", "REP", "COH", "INC"

    # Data control methods

    def next_paragraph(self):
        self.update_text_display()

    def prev_paragraph(self):
        self.update_text_display()

    def next_clause_sequence(self):
        self.update_text_display()

    def prev_clause_sequence(self):
        self.update_text_display()

    def set_curr_classifications(self, classifications: ClassificationTuple):
        pass

    def add_clause_sequence(self, clause_a_range: ClauseTuple, clause_b_range: ClauseTuple):
        pass

    def delete_curr_clause_sequence(self):
        pass
