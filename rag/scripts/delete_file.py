from vector_store import VectorStore
import os

v = VectorStore()

FOLDER = "/Users/adamvalik/Downloads/test-wiki-2nd"

for file in os.listdir(FOLDER):
    file_path = os.path.join("/Users/adamvalik/Downloads/test-wiki", file)
    v.delete_document(file_path)

v.close()