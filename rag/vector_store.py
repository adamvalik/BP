from weaviate import connect_to_local
from weaviate.classes.query import MetadataQuery, Filter, HybridFusion
from weaviate.classes.config import Property, DataType, Configure, VectorDistances
from weaviate.classes.data import DataObject
from weaviate.client import WeaviateClient
from tqdm import tqdm
import time
from chunk import Chunk
from embedding_model import EmbeddingModelFactory
from weaviate.exceptions import WeaviateConnectionError
import os
from chunk import Chunk
from typing import List
from utils import color_print

class VectorStore():
    def __init__(self):
        self.client = self.connect()
        if self.client is None:
            raise WeaviateConnectionError("Failed to connect to Weaviate after multiple attempts.")
        self.collection_name = "DocumentChunks"
        self.get_schema()
        self.embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface", model_name="all-mpnet-base-v2")
        
    @staticmethod
    def connect() -> WeaviateClient:
        print("Connecting to Weaviate...")
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
        
    def document_exists(self, file_id):
        response = self.collection.query.fetch_objects(
            filters=Filter.by_property("file_id").equal(file_id),
            limit=1
        )
        return len(response.objects) > 0

    def insert_chunks(self, chunks, embeddings = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])

        for i, chunk in enumerate(tqdm(chunks, desc="One-by-One Insert", unit="chunk")):
            self.collection.data.insert(properties=chunk.to_dict(), vector=embeddings[i])

    def insert_chunks_batch(self, chunks, embeddings = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])

        with self.collection.batch.dynamic() as batch:
            for i, chunk in enumerate(tqdm(chunks, desc=f"Inserting Batches", unit="chunks")):
                batch.add_object(properties=chunk.to_dict(), vector=embeddings[i])

    def insert_many_chunks(self, chunks, embeddings = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])

        chunk_objs = [DataObject(properties=chunk.to_dict(), vector=embeddings[i]) for i, chunk in enumerate(chunks)]
        self.collection.data.insert_many(chunk_objs)
        
    def update_document(self, file_id, new_chunks):
        if not self.document_exists(file_id):
            color_print(f"File {file_id} not found in collection.", color="yellow")
            return

        # delete existing document
        self.delete_document(file_id)
        # insert new chunks
        self.insert_many_chunks(new_chunks)

    def delete_document(self, file_id):
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

    def close(self):
        if self.client:
            self.client.close()
        
    def hybrid_search(self, query: str, rights: str = None, k: int = 5, alpha: float = 0.5, autocut: bool = False) -> List[Chunk]:
        assert 0 <= alpha <= 1, "Alpha must be between 0 and 1."
        assert rights in [None, "normal", "superior"], "Rights must be None, 'normal', or 'superior'."
        
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
        # chunks = chunks if chunks[0].score > 0.5 else []
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
                explain_score=obj.metadata.explain_score
            )
            chunks.append(chunk)
        return chunks
    
    def get_all_filenames(self):
        filenames = []
        for item in self.collection.iterator():
            filename = item.properties["filename"]
            if filename not in filenames:
                filenames.append(filename)
        
        return filenames    