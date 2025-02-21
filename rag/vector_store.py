from weaviate import connect_to_local
from weaviate.classes.query import MetadataQuery, Filter
from weaviate.classes.config import Property, DataType
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
                properties=[
                    Property(name="chunkid", data_type=DataType.TEXT),
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

    def insert_chunks(self, chunks):
        print(f"Inserting {len(chunks)} chunks into Weaviate one by one...")

        start_time = time()

        embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])
        for i, chunk in enumerate(tqdm(chunks, desc="One-by-One Import", unit="chunk")):
            # vars() converts the Chunks instance to a dict
            self.collection.data.insert(properties=vars(chunk), vector=embeddings[i])

        end_time = time()
        print(f"One-by-one import completed in {end_time - start_time:.2f} seconds.")

    def insert_chunks_batch(self, chunks, batch_size=100):
        print(f"Inserting {len(chunks)} chunks into Weaviate...")

        start_time = time()

        embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])
        with self.collection.batch.dynamic() as batch:
            for i, chunk in enumerate(tqdm(chunks, desc="Batch Importing", unit="chunk")):
                batch.add_object(properties=vars(chunk), vector=embeddings[i])

        end_time = time()
        print(f"Batch import completed in {end_time - start_time:.2f} seconds.")

    def insert_many_chunks(self, chunks):
        # weaviate.exceptions.WeaviateBatchError: Query call with protocol GRPC batch failed with message <AioRpcError of RPC that terminated with:
        # status = StatusCode.RESOURCE_EXHAUSTED
        # details = "CLIENT: Sent message larger than max (28296577 vs. 10485760)"
        # debug_error_string = "UNKNOWN:Error received from peer  {created_time:"2025-02-21T13:00:21.355903+01:00", grpc_status:8,
        # grpc_message:"CLIENT: Sent message larger than max (28296577 vs. 10485760)"}"

        print(f"Inserting {len(chunks)} (many) chunks into Weaviate...")

        start_time = time()

        embeddings = self.embedding_model.embed([chunk.text for chunk in chunks])
        chunks_objs = list()
        for i, chunk in enumerate(tqdm(chunks, desc="Many Chunks Importing", unit="chunk")):
            chunks_objs.append(DataObject(properties=vars(chunk), vector=embeddings[i]))

        self.collection.data.insert_many(chunks_objs)

        end_time = time()
        print(f"Many chunks import completed in {end_time - start_time:.2f} seconds.")

    def delete_schema(self):
        self.client.collections.delete(self.collection_name)
        print("Schema deleted.")

    def hybrid_search(self, query, k):
        embedding = self.embedding_model.embed(query)[0]
        response = self.collection.query.hybrid(
            query=query,
            vector=embedding,
            alpha=0.5,
            return_metadata=MetadataQuery(score=True, explain_score=True),
            limit=k
            # auto_limit=1, # number of close groups - autocut
        )
        return response

    def close(self):
        self.client.close()

    def document_exists(self, file_path):
        filename = file_path.split("/")[-1]
        response = self.collection.query.fetch_objects(
            filters=Filter.by_property("filename").equal(filename),
        )
        return len(response.objects) > 0
