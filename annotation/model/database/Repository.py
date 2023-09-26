from abc import ABC, abstractmethod


class Repository(ABC):

    @abstractmethod
    def read_all(self) -> list:
        raise NotImplementedError()

    @abstractmethod
    def read_by_id(self):
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
