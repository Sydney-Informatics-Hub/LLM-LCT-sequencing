from abc import ABC, abstractmethod

from numpy import ndarray


class TextRangeRepository(ABC):
    @abstractmethod
    def read_all(self) -> ndarray:
        raise NotImplementedError()

    @abstractmethod
    def read_by_id(self, range_id: int) -> tuple:
        raise NotImplementedError()

    @abstractmethod
    def create(self, start: int, end: int) -> int:
        raise NotImplementedError()

    @abstractmethod
    def update(self, range_id: int, start: int, end: int) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def delete(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def clear_database(self):
        raise NotImplementedError()
