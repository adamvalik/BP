import pytest
from vector_store import VectorStore
from document_processor import DocumentProcessor
from embedding_model import EmbeddingModelFactory
import time
import weaviate
from utils import color_print

TEST_FILE_PATH = "tests/test-files/long.txt"

@pytest.fixture(scope="module")
def chunks_and_embeddings():
    document_processor = DocumentProcessor(TEST_FILE_PATH)
    chunks = document_processor.process()
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface", model_name="all-MiniLM-L6-v2")
    embeddings = embedding_model.embed([chunk.text for chunk in chunks])
    return chunks, embeddings

@pytest.fixture(scope="module")
def vector_store():
    store = VectorStore()
    yield store
    store.close()

def test_prep(vector_store, chunks_and_embeddings):
    pass

def test_insert_chunks(vector_store, chunks_and_embeddings):
    """Benchmark for One-by-One Insert"""
    chunks, embeddings = chunks_and_embeddings
    vector_store.delete_document(TEST_FILE_PATH)
    
    start = time.perf_counter()
    vector_store.insert_chunks(chunks, embeddings=embeddings)
    end = time.perf_counter()
    
    color_print(f"One-by-One Insert completed in {end - start:.2f} seconds", color="blue")

def test_insert_chunks_batch_benchmark(vector_store, chunks_and_embeddings):
    """Benchmark for Batch Insert"""
    chunks, embeddings = chunks_and_embeddings
    vector_store.delete_document(TEST_FILE_PATH)

    start = time.perf_counter()
    vector_store.insert_chunks_batch(chunks, embeddings=embeddings)
    end = time.perf_counter()

    color_print(f"Batch Insert completed in {end - start:.2f} seconds", color="blue")

def test_insert_many_chunks_benchmark(vector_store, chunks_and_embeddings):
    """Benchmark for Many Chunks Insert (Adaptive Batch)"""
    chunks, embeddings = chunks_and_embeddings
    vector_store.delete_document(TEST_FILE_PATH)

    start = time.perf_counter()
    try:
        vector_store.insert_many_chunks(chunks, embeddings=embeddings)
        end = time.perf_counter()
        color_print(f"Many Chunks Insert completed in {end - start:.2f} seconds", color="blue")
    
    except weaviate.exceptions.WeaviateBatchError:
        color_print(f"Many Chunks Insert failed due to message larger than max", color="red")
        assert False

