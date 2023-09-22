from enum import Enum


class Classification(Enum):
    CLASS = 1
    COMP = 2
    CAUS = 3
    CORR = 4
    DISP = 5
    DRAM = 6
    PTION = 7
    POSIT = 8


class ClassificationContainer:
    def __init__(self):
        self.classifications: set[Classification] = set()

    def get_classifications(self) -> set[Classification]:
        return self.classifications.copy()

    def add_classification(self, classification: Classification):
        self.classifications.add(classification)

    def remove_classification(self, classification: Classification):
        self.classifications.remove(classification)
