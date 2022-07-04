from file import File


class Letter:
    def __init__(self):
        self.letter_text = ''
        self.boundary = 'qwerty'

    def set_header(self, login: str, to: str, subject: str) -> None:
        self.letter_text += f'From: {login}\nTo: {to}\nSubject: {subject}'
        self.letter_text += f'\nContent-Type: multipart/mixed; '\
                            f'boundary={self.boundary}'

    def set_content(self, file: File, is_final: bool) -> None:
        self.letter_text += f'\n\n--{self.boundary}'
        self.letter_text += '\nMime-Version: 1.0'
        self.letter_text += f'\nContent-Type: image/jpeg; ' \
                            f'name="=?UTF-8?B?{file.b64_name}?="'
        self.letter_text += f'\nContent-Disposition: attachment; ' \
                            f'filename="=?UTF-8?B?{file.b64_name}?="'
        self.letter_text += '\nContent-Transfer-Encoding: base64\n\n'
        self.letter_text += file.get_base64()
        self.letter_text += f'\n--{self.boundary}'
        if is_final:
            self.letter_text += '--'

    def get_letter(self) -> str:
        return f'{self.letter_text}\n.\n'
