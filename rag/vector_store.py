from weaviate import connect_to_local
from weaviate.classes.query import MetadataQuery, Filter
from weaviate.classes.config import Property, DataType, Configure
from tqdm import tqdm
from time import time

class WeaviateClient():  
    def __init__(self):
        self.client = connect_to_local()
        self.collection_name = "DocumentChunks"
        self.collection = None
             
    def create_schema(self):
        # avoid recreating the schema
        if not self.client.collections.exists(self.collection_name):
            print("Schema does not exist. Creating schema...")   
            self.collection = self.client.collections.create(
                name=self.collection_name,
                vectorizer_config=Configure.Vectorizer.text2vec_transformers(),
                properties=[
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="filename", data_type=DataType.TEXT)
                ]
            )
        else:
            self.collection = self.client.collections.get(self.collection_name)
            print("Skipping schema creation. Schema already exists...")
     
    def insert_chunks(self, chunks):        
        print(f"Inserting {len(chunks)} chunks into Weaviate one by one...")

        start_time = time()
        
        for chunk in tqdm(chunks, desc="One-by-One Import", unit="chunk"):
            self.collection.data.insert(
                {"text": chunk["text"], "filename": chunk["metadata"]["filename"]}
            )

        end_time = time()
        print(f"One-by-one import completed in {end_time - start_time:.2f} seconds.")
        
    def insert_chunks_batch(self, chunks, batch_size=100):        
        print(f"Inserting {len(chunks)} chunks into Weaviate...")

        start_time = time()
        
        with self.collection.batch.dynamic() as batch:
            for chunk in tqdm(chunks, desc="Batch Importing", unit="chunk"):
                batch.add_object(
                    properties={
                        "text": chunk["text"],
                        "filename": chunk["metadata"]["filename"]
                    },
                )

        end_time = time()
        print(f"Batch import completed in {end_time - start_time:.2f} seconds.")

        
    def delete_schema(self):
        self.client.collections.delete(self.collection_name)
        print("Schema deleted.")
        
    def hybrid_search(self, query, k):
        response = self.collection.query.hybrid(
            query=query,
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
