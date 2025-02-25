from tracemalloc import start
import pytest
from rag_pipeline import RAGPipeline
from vector_store import VectorStore
from document_processor import DocumentProcessor
from embedding_model import EmbeddingModelFactory
import time
import weaviate

TEST_FILE_PATH = "tests/test-files/long.txt"

@pytest.fixture(scope="module")
def chunks_and_embeddings():
    chunks = DocumentProcessor.process(TEST_FILE_PATH)
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface", model_name="all-MiniLM-L6-v2")
    embeddings = embedding_model.embed([chunk.text for chunk in chunks])
    return chunks, embeddings

@pytest.fixture(scope="module")
def vector_store():
    store = VectorStore()
    yield store
    store.close()

@pytest.fixture(scope="module")
def rag_pipeline(vector_store):
    pipeline = RAGPipeline(vector_store)
    return pipeline

def test_prep(rag_pipeline, chunks_and_embeddings):
    pass

def test_insert_chunks(rag_pipeline, chunks_and_embeddings):
    """Benchmark for One-by-One Insert"""
    chunks, embeddings = chunks_and_embeddings
    rag_pipeline.vector_store.delete_document(TEST_FILE_PATH)
    
    start = time.perf_counter()
    rag_pipeline.vector_store.insert_chunks(chunks, embeddings=embeddings)
    end = time.perf_counter()
    
    print("\033[34mOne-by-One Insert completed in " + f"{end - start:.2f}" + " seconds\033[0m")

def test_insert_chunks_batch_benchmark(rag_pipeline, chunks_and_embeddings):
    """Benchmark for Batch Insert"""
    chunks, embeddings = chunks_and_embeddings
    rag_pipeline.vector_store.delete_document(TEST_FILE_PATH)

    start = time.perf_counter()
    rag_pipeline.vector_store.insert_chunks_batch(chunks, embeddings=embeddings)
    end = time.perf_counter()

    print("\033[34mBatch Insert completed in " + f"{end - start:.2f}" +  " seconds\033[0m")

def test_insert_many_chunks_benchmark(rag_pipeline, chunks_and_embeddings):
    """Benchmark for Many Chunks Insert (Adaptive Batch)"""
    chunks, embeddings = chunks_and_embeddings
    rag_pipeline.vector_store.delete_document(TEST_FILE_PATH)

    start = time.perf_counter()
    try:
        rag_pipeline.vector_store.insert_many_chunks(chunks, embeddings=embeddings)
        end = time.perf_counter()
        print("\033[34mMany Chunks Insert completed in " + f"{end - start:.2f}" + " seconds\033[0m")
    
    except weaviate.exceptions.WeaviateBatchError:
        print("\033[31mInsert failed due to message larger than max\033[0m")
        assert False

