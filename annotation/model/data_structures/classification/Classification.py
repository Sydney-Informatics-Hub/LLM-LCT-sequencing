from enum import Enum


class Classification(Enum):
    INT = 1
    SUB = 2
    CON = 3
    SEQ = 4
    REI = 5
    REP = 6
    COH = 7
    INC = 8


class ClassificationContainer:
    def __init__(self):
        self.classifications: set[Classification] = set()

    def get_classifications(self) -> set[Classification]:
        return self.classifications.copy()

    def add_classification(self, classification: Classification):
        self.classifications.add(classification)

    def remove_classification(self, classification: Classification):
        self.classifications.remove(classification)
