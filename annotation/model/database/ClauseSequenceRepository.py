from abc import ABC, abstractmethod

from numpy import ndarray


class ClauseSequenceRepository(ABC):

    @abstractmethod
    def read_all(self) -> ndarray:
        raise NotImplementedError()

    @abstractmethod
    def read_all_by_paragraph(self, paragraph_id: int):
        raise NotImplementedError()

    @abstractmethod
    def create(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def update(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def delete(self) -> bool:
        raise NotImplementedError()
