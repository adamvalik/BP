# document_processor.py - DocumentProcessor module
# Author: Adam Valík <xvalik05@stud.fit.vut.cz>

import io
from chunk import Chunk
from collections import deque
from typing import List, Optional

import emoji
import nltk
from transformers import AutoTokenizer
from unstructured.cleaners.core import clean
from unstructured.partition.text import partition_text

from utils import color_print

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class DocumentProcessor():
    # chunking based on titles and number of tokens, respecting the token limit of the embedding model
    MAX_TOKENS = 384 - 10 # limit with safety margin
    
    def __init__(self, filename: str, file: Optional[bytes] = None, file_id: Optional[str] = None):
        '''filename is full target file path or just a name of the file if bytes are specified'''
        self.filename = filename
        self.ext = self.filename.lower().split(".")[-1] if "." in self.filename else "txt"
        self.file = file
        self.file_id = file_id if file_id else filename
        self.elements = []
        self.chunks = []
        self.rights = ""
        
    def add_rights(self, rights: str):
        self.rights = rights
    
    def partition_elements(self):
        if self.ext not in ["txt", "pdf", "doc", "docx", "jpg", "png", "heic"]:
            color_print(message="Unsupported file extension", color="red", additional_text=f": {self.ext}, processing of {self.filename} is skipped.")
            return

        try:
            if self.file:
                # in-memory partition
                file_stream = io.BytesIO(self.file)
                
                if self.ext == "txt":
                    self.elements = partition_text(file=file_stream)

                elif self.ext == "pdf":
                    from unstructured.partition.pdf import partition_pdf
                    self.elements = partition_pdf(file=file_stream)
                elif self.ext == "doc":
                    from unstructured.partition.doc import partition_doc
                    self.elements = partition_doc(file=file_stream)
                elif self.ext == "docx":
                    from unstructured.partition.docx import partition_docx
                    self.elements = partition_docx(file=file_stream)
                elif self.ext == "jpg" or self.ext == "png" or self.ext == "heic":
                    from unstructured.partition.image import partition_image
                    self.elements = partition_image(file=file_stream)
                
            else:
                # disk-based partition
                if self.ext == "txt":
                    self.elements = partition_text(filename=self.filename)

                elif self.ext == "pdf":
                    from unstructured.partition.pdf import partition_pdf
                    self.elements = partition_pdf(filename=self.filename)
                elif self.ext == "doc":
                    from unstructured.partition.doc import partition_doc
                    self.elements = partition_doc(filename=self.filename)
                elif self.ext == "docx":
                    from unstructured.partition.docx import partition_docx
                    self.elements = partition_docx(filename=self.filename)
                elif self.ext == "jpg" or self.ext == "png" or self.ext == "heic":
                    from unstructured.partition.image import partition_image
                    self.elements = partition_image(filename=self.filename)

        except FileNotFoundError:
            color_print(message="File not found", color="red", additional_text=f": {self.filename}, processing is skipped.")
            return
        
        if not self.elements:
            color_print(message="No elements found", color="red", additional_text=f" in {self.filename}, processing is skipped.")
            return

    def clean_elements(
        self, 
        add_titles: bool = False, 
        remove_titles: bool = False,
        remove_list_of_titles: bool = False,
        remove_formulas: bool = False
    ):
        if not self.elements:
            return
        
        for i, el in enumerate(self.elements):            
            if add_titles:
                # add the titles if not partitioned well
                if el.category != "Title" and len(el.text) < 80 and not el.text.endswith((".", "\"")):
                    el.category = "Title"
            if remove_titles:
                # remove the titles if they are not needed
                if el.category == "Title" and el.text.endswith((":", ".", ">")):
                    el.category = "NarrativeText"
            if remove_list_of_titles:
                # title is followed by another title, categorize it as narrative text, it is likely a list of items
                if el.category == "Title" and i + 1 < len(self.elements) and self.elements[i + 1].category == "Title":
                    el.category = "NarrativeText"
                    j = i + 1
                    while i < len(self.elements) and self.elements[j].category == "Title":
                        self.elements[j].category = "NarrativeText"
                        j += 1
            if remove_formulas:
                # remove formulas as titles
                if el.category == "Title" and el.text.split("_")[0] == "formula":
                    el.category = "NarrativeText"

        el.text = emoji.replace_emoji(el.text, "") # remove emojis
        el.text = clean(el.text, extra_whitespace=True, dashes=True, bullets=True)        

        self.elements = [
            el for el in self.elements 
            if el.text.strip() and el.category not in ["Header", "Footer"]
        ]
        
    def chunk_elements(self):
        if not self.elements:
            return
        
        tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-mpnet-base-v2")
        
        curr_chunk_text = ""
        curr_token_count = 0
        title = ""
        chunk_id = 0
        last_sentence = ""
        last_sentence_token_count = 0
        chunk_element_indices = deque()
        
        # process filename and file directory (in disk-based partitioning, self.filename is the full path)
        file_directory = ""
        if "/" in self.filename:
            parts = self.filename.split("/")
            file_directory = "/".join(parts[:-1])
            self.filename = parts[-1]
           
        # helper function to calculate the page range 
        def get_page_range(start_idx, end_idx) -> str:
            pages = {
                self.elements[i].metadata.page_number
                for i in range(start_idx, end_idx)
                if self.elements[i].metadata.page_number is not None
            }
            if not pages:
                return ""
            pages = sorted(pages)
            return str(pages[0]) if len(pages) == 1 else f"{pages[0]}-{pages[-1]}"

        # helper function to add a chunk
        def append_chunk(start_idx, end_idx):
            nonlocal curr_chunk_text, curr_token_count, chunk_id, title
            page = get_page_range(start_idx, end_idx)
            self.chunks.append(Chunk(
                text=curr_chunk_text.strip(),
                chunk_id=f"{self.file_id}_{chunk_id}",
                file_id=self.file_id,
                filename=self.filename,
                file_directory=file_directory if file_directory else self.elements[0].metadata.file_directory,
                title=title,
                page=page,
                token_count=curr_token_count,
                rights=self.rights
            ))
            chunk_id += 1

        # process the text for each element
        for i, el in enumerate(self.elements):
            
            # split to sentences
            for sentence in nltk.tokenize.sent_tokenize(el.text):
                sentence_token_count = len(tokenizer.tokenize(sentence))
                
                # if adding another sentence exceeds the token limit (or it's a new title), close the current chunk
                if curr_token_count + sentence_token_count > DocumentProcessor.MAX_TOKENS or el.category == "Title":
                    if curr_chunk_text.strip():
                        end_idx = i
                        start_idx = chunk_element_indices[0] if chunk_element_indices else end_idx
                        append_chunk(start_idx, end_idx)
                        
                        # for non-title elements, start a new chunk with the overlap of the last sentence
                        if el.category != "Title":
                            curr_chunk_text = last_sentence + " "
                            curr_token_count = last_sentence_token_count
                            chunk_element_indices = deque([i - 1])
                        else:
                            curr_chunk_text = ""
                            curr_token_count = 0
                            chunk_element_indices.clear()
                        
                if el.category == "Title":
                    title = el.text  # update title

                # append the sentence to the current chunk
                curr_chunk_text += sentence + ("\n\n" if el.category == "Title" else " ")
                curr_token_count += sentence_token_count
                last_sentence = sentence
                last_sentence_token_count = sentence_token_count
                chunk_element_indices.append(i)
        
        if curr_chunk_text.strip():
            start_idx = chunk_element_indices[0] if chunk_element_indices else i
            end_idx = i
            append_chunk(start_idx, end_idx)
            
    def log(self, elements: bool = True, chunks: bool = True, output_file: Optional[str] = None):
        if not self.elements:
            return

        if output_file:
            with open(output_file, "a") as f:
                f.write(f"File: {self.filename}\n")
                
                if elements:
                    f.write(f"Partitioned {len(self.elements)} elements\n")
                    for el in self.elements:
                        f.write(f"Category: {el.category}\n")
                        f.write(f"Text: {el.text}\n")
                        f.write("-"*50 + "\n")
                    f.write(f"Partitioned {len(self.elements)} elements\n")
                
                if chunks:
                    f.write(f"Chunked {len(self.chunks)} chunks from {len(self.elements)} elements\n")
                    for chunk in self.chunks:
                        f.write(str(chunk))
                        f.write("\n" + "-"*50 + "\n")
                    f.write(f"Chunked {len(self.chunks)} chunks from {len(self.elements)} elements\n")
        else:
            color_print(f"File: {self.filename}", color="blue")
            
            if elements:
                color_print(f"Partitioned {len(self.elements)} elements")
                for el in self.elements:
                    print(f"Category: {el.category}")
                    print(f"Text: {el.text}")
                    print("-"*50)
                color_print(f"Partitioned {len(self.elements)} elements")
            
            if chunks:
                color_print(f"Chunked {len(self.chunks)} chunks from {len(self.elements)} elements")
                for chunk in self.chunks:
                    print(str(chunk))
                    print("-"*50)
                color_print(f"Chunked {len(self.chunks)} chunks from {len(self.elements)} elements")
                
    def process(self, verbose: bool = False) -> List[Chunk]:
        # processing pipeline
        self.partition_elements()
        self.clean_elements(remove_titles=True, remove_formulas=True, remove_list_of_titles=True)
        self.chunk_elements()

        if verbose: 
            self.log(elements=False, output_file="chunking.log")

        return self.chunks
