from pathlib import Path
import base64


class File:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.b64_name = base64.b64encode(file_path.name.encode('utf-8'))\
            .decode('utf-8')

    def get_base64(self):
        with self.file_path.open('rb') as file:
            return base64.b64encode(file.read()).decode('utf-8')