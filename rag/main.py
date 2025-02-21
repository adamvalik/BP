from vector_store import VectorStore
from rag_pipeline import RAGPipeline


vector_store = VectorStore()
rag_pipeline = RAGPipeline(vector_store)
rag_pipeline.


try:
    # vector_store.delete_schema()
    rag_pipeline = RAGPipeline(vector_store)
    rag_pipeline.chunk_document("txt-dataset/business/business_1.txt")
finally:
    vector_store.close()
