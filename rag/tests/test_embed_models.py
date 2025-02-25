from document_processor import DocumentProcessor
from embedding_model import EmbeddingModelFactory
import time
import pytest

TEST_FILE_PATH = "tests/test-files/long.txt"

@pytest.fixture(scope="module")
def text_chunks():
    chunks = DocumentProcessor.process(TEST_FILE_PATH)
    texts = [chunk.text for chunk in chunks]
    return texts

def test_prep(text_chunks):
    pass

def test_huggingface_shape():
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface")
    embeddings = embedding_model.embed(["Hello", "world!"])
    
    print("\033[34mHugging Face embeddings shape: ", embeddings[0].shape, "\033[0m")

def test_huggingface(text_chunks):
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface")
    print()
    
    start = time.perf_counter()
    embedding_model.embed(text_chunks)
    end = time.perf_counter()
    
    print("\033[34mHugging Face completed in ", f"{end - start:.2f}", " seconds\033[0m")
    
def test_huggingface_batch(text_chunks):
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface")
    print()
    
    start = time.perf_counter()
    embedding_model.embed(text_chunks, batch_size=100)
    end = time.perf_counter()
    
    print("\033[34mHugging Face Batch completed in ", f"{end - start:.2f}", " seconds\033[0m")