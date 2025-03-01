from document_processor import DocumentProcessor
from embedding_model import EmbeddingModelFactory
import time
import pytest
from dotenv import load_dotenv
from utils import color_print

load_dotenv()

TEST_FILE_PATH = "tests/test-files/long.txt"

@pytest.fixture(scope="module")
def text_chunks():
    document_processor = DocumentProcessor(TEST_FILE_PATH)
    chunks = document_processor.process()
    texts = [chunk.text for chunk in chunks]
    return texts

def test_prep(text_chunks):
    pass

def test_huggingface_shape():
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface")
    embeddings = embedding_model.embed(["Hello", "world!"])
    
    color_print(f"Hugging Face embeddings shape: {len(embeddings[0])}", color="blue")
    
def test_huggingface(text_chunks):
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface")
    print()
    
    start = time.perf_counter()
    embedding_model.embed(text_chunks)
    end = time.perf_counter()
    
    color_print(f"Hugging Face completed in {end - start:.2f} seconds", color="blue")
    
def test_huggingface_batch(text_chunks):
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface")
    print()
    
    start = time.perf_counter()
    embedding_model.embed(text_chunks, batch_size=100)
    end = time.perf_counter()
    
    color_print(f"Hugging Face Batch completed in {end - start:.2f} seconds", color="blue")
    
# def test_openai_shape():
#     embedding_model = EmbeddingModelFactory.get_model(model_type="openai")
#     embeddings = embedding_model.embed(["Hello", "world!"])
    
#     color_print("OpenAI embeddings shape: ", len(embeddings[0]), color="blue")
    
# def test_openai(text_chunks):
#     embedding_model = EmbeddingModelFactory.get_model(model_type="openai")
#     print()
    
#     start = time.perf_counter()
#     embedding_model.embed(text_chunks)
#     end = time.perf_counter()
    
#     color_print(f"OpenAI completed in {end - start:.2f} seconds", color="blue")