from vector_store import VectorStore

# https://www.kaggle.com/datasets/jensenbaxter/10dataset-text-document-classification
# download the dataset and extract it to a folder

dataset_folder = "txt-dataset"

vector_store = VectorStore()

try:
    vector_store.add_documents(dataset_folder)

finally:
    vector_store.close()

