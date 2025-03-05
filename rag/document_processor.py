from unstructured.partition.text import partition_text
from unstructured.chunking.title import chunk_by_title
from unstructured.cleaners.core import clean
import emoji
import re
import io
from typing import List, Optional
from chunk import Chunk
from utils import color_print

class DocumentProcessor():
    # chunking parameters
    MAX_CHUNK_SIZE = 1500
    PREFFERED_CHUNK_SIZE = 1000
    OVERLAP = 50
    MIN_CHUNK_SIZE = 100
    # real maximum chunk size is MAX_CHUNK_SIZE + MIN_CHUNK_SIZE (due to merging small chunks)
    
    def __init__(self, filename: str, file: Optional[bytes] = None, file_id: Optional[str] = None):
        '''filename is full target file path or just a name of the file if bytes are specified'''
        self.filename = filename
        self.ext = self.filename.lower().split(".")[-1]
        self.file = file
        self.file_id = file_id if file_id else filename
        self.elements = []
        self.chunks = []
    
    def partition_elements(self):
        if self.ext not in ["txt"]:
            color_print(message="Unsupported file extension", color="red", additional_text=f": {self.ext}, processing of {self.filename} is skipped.")
            return

        try:
            if self.file:
                # --- IN-MEMORY PARTITION ---
                file_stream = io.BytesIO(self.file)
                
                if self.ext == "txt":
                    self.elements = partition_text(file=file_stream)
                # elif self.ext == "pdf":
                #     self.elements = partition_pdf(file=file_stream)
                
            else:
                # --- DISK-BASED PARTITION ---
                if self.ext == "txt":
                    self.elements = partition_text(filename=self.filename)
                # elif self.ext == "pdf":
                #     self.elements = partition_pdf(self.filename)

        except FileNotFoundError:
            color_print(message="File not found", color="red", additional_text=f": {self.filename}, processing is skipped.")
            return
        
        if not self.elements:
            color_print(message="No elements found", color="red", additional_text=f" in {self.filename}, processing is skipped.")
            return

    def clean_elements(self):
        if not self.elements:
            return

        # apply every possible cleaning method to the elements
        for el in self.elements:
            el.text = emoji.replace_emoji(el.text, "") # remove emojis
            # el.text = re.sub(r"---+", "", el.text)  # remove horizontal lines (e.g., ---)
            # el.text = re.sub(r"#+\s*", "", el.text)  # remove headers (e.g., ## Header)
            # el.text = re.sub(r"\*\*(.*?)\*\*", r"\1", el.text)  # remove bold (e.g., **bold** -> bold)
            # el.text = re.sub(r"\*(.*?)\*", r"\1", el.text)  # remove italics (e.g., *italic* -> italic)
            el.text = clean(el.text, extra_whitespace=True, dashes=True, bullets=True)
        
        self.elements = [
            el for el in self.elements 
            if el.text.strip() and el.category not in ["Header", "Footer"]
        ]

    def chunk_elements(self) -> List[Chunk]:
        if not self.elements:
            return

        # aim for 1000-1500 chars, use overlap (100 chars) when text-splitting
        raw_chunks = chunk_by_title(self.elements, max_characters=self.MAX_CHUNK_SIZE, new_after_n_chars=self.PREFFERED_CHUNK_SIZE, overlap=self.OVERLAP)
        
        curr_title = ""
        prev_chunk = None
        
        for i, chunk in enumerate(raw_chunks):
            chunk_text = chunk.text.strip()
            
            # merge with previous chunk if too small
            if prev_chunk and len(chunk_text) < (self.MIN_CHUNK_SIZE + self.OVERLAP):
                # remove overlap and add to previous chunk
                prev_chunk.text += " " + chunk_text[self.OVERLAP:]
                continue

            # extract metadata from original elements
            c = Chunk(
                chunk_id=f"{self.file_id}_{i}",
                file_id=self.file_id,
                text=chunk.text,
                filename=self.filename,
                file_directory=chunk.metadata.orig_elements[0].metadata.file_directory,
                title=curr_title,
            )

            for j, el in enumerate(chunk.metadata.orig_elements):
                # add title to metadata
                if (j == 0 and el.category == "Title") or (j != 0 and el.category == "Title" and not curr_title):
                    c.title = el.text
                    curr_title = el.text
                elif j != 0 and el.category == "Title":
                    c.title += f", {el.text}"
                    curr_title = el.text

                # add page number to metadata
                if not c.page and el.metadata.page_number:
                    c.page = str(el.metadata.page_number)
                elif c.page and el.metadata.page_number:
                    c.page += f", {str(el.metadata.page_number)}"

            self.chunks.append(c)
            prev_chunk = c # save for potential metging with small chunk
            
    def log(self):
        if not self.elements:
            return

        color_print(f"File: {self.filename}", color="blue")

        color_print(f"Partitioned {len(self.elements)} elements")
        for el in self.elements:
            print(f"Category: {el.category}")
            print(f"Text: {el.text}")
            print("-------------------------------")
            
        color_print(f"Chunked {len(self.chunks)} chunks from {len(self.elements)} elements")
        for chunk in self.chunks:
            print(chunk)
            print("-------------------------------")

    def process(self, verbose: bool = False) -> List[Chunk]:
        # processing pipeline
        self.partition_elements()
        self.clean_elements()
        self.chunk_elements()

        if verbose: 
            self.log()

        return self.chunks
