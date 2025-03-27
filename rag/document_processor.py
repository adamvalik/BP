from unstructured.partition.text import partition_text
from unstructured.chunking.title import chunk_by_title
from unstructured.cleaners.core import clean
import emoji
import io
from typing import List, Optional
from chunk import Chunk
from utils import color_print
from transformers import AutoTokenizer

import nltk

# try:
#     nltk.data.find('tokenizers/punkt')
# except LookupError:
#     nltk.download('punkt')

class DocumentProcessor():
    
    def __init__(self, filename: str, file: Optional[bytes] = None, file_id: Optional[str] = None):
        '''filename is full target file path or just a name of the file if bytes are specified'''
        self.filename = filename
        self.ext = self.filename.lower().split(".")[-1] if "." in self.filename else "txt"
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

    def clean_elements(self, add_titles: bool = False, remove_titles: bool = False, remove_list_of_titles: bool = False):
        if not self.elements:
            return
        
        for i, el in enumerate(self.elements):
            el.text = emoji.replace_emoji(el.text, "") # remove emojis
            el.text = clean(el.text, extra_whitespace=True, dashes=True, bullets=True)
            
            if add_titles:
                # add the titles if not partitioned well
                if el.category != "Title" and len(el.text) < 80 and not el.text.endswith((".", "\"")):
                    el.category = "Title"
            if remove_titles:
                # remove the titles if they are not needed
                if el.category == "Title" and len(el.text) < 80 and el.text.endswith((":")):
                    el.category = "NarrativeText"
            if remove_list_of_titles:
                # title is followed by another title, categorize it as narrative text, it is likely a list of items
                if el.category == "Title" and i + 1 < len(self.elements) and self.elements[i + 1].category == "Title":
                    el.category = "NarrativeText"
                    j = i + 1
                    while i < len(self.elements) and self.elements[j].category == "Title":
                        self.elements[j].category = "NarrativeText"
                        j += 1
        
        self.elements = [
            el for el in self.elements 
            if el.text.strip() and el.category not in ["Header", "Footer"]
        ]
            
    def chunk_elements(self) -> List[Chunk]:
        if not self.elements:
            return
        
        # chunking based on titles and number of tokens
        # respecting the token limit of the embedding model
        max_tokens = 384 - 10 # limit with safety margin
        tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-mpnet-base-v2")
        
        curr_chunk_text = ""
        curr_token_count = 0
        title = ""
        chunk_id = 0
        last_sentence = ""
        last_sentence_token_count = 0
        
        # process filename and file directory (in disk-based partitioning, self.filename is the full path)
        file_directory = ""
        if "/" in self.filename:
            parts = self.filename.split("/")
            file_directory = "/".join(parts[:-1])
            self.filename = parts[-1]
            
        # helper function to add a chunk
        def append_chunk():
            nonlocal curr_chunk_text, curr_token_count, chunk_id
            self.chunks.append(Chunk(
                text=curr_chunk_text.strip(),
                chunk_id=f"{self.file_id}_{chunk_id}",
                file_id=self.file_id,
                filename=self.filename,
                file_directory=file_directory if file_directory else self.elements[0].metadata.file_directory,
                title=title,
                token_count=curr_token_count
            ))
            chunk_id += 1
    
        # process the text for each element
        for el in self.elements:
                    
            # split to sentences
            sentences = nltk.tokenize.sent_tokenize(el.text)
     
            # set initial title       
            if el.category == "Title" and title == "":
                title = el.text
            
            for sentence in sentences:
                sentence_token_count = len(tokenizer.tokenize(sentence))
                
                # if adding another sentence exceeds the token limit (or it's a new title), close the current chunk
                if curr_token_count + sentence_token_count > max_tokens or el.category == "Title":
                    if curr_chunk_text.strip():
                        append_chunk()
                        
                        # for non-title elements, start a new chunk with the overlap of the last sentence
                        if el.category != "Title":
                            curr_chunk_text = last_sentence + " "
                            curr_token_count = last_sentence_token_count
                        else:
                            curr_chunk_text = ""
                            curr_token_count = 0
                        
                # append the sentence to the current chunk
                if el.category == "Title":
                    title = el.text  # update title
                    curr_chunk_text += sentence + "\n\n"
                else:
                    curr_chunk_text += sentence + " "

                curr_token_count += len(tokenizer.tokenize(sentence))
                last_sentence = sentence
                last_sentence_token_count = sentence_token_count
        
        if curr_chunk_text.strip():
            append_chunk()
            
    def log(self, elements: bool = True, chunks: bool = True, output_file: Optional[str] = None):
        if not self.elements:
            return

        if output_file:
            with open(output_file, "w") as f:
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
        self.clean_elements(remove_titles=True, remove_list_of_titles=True)
        self.chunk_elements()

        if verbose: 
            self.log(elements=False, output_file="chunking.log")

        return self.chunks
