from dataclasses import dataclass, field
from typing import List

@dataclass
class Chunk:
    chunk_id: str = ""
    file_id: str = ""
    text: str = ""
    filename: str = ""
    file_directory: str = ""
    title: str = ""
    page: str = ""
    rights: str = ""
    score: float = 0.0
    explain_score: str = ""

    def __str__(self):
        parts = [
            f"Chunk ID: {self.chunk_id}" if self.chunk_id else "",
            f"File ID: {self.file_id}" if self.file_id else "",
            f"Filename: {self.filename}" if self.filename else "",
            f"File Directory: {self.file_directory}" if self.file_directory else "",
            f"Title: {self.title}" if self.title else "",
            f"Page: {self.page}" if self.page else "",
            f"Rights: {self.rights}" if self.rights else ""
            f"Text: {self.text}" if self.text else "",
        ]
        return "\n".join(filter(bool, parts))
    
    # for inserting (makes dictionary without score and explain_score)
    def to_dict(self):
        return {k: v for k, v in vars(self).items() if k not in {"score", "explain_score"}}
