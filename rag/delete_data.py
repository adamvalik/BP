from vector_store import VectorStore

vector_store = VectorStore()

try:
    vector_store.delete_schema()

finally:
    vector_store.close()

