from typing import Optional

from annotation.model.data_structures.classification.Classification import Classification


class Clause:
    """
    Represents a sub-string of a paragraph.
    This object contains a start index and end index of the substring relative to the start of the paragraph
    """

    def __init__(self, start: int, end: int, clause_id: Optional[int] = None):
        """
        Parameters
        ----------
        start: int - the start index of the clause relative to the paragraph, beginning at 0
        end: int - the end index of the clause relative to the paragraph
        clause_id: int - The database integer id of the clause. Can be None
        """
        self.start: int = int(start)
        self.end: int = int(end)
        self.clause_id: Optional[int] = clause_id

    def __eq__(self, other) -> bool:
        if type(other) is not Clause:
            return False
        return (self.start == other.start) and (self.end == other.end)

    def __hash__(self):
        return hash((self.start, self.end))

    def get_id(self) -> Optional[int]:
        return self.clause_id

    def get_start(self) -> int:
        return self.start

    def get_end(self) -> int:
        return self.end

    def get_range(self) -> tuple[int, int]:
        return self.start, self.end


class ClauseSequence:
    def __init__(self, sequence_id: int, first_clause: Clause, second_clause: Clause,
                 predicted_class: Optional[list[Classification]] = None,
                 correct_class: Optional[list[Classification]] = None):
        self.sequence_id: int = sequence_id
        self.first_clause: Clause = first_clause
        self.second_clause: Clause = second_clause
        self.predicted_classes: Optional[list[Classification]] = predicted_class
        self.correct_classes: Optional[list[Classification]] = correct_class

    def __eq__(self, other) -> bool:
        if type(other) is not ClauseSequence:
            return False
        return ((self.sequence_id == other.sequence_id) and
                (self.first_clause == other.first_clause) and
                (self.second_clause == other.second_clause))

    def __hash__(self):
        return hash((self.sequence_id, self.first_clause, self.second_clause))

    def get_id(self) -> int:
        return self.sequence_id

    def get_clause_ranges(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return tuple(self.first_clause.get_range()), tuple(self.second_clause.get_range())

    def get_predicted_classes(self) -> Optional[list[Classification]]:
        return self.predicted_classes

    def set_predicted_classes(self, predicted_classes: Optional[list[Classification]]):
        self.predicted_classes = predicted_classes

    def get_correct_classes(self) -> Optional[list[Classification]]:
        return self.correct_classes

    def set_correct_classes(self, correct_classes: Optional[list[Classification]]):
        self.correct_classes = correct_classes
