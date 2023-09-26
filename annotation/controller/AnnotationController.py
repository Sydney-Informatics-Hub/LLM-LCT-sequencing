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

    # Data access methods

    def get_next_paragraph_text(self) -> str:
        return ""

    def get_prev_paragraph_text(self) -> str:
        return ""

    def get_curr_paragraph_text(self) -> str:
        return ""

    def get_prev_sequence(self) -> ClauseSequenceTuple:
        return (0, 1), (2, 3)

    def get_next_sequence(self) -> ClauseSequenceTuple:
        return (0, 1), (2, 3)

    def get_curr_sequence(self) -> ClauseSequenceTuple:
        return (0, 1), (2, 3)

    def get_curr_set_classifications(self) -> ClassificationTuple:
        return "INT", "SUB"

    def get_curr_unset_classifications(self) -> ClassificationTuple:
        return "SEQ", "REI", "REP", "COH", "INC"

    # Data control methods

    def next_paragraph(self):
        pass

    def prev_paragraph(self):
        pass

    def next_clause_sequence(self):
        pass

    def prev_clause_sequence(self):
        pass

    def set_curr_classifications(self, classifications: ClassificationTuple):
        pass

    def add_clause_sequence(self, clause_a_range: ClauseTuple, clause_b_range: ClauseTuple):
        pass

    def delete_curr_clause_sequence(self):
        pass
