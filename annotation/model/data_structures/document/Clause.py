from annotation.model.data_structures.classification.Classification import Classification


class Clause:
    """
    Represents a sub-string of a paragraph.
    This object contains a start index and end index of the substring relative to the start of the paragraph
    """

    def __init__(self, start: int, end: int):
        """
        Parameters
        ----------
        start: int - the start index of the clause relative to the paragraph, beginning at 0
        end: int - the end index of the clause relative to the paragraph
        """
        self.start: int = int(start)
        self.end: int = int(end)

    def __eq__(self, other) -> bool:
        if type(other) is not Clause:
            return False
        return (self.start == other.start) and (self.end == other.end)

    def get_start(self) -> int:
        return self.start

    def get_end(self) -> int:
        return self.end

    def get_range(self) -> tuple[int, int]:
        return self.start, self.end


class ClauseSequence:
    def __init__(self, first_clause: Clause, second_clause: Clause):
        self.first_clause: Clause = first_clause
        self.second_clause: Clause = second_clause
        self.classification_cont: set[Classification] = set()

    def get_clause_ranges(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return tuple(self.first_clause.get_range()), tuple(self.second_clause.get_range())

    def get_classifications(self) -> set[Classification]:
        return self.classification_cont.copy()

    def add_classification(self, classification: Classification):
        self.classification_cont.add(classification)

    def remove_classification(self, classification: Classification):
        self.classification_cont.remove(classification)
