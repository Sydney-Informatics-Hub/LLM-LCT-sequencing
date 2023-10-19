from typing import Callable, Optional

from annotation.model import AnnotationService

# Type alias for complex tuples
ClauseTuple = tuple[int, int]
ClauseSequenceTuple = tuple[ClauseTuple, ClauseTuple]


class AnnotationController:
    def __init__(self, service: AnnotationService):
        self.annotation_service: AnnotationService = service
        self.curr_sequence_id: int = 1

        self._update_display_callables: list[Callable] = []

    def add_update_text_display_callable(self, update_text_display_callable: Optional[Callable]):
        if (type(update_text_display_callable) is not None) and (not callable(update_text_display_callable)):
            raise TypeError("update_text_display_callable must be either None or a callable")
        self._update_display_callables.append(update_text_display_callable)

    def update_displays(self):
        for update_callable in self._update_display_callables:
            update_callable()

    # Data access methods

    def get_text(self) -> str:
        return self.annotation_service.get_text()

    def get_clauses(self) -> list[tuple[int, str]]:
        return self.annotation_service.get_clauses()

    def get_curr_sequence(self) -> ClauseSequenceTuple:
        return self.annotation_service.get_sequence_clause_ranges(self.curr_sequence_id)

    def get_all_classifications(self) -> list[str]:
        return self.annotation_service.get_all_sequence_classifications()

    def get_predicted_classification(self) -> str:
        return self.annotation_service.get_sequence_predict_class(self.curr_sequence_id)

    def get_correct_classification(self) -> str:
        return self.annotation_service.get_sequence_correct_class(self.curr_sequence_id)

    # Data control methods

    def next_sequence(self):
        num_sequences: int = self.annotation_service.get_sequence_count()
        if self.curr_sequence_id < (num_sequences - 1):
            self.curr_sequence_id += 1
        self.update_displays()

    def prev_sequence(self):
        if self.curr_sequence_id > 1:
            self.curr_sequence_id -= 1
        self.update_displays()

    def set_correct_classification(self, classification: str):
        self.annotation_service.set_sequence_correct_class(self.curr_sequence_id, classification)

    def add_sequence(self, clause_a_id: int, clause_b_id: int) -> int:
        new_id: int = self.annotation_service.create_sequence(clause_a_id, clause_b_id)
        return new_id

    def delete_curr_sequence(self):
        self.annotation_service.delete_sequence(self.curr_sequence_id)

        # The sequence index must be decreased if the deleted sequence was not the first sequence
        if self.curr_sequence_id > 0:
            self.curr_sequence_id -= 1

        # The display must be updated to reflect the deletion
        self.update_displays()
