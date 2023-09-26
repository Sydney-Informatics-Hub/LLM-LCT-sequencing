from annotation.model.data_structures.classification.Classification import ClassificationContainer, Classification


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
        self.start: int = start
        self.end: int = end

    def __eq__(self, other) -> bool:
        if type(other) is not Clause:
            return False
        return (self.start == other.start) and (self.end == other.end)

    def get_start(self) -> int:
        return self.start

    def get_end(self) -> int:
        return self.end


class ClauseSequence:
    def __init__(self, first_clause: Clause, second_clause: Clause):
        self.first_clause: Clause = first_clause
        self.second_clause: Clause = second_clause
        self.classification_cont: ClassificationContainer = ClassificationContainer()

    def get_classifications(self) -> set[Classification]:
        return self.classification_cont.get_classifications()

    def add_classification(self, classification: Classification):
        self.classification_cont.add_classification(classification)

    def remove_classification(self, classification: Classification):
        self.classification_cont.remove_classification(classification)
