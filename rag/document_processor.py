from unstructured.partition.text import partition_text
# from unstructured.partition.pdf import partition_pdf
# from unstructured.partition.doc import partition_doc
# from unstructured.partition.docx import partition_docx
# from unstructured.partition.image import partition_image
# from unstructured.partition.md import partition_md
from unstructured.chunking.title import chunk_by_title
from unstructured.cleaners.core import clean
import emoji
import re
from typing import List
from chunk import Chunk

class DocumentProcessor():

    @staticmethod
    def partition_elements(file_path: str):
        ext = file_path.lower().split(".")[-1]
        if ext == "txt":
            try:
                elements = partition_text(filename=file_path)
            except FileNotFoundError as e:
                print("\033[31mFile not found\033[0m" + f": {file_path}, processing is skipped.")
                return []
            if not elements:
                print("\033[31mNo elements found\033[0m" + f" in {file_path}, processing is skipped.")
                return []
        # elif ext == "pdf":
        #     elements = partition_pdf(filename=file_path, strategy="hi_res") # images are ignored
        # elif ext == "docx":
        #     elements = partition_docx(filename=file_path, include_page_breaks=False)
        # elif ext == "doc":
        #     elements = partition_doc(filename=file_path)
        # elif ext == "md":
        #     elements = partition_md(filename=file_path)
        # elif ext in ["jpg", "png", "heic"]:
        #     elements = partition_image(filename=file_path)
        else:
            print("\033[31mUnsupported file extension\033[0m" + f": {ext}, processing of {file_path} is skipped.")
            return []
        return elements

    @staticmethod
    def clean_elements(elements):
        for el in elements:
            el.text = emoji.replace_emoji(el.text, "") # remove emojis
            el.text = re.sub(r"---+", "", el.text)  # remove horizontal lines (e.g., ---)
            el.text = re.sub(r"#+\s*", "", el.text)  # remove headers (e.g., ## Header)
            el.text = re.sub(r"\*\*(.*?)\*\*", r"\1", el.text)  # remove bold (e.g., **bold** -> bold)
            el.text = re.sub(r"\*(.*?)\*", r"\1", el.text)  # remove italics (e.g., *italic* -> italic)
            el.text = clean(el.text, extra_whitespace=True, dashes=True, bullets=True)
        cleaned_elements = [el for el in elements if el.text.strip()]
        cleaned_elements = [el for el in cleaned_elements if el.category not in ["Header", "Footer"]]
        return cleaned_elements

    @staticmethod
    def chunk_elements(elements) -> List[Chunk]:
        chunks = chunk_by_title(elements)
        processed_chunks = []
        title = ""

        for i, chunk in enumerate(chunks):
            # remove \n\n from chunk.text
            chunk_text = chunk.text.replace("\n\n", " ")

            # extract metadata from original elements
            meta = chunk.metadata.orig_elements[0].metadata
            c = Chunk(
                chunkid=f"{meta.filename}_{i}",
                text=chunk_text,
                filename=meta.filename,
                file_directory=meta.file_directory,
                title=title,
            )

            for elem in chunk.metadata.orig_elements:
                if elem.category == "Title":
                    c.title = elem.text
                    title = elem.text
                if not c.page_number and elem.metadata.page_number:
                    c.page_number = elem.metadata.page_number
                    # TODO: page as string for page range (e.g. "1-2")

            processed_chunks.append(c)
        return processed_chunks

    @staticmethod
    def process(file_path: str, verbose: bool = False) -> List[Chunk]:
        # processing pipeline
        elements = DocumentProcessor.partition_elements(file_path)
        if not elements:
            return []
        cleaned_elements = DocumentProcessor.clean_elements(elements)

        if verbose:
            print("\033[32m" + f"Partitioned {len(elements)} elements" + "\033[0m" + f" ({file_path})")
            for el in cleaned_elements:
                print(f"Category: {el.category}")
                print(f"Text: {el.text}")
                print("-------------------------------")

        chunks = DocumentProcessor.chunk_elements(cleaned_elements)

        if verbose:
            print("\033[32m" + f"Chunked {len(chunks)} chunks from {len(cleaned_elements)} elements"  + "\033[0m" + f" ({file_path})")
            for chunk in chunks:
                print(chunk)
                print("-------------------------------")

        return chunks
