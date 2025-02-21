from urllib import response
from vector_store import VectorStore
from rag_pipeline import RAGPipeline


vector_store = VectorStore()

try:
    rag_pipeline = RAGPipeline(vector_store)
    objects = rag_pipeline.vector_store.hybrid_search("", k=1)
    if not objects:
        print("No results found.")
    else:
        for obj in objects:
            print(f"Score: {obj.metadata.score} {obj.metadata.explain_score}")
            print(f"Filename: {obj.properties['filename']}")
            print(f"Text: {obj.properties['text']}")
            print("-------------------------------")


finally:
    vector_store.close()

