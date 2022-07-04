class WrongPortException(Exception):
    def __init__(self, message: str):
        self.message = f'Wrong port to imap: {message}'

    def __str__(self) -> str:
        return self.message
