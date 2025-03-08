from vector_store import VectorStore
from document_processor import DocumentProcessor
from utils import color_print
import os
import time

dataset_folder = "txt-dataset-2/sport"

def add_documents(folder_path):
    color_print(f"\nIngesting documents from directory: {folder_path}", color="blue")
    buffer = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            if vector_store.document_exists(file_path):
                # avoid duplicate ingestion
                color_print(f"Document {file_path} already exists in the vector store. Skipping ingestion...", color="yellow")
            else:
                document_processor = DocumentProcessor(filename=file_path)
                chunks = document_processor.process()
                if chunks:
                    buffer.extend(chunks)

        elif os.path.isdir(file_path):
            add_documents(file_path)

    if buffer:
        vector_store.insert_chunks_batch(buffer)


vector_store = VectorStore()

try:
    start_time = time.perf_counter()
    add_documents(dataset_folder)
    color_print(f"\nIngestion complete!", color="green")
    end_time = time.perf_counter()
    color_print(f"Total time: {end_time - start_time:.2f} seconds")
finally:
    vector_store.close()
    
