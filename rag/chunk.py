from dataclasses import dataclass, field
from typing import List

@dataclass
class Chunk:
    chunkid: str = ""
    text: str = ""
    filename: str = ""
    file_directory: str = ""
    title: str = ""
    page_number: int = 0
    rights: str = ""

    def __str__(self):
            parts = [
                f"Chunk ID: {self.chunkid}" if self.chunkid else "",
                f"Text: {self.text}" if self.text else "",
                f"Filename: {self.filename}" if self.filename else "",
                f"File Directory: {self.file_directory}" if self.file_directory else "",
                f"Title: {self.title}" if self.title else "",
                f"Page Number: {self.page_number}" if self.page_number > 0 else "",
                f"Rights: {self.rights}" if self.rights else ""
            ]
            return "\n".join(filter(bool, parts))
