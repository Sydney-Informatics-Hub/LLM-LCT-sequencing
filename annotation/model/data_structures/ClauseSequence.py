from typing import Optional

from annotation.model.data_structures import TextRange, Classification, TextRangeTuple

SequenceTuple = tuple[TextRangeTuple, TextRangeTuple]


class ClauseSequence:
    def __init__(self, sequence_id: int, first_clause: TextRange,
                 second_clause: TextRange, linkage_words: list[str],
                 predicted_class: Optional[list[Classification]] = None,
                 correct_class: Optional[list[Classification]] = None,
                 reasoning: str = ''):
        self.sequence_id: int = sequence_id
        self.first_clause: TextRange = first_clause
        self.second_clause: TextRange = second_clause
        self.linkage_words: list[str] = linkage_words
        self.reasoning: str = reasoning
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

    def get_first_clause(self) -> TextRange:
        return self.first_clause

    def get_second_clause(self) -> TextRange:
        return self.second_clause

    def get_linkage_words(self) -> list[str]:
        return self.linkage_words

    def get_clause_ranges(self) -> SequenceTuple:
        return (tuple(self.first_clause.get_range()),
                tuple(self.second_clause.get_range()))

    def get_reasoning(self) -> str:
        return self.reasoning

    def get_predicted_classes(self) -> Optional[list[Classification]]:
        return self.predicted_classes

    def set_predicted_classes(self, predicted_classes: Optional[list[Classification]]):
        self.predicted_classes = predicted_classes

    def get_correct_classes(self) -> Optional[list[Classification]]:
        return self.correct_classes

    def set_correct_classes(self, correct_classes: Optional[list[Classification]]):
        self.correct_classes = correct_classes
