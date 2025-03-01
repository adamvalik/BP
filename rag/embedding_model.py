from abc import ABC, abstractmethod
from typing import List, Union
from tqdm import tqdm
import os

class BaseEmbeddingModel(ABC):
    @abstractmethod
    def embed(self, texts: Union[str, List[str]]):
        pass

class HuggingFaceEmbeddingModel(BaseEmbeddingModel):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = self._init_model()
        
    def _init_model(self):
        # lazy import
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(self.model_name)

    def embed(self, texts: Union[str, List[str]], batch_size: int = 0):
        if isinstance(texts, str):
            texts = [texts]

        if batch_size == 0:
            if len(texts) > 1:
                print(f"Embedding {len(texts)} text chunks...")
            embeddings = self.model.encode(texts)
        else:
            embeddings = []
            print(f"Embedding {len(texts)} text chunks in batches (batch_size: {batch_size})")
            for i in tqdm(range(0, len(texts), batch_size), desc=f"Embedding Batches", unit="batch"):
                batch = texts[i:i+batch_size]
                batch_embeddings = self.model.encode(batch)
                embeddings.extend(batch_embeddings)

        return embeddings

class OpenAIEmbeddingModel(BaseEmbeddingModel):
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self.client = self._init_client()

    def _init_client(self):
        import openai
        return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def embed(self, texts: Union[str, List[str]]):
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []

        for text in tqdm(texts, desc="Embedding with OpenAI", unit="text"):
            try:
                response = self.client.embeddings.create(input=text, model=self.model_name)
                embeddings.append(response.data[0].embedding)
            except Exception as e:
                print(f"Failed to generate embedding for text: {text[:50]}... - Error: {e}")

        return embeddings

class EmbeddingModelFactory:
    @staticmethod
    def get_model(model_type: str = "huggingface", **kwargs) -> BaseEmbeddingModel:
        model_type = model_type.lower()
        if model_type == "huggingface":
            return HuggingFaceEmbeddingModel(**kwargs)
        elif model_type == "openai":
            return OpenAIEmbeddingModel(**kwargs)
        else:
            raise ValueError(f"Unknown model_type '{model_type}'")
