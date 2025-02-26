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
from document_processor import DocumentProcessor
from chunk import Chunk
from typing import List

class VectorStore():
    def __init__(self):
        self.client = self.connect()
        if self.client is None:
            raise WeaviateConnectionError("Failed to connect to Weaviate after multiple attempts.")
        self.collection_name = "DocumentChunks"
        self.get_schema()
        self.embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface", model_name="all-MiniLM-L6-v2")
        
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
                print(f"Failed to connect to Weaviate: {e}, trying again...")
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
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="filename", data_type=DataType.TEXT),
                    Property(name="file_directory", data_type=DataType.TEXT),
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="page_number", data_type=DataType.INT),
                    Property(name="rights", data_type=DataType.TEXT)
                ],
            )
        else:
            self.collection = self.client.collections.get(self.collection_name)

    def delete_schema(self):
        self.client.collections.delete(self.collection_name)
        print("Schema deleted.")

    def insert_chunks(self, chunks, embeddings = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])

        for i, chunk in enumerate(tqdm(chunks, desc="One-by-One Insert", unit="chunk")):
            # vars() converts the Chunks instance to a dict
            self.collection.data.insert(properties=vars(chunk), vector=embeddings[i])

    def insert_chunks_batch(self, chunks, embeddings = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])

        with self.collection.batch.dynamic() as batch:
            for i, chunk in enumerate(tqdm(chunks, desc=f"Inserting Batches", unit="chunks")):
                batch.add_object(properties=vars(chunk), vector=embeddings[i])

    def insert_many_chunks(self, chunks, embeddings = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])

        chunk_objs = [DataObject(properties=vars(chunk), vector=embeddings[i]) for i, chunk in enumerate(chunks)]
        self.collection.data.insert_many(chunk_objs)

    def add_document(self, file_path):
        if self.document_exists(file_path):
            # avoid duplicate ingestion
            print(f"Document {file_path} already exists in the vector store. Skipping ingestion...")
        else:
            chunks = DocumentProcessor.process(file_path, verbose=True)
            if chunks:
                self.insert_chunks(chunks)

    def add_documents(self, dir_path):
        buffer = []
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            if os.path.isfile(file_path):
                if self.document_exists(file_path):
                    # avoid duplicate ingestion
                    print(f"Document {file_path} already exists in the vector store. Skipping ingestion...")
                else:
                    chunks = DocumentProcessor.process(file_path)
                    if chunks:
                        buffer.extend(chunks)

            elif os.path.isdir(file_path):
                self.add_documents(file_path)

        self.insert_chunks_batch(buffer)

    def delete_document(self, file_path):
        # NOTE: There is a configurable maximum limit (QUERY_MAXIMUM_RESULTS) on the number of objects
        # that can be deleted in a single query (default 10,000). To delete more objects than the limit,
        # re-run the query.
        if self.document_exists(file_path):
            filename = file_path.split("/")[-1]
            while self.document_exists(file_path):
                self.collection.data.delete_many(
                    where=Filter.by_property("filename").equal(filename)
                )
            print(f"File {file_path} successfully deleted from collection.")

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
        return chunks if chunks[0].score > 0.5 else []
    
    @staticmethod
    def get_chunks_from_objs(objects) -> List[Chunk]:
        chunks = []
        for obj in objects:
            chunk = Chunk(
                chunk_id=obj.properties["chunk_id"],
                text=obj.properties["text"],
                filename=obj.properties["filename"],
                file_directory=obj.properties["file_directory"],
                title=obj.properties["title"],
                page_number=obj.properties["page_number"],
                rights=obj.properties["rights"],
                score=obj.metadata.score,
                explain_score=obj.metadata.explain_score
            )
            chunks.append(chunk)
        return chunks
    
    def document_exists(self, file_path):
        filename = file_path.split("/")[-1]
        response = self.collection.query.fetch_objects(
            filters=Filter.by_property("filename").equal(filename),
            limit=1
        )
        return len(response.objects) > 0

    def get_all_file_paths(self):
        file_paths = []
        for item in self.collection.iterator():
            file_path = item.properties["file_directory"] + "/" + item.properties["filename"]
            if file_path not in file_paths:
                file_paths.append(file_path)
        
        return file_paths    