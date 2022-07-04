class IMAPException(Exception):
    def __init__(self, message: str):
        self.message = f'IMAP exception {message}'

    def __str__(self) -> str:
        return self.message
