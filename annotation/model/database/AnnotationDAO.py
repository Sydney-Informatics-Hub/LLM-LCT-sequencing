from pathlib import Path
from typing import Optional

import pandas as pd
from numpy import ndarray

from annotation.model.data_structures import TextRange, ClauseSequence
from annotation.model.data_structures.Classification import Classification
from annotation.model.database.repositories import TextTXTRepository, TextRangeCSVRepository, SequenceCSVRepository


class AnnotationDAO:
    def __init__(self, text_database_fn: Path, clause_database_fn: Path, sequence_database_fn: Path):
        self.text_repository: TextTXTRepository = TextTXTRepository(text_database_fn)
        self.clause_repository: TextRangeCSVRepository = TextRangeCSVRepository(clause_database_fn)
        self.sequence_repository: SequenceCSVRepository = SequenceCSVRepository(sequence_database_fn)

    @staticmethod
    def _split_to_int_list(sequence_data) -> list[int]:
        if pd.isna(sequence_data):
            return []
        sequence_data = str(sequence_data)
        if len(sequence_data) == 0:
            return []

        delimiter: str = SequenceCSVRepository.CLASS_LS_DELIMITER
        return [int(x) for x in sequence_data.split(delimiter)]

    @staticmethod
    def _join_str_from_int_list(int_list: list[int]) -> str:
        delimiter: str = SequenceCSVRepository.CLASS_LS_DELIMITER
        return delimiter.join([str(x) for x in int_list])

    def write_text_file(self, text: str):
        self.text_repository.write_file(text)

    def get_text(self) -> str:
        return self.text_repository.read_all()

    def create_clause(self, start: int, end: int) -> int:
        return self.clause_repository.create(start, end)

    def get_all_clauses(self) -> list[TextRange]:
        clause_data: ndarray = self.clause_repository.read_all()
        clauses: list[TextRange] = [TextRange(data[1], data[2], range_id=data[0]) for data in clause_data]

        return clauses

    def get_all_clause_text(self) -> dict[int, str]:
        text: str = self.get_text()
        clauses: list[TextRange] = self.get_all_clauses()

        clause_str_dict: dict[int, str] = {}
        for clause in clauses:
            clause_text = text[clause.get_start():clause.get_end()]
            clause_str_dict[clause.range_id] = clause_text

        return clause_str_dict

    def get_sequence_count(self) -> int:
        sequence_data: ndarray = self.sequence_repository.read_all()
        return sequence_data.shape[0]

    def _read_sequence_from_sequence_data(self, sequence_data: tuple[int]) -> ClauseSequence:
        sequence_id: int = sequence_data[0]
        clause_a_id: int = sequence_data[1]
        clause_b_id: int = sequence_data[2]
        linkage_words: str | float = sequence_data[3]
        class_predict_ids: list[int] = AnnotationDAO._split_to_int_list(sequence_data[4])
        class_correct_ids: list[int] = AnnotationDAO._split_to_int_list(sequence_data[5])
        reasoning: str = sequence_data[6]

        clause_a_data: tuple = self.clause_repository.read_by_id(clause_a_id)
        if len(clause_a_data) == 0:
            raise ValueError(f"Clause database does not contain a clause with id {clause_a_id}")
        clause_b_data: tuple = self.clause_repository.read_by_id(clause_b_id)
        if len(clause_b_data) == 0:
            raise ValueError(f"Clause database does not contain a clause with id {clause_b_id}")

        clause_a: TextRange = TextRange(clause_a_data[1], clause_a_data[2], range_id=clause_a_id)
        clause_b: TextRange = TextRange(clause_b_data[1], clause_b_data[2], range_id=clause_b_id)

        linkage_words_list: list[str] = []
        if isinstance(linkage_words, str) and (len(linkage_words) > 0):
            linkage_words_list = linkage_words.split(SequenceCSVRepository.LINKAGE_LS_DELIMITER)

        predicted_classes: Optional[list[Classification]] = []
        for class_int in class_predict_ids:
            try:
                predicted_classes.append(Classification(class_int))
            except ValueError:
                continue
        if len(predicted_classes) == 0:
            predicted_classes = None

        corrected_classes: Optional[list[Classification]] = []
        for class_int in class_correct_ids:
            try:
                corrected_classes.append(Classification(class_int))
            except ValueError:
                continue
        if len(corrected_classes) == 0:
            corrected_classes = None

        return ClauseSequence(sequence_id, clause_a, clause_b, linkage_words_list,
                              predicted_classes, corrected_classes, reasoning)

    def get_sequence_by_id(self, sequence_id: int) -> Optional[ClauseSequence]:
        sequence_data: tuple = self.sequence_repository.read_by_id(sequence_id)
        if len(sequence_data) == 0:
            return None

        return self._read_sequence_from_sequence_data(sequence_data)

    def get_all_sequences(self) -> list[ClauseSequence]:
        sequence_data: ndarray = self.sequence_repository.read_all()
        sequence_map: dict[int, ClauseSequence] = {}

        for data in sequence_data:
            sequence = self._read_sequence_from_sequence_data(data)
            sequence_map[sequence.get_id()] = sequence

        return list(sequence_map.values())

    def update_sequence(self, sequence_id: int, linkage_words: str, predicted_classes: str,
                        corrected_classes: str, reasoning: str) -> bool:
        return self.sequence_repository.update(sequence_id, linkage_words, predicted_classes,
                                               corrected_classes, reasoning)

    def update_sequence_classifications(self, sequence_id: int, correct_classes: list[int]):
        correct_classes_str: str = AnnotationDAO._join_str_from_int_list(correct_classes)
        self.sequence_repository.update(sequence_id, corrected_classes=correct_classes_str)

    def create_sequence(self, clause_a_id: int, clause_b_id: int, linkage_words: str = "",
                        predicted_classes: str = "0", correct_classes: str = "", reasoning: str = "") -> int:
        return self.sequence_repository.create(clause_a_id, clause_b_id, linkage_words,
                                               predicted_classes, correct_classes, reasoning)

    def delete_sequence(self, sequence_id: int):
        self.sequence_repository.delete(sequence_id)

    def clear_all_data_stores(self):
        self.text_repository.clear_database()
        self.sequence_repository.clear_database()
        self.clause_repository.clear_database()
