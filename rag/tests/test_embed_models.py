from document_processor import DocumentProcessor
from embedding_model import EmbeddingModelFactory
import time
import pytest
from dotenv import load_dotenv
from utils import color_print

load_dotenv()

sentence_transformers_models = [
    "all-mpnet-base-v2",
    "all-MiniLM-L6-v2"
]

TEST_FILE_PATH = "tests/test-files/long.txt"

@pytest.fixture(scope="module")
def text_chunks():
    document_processor = DocumentProcessor(TEST_FILE_PATH)
    chunks = document_processor.process()
    texts = [chunk.text for chunk in chunks]
    return texts

def test_prep(text_chunks):
    pass

@pytest.mark.parametrize("model_name", sentence_transformers_models)
def test_huggingface_shape(model_name):
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface", model_name=model_name)
    embeddings = embedding_model.embed(["Hello", "world!"])
    
    color_print(f"{model_name} shape: {len(embeddings[0])}", color="blue")
    
@pytest.mark.parametrize("model_name", sentence_transformers_models)
def test_huggingface_limit(model_name):
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface", model_name=model_name)
    
    color_print(f"{model_name} limit: {embedding_model.model.max_seq_length}", color="blue")
    
@pytest.mark.parametrize("model_name", sentence_transformers_models)
def test_huggingface(text_chunks, model_name):
    embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface", model_name=model_name)
    print()
    
    start = time.perf_counter()
    embedding_model.embed(text_chunks)
    end = time.perf_counter()
    
    color_print(f"{model_name} completed in {end - start:.2f} seconds", color="blue")
    
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