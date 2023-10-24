from abc import ABC, abstractmethod

from numpy import ndarray


class TextRangeRepository(ABC):
    @abstractmethod
    def read_all(self) -> ndarray:
        raise NotImplementedError()

    @abstractmethod
    def read_by_id(self, clause_id: int) -> tuple:
        raise NotImplementedError()

    @abstractmethod
    def create(self, clause) -> int:
        raise NotImplementedError()

    @abstractmethod
    def update(self, clause_id: int, start: int, end: int) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def delete(self) -> bool:
        raise NotImplementedError()
