import re
from weaviate import connect_to_local
from weaviate.classes.query import MetadataQuery, Filter
from weaviate.classes.config import Property, DataType, Configure, VectorDistances
from weaviate.classes.data import DataObject
from tqdm import tqdm
from time import time
from chunk import Chunk
from embedding_model import EmbeddingModelFactory

class VectorStore():
    def __init__(self):
        self.client = connect_to_local()
        self.collection_name = "DocumentChunks"
        self.collection = None
        self.embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface", model_name="all-MiniLM-L6-v2")

    def create_schema(self):
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
            print("Skipping schema creation. Schema already exists.")

    def insert_chunks(self, chunks, embeddings = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])
        print(f"Inserting {len(chunks)} chunks into Weaviate one by one...")

        start_time = time()
        for i, chunk in enumerate(tqdm(chunks, desc="One-by-One Insert", unit="chunk")):
            # vars() converts the Chunks instance to a dict
            self.collection.data.insert(properties=vars(chunk), vector=embeddings[i])

        end_time = time()
        print(f"One-by-one insert completed in {end_time - start_time:.2f} seconds.")

    def insert_chunks_batch(self, chunks, embeddings = None):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])
        print(f"Inserting {len(chunks)} chunks into Weaviate in batches...")

        start_time = time()
        with self.collection.batch.dynamic() as batch:
            for i, chunk in enumerate(tqdm(chunks, desc=f"Inserting Batches", unit="batch")):
                batch.add_object(properties=vars(chunk), vector=embeddings[i])

        end_time = time()
        print(f"Batch insert completed in {end_time - start_time:.2f} seconds.")

    def insert_many_chunks(self, chunks, embeddings = None, max_batch_size=10485760):
        if embeddings is None:
            embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])
        print(f"Inserting {len(chunks)} (many) chunks into Weaviate...")

        start_time = time()
        batch_size = 0
        batch = []

        for i, chunk in enumerate(tqdm(chunks, desc="Inserting Many Chunks", unit="chunk")):
            chunk_obj = DataObject(properties=vars(chunk), vector=embeddings[i])
            chunk_size = len(str(chunk_obj).encode('utf-8')) # in bytes

            if batch_size + chunk_size > max_batch_size:
                self.collection.data.insert_many(batch)
                batch = []
                batch_size = 0

            batch.append(chunk_obj)
            batch_size += chunk_size

        # remaining chunks
        if batch:
            self.collection.data.insert_many(batch)

        end_time = time()
        print(f"Many chunks insert completed in {end_time - start_time:.2f} seconds.")

    def delete_schema(self):
        self.client.collections.delete(self.collection_name)
        print("Schema deleted.")

    def delete_chunks(self, file_path):
        if self.document_exists(file_path):
            filename = file_path.split("/")[-1]
            while self.document_exists(file_path):
                self.collection.data.delete_many(
                    where=Filter.by_property("filename").equal(filename)
                )
                # NOTE: There is a configurable maximum limit (QUERY_MAXIMUM_RESULTS) on the number of objects
                # that can be deleted in a single query (default 10,000). To delete more objects than the limit,
                # re-run the query.
            print(f"File {file_path} successfully deleted from collection.")

    def close(self):
        self.client.close()

    def hybrid_search(self, query: str, k: int = 5, alpha: float = 0.5):
        assert 0 <= alpha <= 1, "Alpha must be between 0 and 1."
        
        embedding = self.embedding_model.embed(query)[0]
        response = self.collection.query.hybrid(
            query=query,
            vector=embedding,
            alpha=alpha,
            return_metadata=MetadataQuery(score=True, explain_score=True),
            limit=k
        )
        return response.objects if response.objects[0].metadata.score > 0.5 else []
    
    def hybrid_search_autocut(self, query: str, k: int = 1, alpha: float = 0.5):
        assert 0 <= alpha <= 1, "Alpha must be between 0 and 1."
        
        embedding = self.embedding_model.embed(query)[0]
        response = self.collection.query.hybrid(
            query=query,
            vector=embedding,
            alpha=alpha,
            return_metadata=MetadataQuery(score=True, explain_score=True),
            auto_limit=k, # number of close groups - autocut
        )
        return response.objects if response.objects[0].metadata.score > 0.5 else []

    def document_exists(self, file_path):
        filename = file_path.split("/")[-1]
        response = self.collection.query.fetch_objects(
            filters=Filter.by_property("filename").equal(filename),
            limit=1
        )
        return len(response.objects) > 0

    # def list_files(self):
    #     response = self.collection.query.fetch_objects(
    #         filters=Filter.exists("filename"),
    #         limit=1000
    #     )
    #     return response.objects
