from annotation.model.database.ClauseSequenceRepository import ClauseSequenceRepository


class ClauseSequenceCSVRepository(ClauseSequenceRepository):
    def __init__(self, database_csv_filename: str):
        self._database_filename: str = database_csv_filename

    def read_all(self) -> list:
        pass

    def read_by_id(self, paragraph_id: int, clause_id: int):
        pass

    def create(self) -> bool:
        pass

    def update(self) -> bool:
        pass

    def delete(self) -> bool:
        pass
