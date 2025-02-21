from document_processor import DocumentProcessor
from embedding_model import EmbeddingModelFactory
from vector_store import VectorStore
import os

class RAGPipeline:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.vector_store.create_schema()

    def add_document(self, file_path):
        if self.vector_store.document_exists(file_path):
            # avoid duplicate ingestion
            print(f"Document {file_path} already exists in the vector store. Skipping ingestion...")
        else:
            chunks = DocumentProcessor.process(file_path, verbose=True)
            if chunks:
                self.vector_store.insert_chunks(chunks)

    def add_documents(self, dir_path):
        buffer = []
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            if os.path.isfile(file_path):
                if self.vector_store.document_exists(file_path):
                    # avoid duplicate ingestion
                    print(f"Document {file_path} already exists in the vector store. Skipping ingestion...")
                else:
                    chunks = DocumentProcessor.process(file_path)
                    if chunks:
                        buffer.extend(chunks)

            elif os.path.isdir(file_path):
                self.add_documents(file_path)

        self.vector_store.insert_many_chunks(buffer)

    def insert_speed_test(self, file_path: str):
        chunks = DocumentProcessor.process(file_path)
        embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface", model_name="all-MiniLM-L6-v2")
        embeddings = embedding_model.embed([chunk.text for chunk in chunks])

        print("\033[34mInserting strategies speed test\033[0m")
        if chunks:
            self.vector_store.delete_chunks(file_path)
            self.vector_store.insert_chunks(chunks, embeddings=embeddings)
            self.vector_store.delete_chunks(file_path)
            self.vector_store.insert_chunks_batch(chunks, embeddings=embeddings)
            self.vector_store.delete_chunks(file_path)
            self.vector_store.insert_many_chunks(chunks, embeddings=embeddings)

    def embedding_speed_test(self, file_path: str):
        chunks = DocumentProcessor.process(file_path)
        texts = [chunk.text for chunk in chunks]
        print("\033[34mEmbedding strategies speed test\033[0m")
        embedding_model = EmbeddingModelFactory.get_model(model_type="huggingface")
        embedding_model.embed(texts)
        embedding_model.embed(texts, batch_size=100)
        # embedding_model = EmbeddingModelFactory.get_model(model_type="openai", api_key=None)
        # embedding_model.embed(texts)

    # def answer_query(self, query):
    #     response = self.vector_store.hybrid_search(query, k=5)
    #     for obj in response.objects:
    #         print(f"Score: {obj.metadata.score} {obj.metadata.explain_score}")
    #         print(f"Filename: {obj.properties['filename']}")
    #         print(f"Text: {obj.properties['text']}")
    #         print("-------------------------------")

    # def query_hybrid(self, query) -> str:
    #     """returns the filename of the most similar document to the query"""
    #     response = self.vector_store.hybrid_search(query, k=1)
    #     if response.objects:
    #         return response.objects[0].properties["filename"]
    #     return "No results found"
