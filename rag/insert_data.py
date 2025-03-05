from vector_store import VectorStore
from document_processor import DocumentProcessor
from utils import color_print
import os

# https://www.kaggle.com/datasets/jensenbaxter/10dataset-text-document-classification
# download the dataset and extract it to a folder

dataset_folder = "txt-dataset"

vector_store = VectorStore()

try:
    color_print(f"\nIngesting documents from directory: {dataset_folder}", color="blue")
    buffer = []
    for filename in os.listdir(dataset_folder):
        file_path = os.path.join(dataset_folder, filename)
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
            vector_store.add_documents(file_path)

    if buffer:
        vector_store.insert_chunks_batch(buffer)

finally:
    vector_store.close()