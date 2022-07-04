class SMTPException(Exception):
    def __init__(self, message: str):
        self.message = f'SMTP exception {message}'

    def __str__(self) -> str:
        return self.message