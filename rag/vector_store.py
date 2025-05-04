# File: vector_store.py - VectorStore module 
# Author: Adam Valík <xvalik05@stud.fit.vut.cz>

import os
import re
import time
from chunk import Chunk
from typing import List, Optional

from tqdm import tqdm
from rag.tests.ragas_evaluation import EMBEDDING
from weaviate import connect_to_local
from weaviate.classes.config import (Configure, DataType, Property,
                                     VectorDistances)
from weaviate.classes.data import DataObject
from weaviate.classes.query import Filter, HybridFusion, MetadataQuery
from weaviate.client import WeaviateClient
from weaviate.exceptions import WeaviateConnectionError

from embedding_model import EmbeddingModelFactory
from utils import color_print


class VectorStore():
    EMBEDDING_MODEL_TYPE = "huggingface"
    EMBEDDING_MODEL = "all-mpnet-base-v2"
    
    def __init__(self):
        self.client = self.connect()
        if self.client is None:
            raise WeaviateConnectionError("Failed to connect to Weaviate after multiple attempts.")
        self.collection_name = "DocumentChunks"
        self.get_schema()
        self.embedding_model = EmbeddingModelFactory.get_model(model_type=self.EMBEDDING_MODEL_TYPE, model_name=self.EMBEDDING_MODEL)
        color_print("Connected to Weaviate.")
        
    @staticmethod
    def connect() -> WeaviateClient:
        color_print("Connecting to Weaviate...", color="yellow")
        weaviate_url = os.getenv("WEAVIATE_HOST", "http://localhost:8080")
        host, port = weaviate_url.replace("http://", "").split(":")
        
        # connect to the Weaviate client, try again if connection fails
        for _ in range(3):
            try:
                client = connect_to_local(host=host, port=int(port))
                return client
            except WeaviateConnectionError as e:
                color_print(f"Failed to connect to Weaviate: {e}, trying again...", color="red")
                time.sleep(2)
        return None

    def get_schema(self):
        # avoid recreating the schema
        if not self.client.collections.exists(self.collection_name):
            print("Schema does not exist. Creating schema...")
            self.collection = self.client.collections.create(
                name=self.collection_name,
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE,
                ),
                properties=[
                    Property(name="chunk_id", data_type=DataType.TEXT),
                    Property(name="file_id", data_type=DataType.TEXT),
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="filename", data_type=DataType.TEXT),
                    Property(name="file_directory", data_type=DataType.TEXT),
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="page", data_type=DataType.TEXT),
                    Property(name="rights", data_type=DataType.TEXT)
                ],
            )
        else:
            self.collection = self.client.collections.get(self.collection_name)

    def delete_schema(self):
        self.client.collections.delete(self.collection_name)
        color_print("Schema deleted.", color="yellow")
        
    def document_exists(self, file_id: str) -> bool:
        response = self.collection.query.fetch_objects(
            filters=Filter.by_property("file_id").equal(file_id),
            limit=1
        )
        return len(response.objects) > 0

    def insert_chunks(self, chunks: List[Chunk], embeddings: Optional[List[float]] = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])

        for i, chunk in enumerate(tqdm(chunks, desc="One-by-One Insert", unit="chunk")):
            self.collection.data.insert(properties=chunk.to_dict(), vector=embeddings[i])

    def insert_chunks_batch(self, chunks: List[Chunk], embeddings: Optional[List[float]] = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks], batch_size=100)

        with self.collection.batch.dynamic() as batch:
            for i, chunk in enumerate(tqdm(chunks, desc=f"Inserting Batches", unit="chunks")):
                batch.add_object(properties=chunk.to_dict(), vector=embeddings[i])

    def insert_many_chunks(self, chunks: List[Chunk], embeddings: Optional[List[float]] = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])

        chunk_objs = [DataObject(properties=chunk.to_dict(), vector=embeddings[i]) for i, chunk in enumerate(chunks)]
        self.collection.data.insert_many(chunk_objs)
        
    def update_document(self, file_id: str, new_chunks: List[Chunk]):
        if not self.document_exists(file_id):
            color_print(f"File {file_id} not found in collection.", color="yellow")
            return

        # delete existing document
        self.delete_document(file_id)
        # insert new chunks
        self.insert_many_chunks(new_chunks)

    def delete_document(self, file_id: str):
        # NOTE: There is a configurable maximum limit (QUERY_MAXIMUM_RESULTS) on the number of objects
        # that can be deleted in a single query (default 10,000). To delete more objects than the limit,
        # re-run the query.
        deleted = False
        while self.document_exists(file_id):
            self.collection.data.delete_many(
                where=Filter.by_property("file_id").equal(file_id)
            )
            deleted = True
        
        if deleted:
            color_print(f"File {file_id} successfully deleted from collection.")
        else:
            color_print(f"File {file_id} not found in collection.", color="yellow")
            
    def get_rights(self, file_id: str) -> Optional[str]:
        response = self.collection.query.fetch_objects(
            filters=Filter.by_property("file_id").equal(file_id),
            limit=1
        )
        if len(response.objects) == 0:
            return None
        return response.objects[0].properties["rights"]

    def close(self):
        if self.client:
            self.client.close()
            
    def get_all_filenames(self) -> List[str]:
        filenames = []
        for item in self.collection.iterator():
            filename = item.properties["filename"]
            if filename not in filenames:
                filenames.append(filename)
        
        return filenames    
        
    def hybrid_search(self, query: str, rights: str = None, k: int = 5, alpha: float = 0.55, autocut: bool = False) -> List[Chunk]:
        assert 0 <= alpha <= 1, "Alpha must be between 0 and 1."
        
        embedding = self.embedding_model.embed(query)[0]
        response = self.collection.query.hybrid(
            query=query,
            vector=embedding,
            alpha=alpha,
            fusion_type=HybridFusion.RELATIVE_SCORE,
            return_metadata=MetadataQuery(score=True, explain_score=True),
            limit = k if not autocut else None,
            auto_limit= k if autocut else None,
            filters=Filter.by_property("rights").equal(rights) if rights else None
        )
        chunks = self.get_chunks_from_objs(response.objects)
        return chunks
    
    @staticmethod
    def get_chunks_from_objs(objects) -> List[Chunk]:
        chunks = []
        for obj in objects:
            chunk = Chunk(
                chunk_id=obj.properties["chunk_id"],
                file_id=obj.properties["file_id"],
                text=obj.properties["text"],
                filename=obj.properties["filename"],
                file_directory=obj.properties["file_directory"],
                title=obj.properties["title"],
                page=obj.properties["page"],
                rights=obj.properties["rights"],
                score=obj.metadata.score,
                explain_score=VectorStore.format_explain_score(obj.metadata.explain_score)
            )
            chunks.append(chunk)
        return chunks
    
    @staticmethod
    def format_explain_score(explain_score: str) -> str:
        pattern = re.compile(r"normalized score: ([\d.]+)")
        matches = pattern.findall(explain_score)

        if len(matches) == 1:
            return f"vector: {float(matches[0]):.2f}"
        elif len(matches) == 2:
            return f"keyword: {float(matches[0]):.2f} | vector: {float(matches[1]):.2f}"        
        else:
            return explain_score
