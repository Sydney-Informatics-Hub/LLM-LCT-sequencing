class DatabaseStateError(Exception):
    pass


class DatabaseFieldError(DatabaseStateError):
    pass


class DatabaseEntryError(DatabaseStateError):
    pass
