from document_processor import DocumentProcessor
from vector_store import VectorStore
import os

class RAGPipeline:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.vector_store.create_schema()

    def ingest_document(self, file_path):
        chunks = self.chunk_document(file_path)
        if chunks:
            self.vector_store.insert_chunks(chunks)

    def chunk_document(self, file_path):
        # avoid duplicate ingestion
        if self.vector_store.document_exists(file_path):
            print(f"Document {file_path} already exists in the vector store. Skipping ingestion...")
            return None

        # ingest document
        chunks = DocumentProcessor.process(file_path, verbose=True)
        return chunks

    def ingest_documents(self, dir_path):
        buffer = []
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            if os.path.isfile(file_path):
                chunks = self.chunk_document(file_path)
                if not chunks:
                    continue

                buffer.extend(chunks)
            elif os.path.isdir(file_path):
                self.ingest_documents(file_path)

        self.vector_store.insert_many_chunks(buffer)

    def answer_query(self, query):
        response = self.vector_store.hybrid_search(query, k=5)
        for obj in response.objects:
            print(f"Score: {obj.metadata.score} {obj.metadata.explain_score}")
            print(f"Filename: {obj.properties['filename']}")
            print(f"Text: {obj.properties['text']}")
            print("-------------------------------")

    def query_hybrid(self, query) -> str:
        """returns the filename of the most similar document to the query"""
        response = self.vector_store.hybrid_search(query, k=1)
        if response.objects:
            return response.objects[0].properties["filename"]
        return "No results found"


    def insert_speed_test(self, file_path):
        # TODO: not working independently
        chunks = self.chunk_document(file_path)
        print("\033[34mInserting strategies speed test\033[0m")
        if chunks:
            self.vector_store.insert_many_chunks(chunks)
            # self.vector_store.insert_chunks_batch(chunks)
            # self.vector_store.insert_chunks(chunks)
