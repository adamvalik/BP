from abc import ABC, abstractmethod
from typing import List, Union
from sentence_transformers import SentenceTransformer
import openai
from tqdm import tqdm

class BaseEmbeddingModel(ABC):
    @abstractmethod
    def embed(self, texts: Union[str, List[str]]):
        pass

class HuggingFaceEmbeddingModel(BaseEmbeddingModel):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(self.model_name)

    def embed(self, texts: Union[str, List[str]], batch_size: int = 32):
        if isinstance(texts, str):
            texts = [texts]

        if batch_size == 0:
            return self.model.encode(texts)

        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding Batches", unit="batch"):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.model.encode(batch)
            embeddings.extend(batch_embeddings)
        return embeddings

class OpenAIEmbeddingModel(BaseEmbeddingModel):
    def __init__(self, model_name: str = "text-embedding-ada-002", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key

    def embed(self, texts: Union[str, List[str]]):
        if isinstance(texts, str):
            texts = [texts]

        openai.api_key = self.api_key
        embeddings = []

        for text in texts:
            response = openai.Embedding.create(input=text, model=self.model_name)
            embedding = response['data'][0]['embedding']
            embeddings.append(embedding)

        return embeddings

class EmbeddingModelFactory:
    @staticmethod
    def get_model(model_type: str = "huggingface", **kwargs) -> BaseEmbeddingModel:
        if model_type == "huggingface":
            return HuggingFaceEmbeddingModel(**kwargs)
        elif model_type == "openai":
            return OpenAIEmbeddingModel(**kwargs)
        else:
            raise ValueError(f"Unknown model_type '{model_type}'")
