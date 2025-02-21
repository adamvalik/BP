import pytest
from rag_pipeline import RAGPipeline
from vector_store import VectorStore

@pytest.mark.parametrize("query, filename", [
    ("who felt like running alone?", "No results found")
])
def test_query_hybrid(query, filename):
    vector_store = VectorStore()
    rag_pipeline = RAGPipeline(vector_store)
    assert rag_pipeline.query_hybrid(query) == filename
    vector_store.close()
