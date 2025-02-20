from document_processor import DocumentProcessor
from vector_store import WeaviateClient
import os

class RAGPipeline:
    def __init__(self, vector_store: WeaviateClient):
        self.vector_store = vector_store
        
    def ingest_document(self, file_path):
        document_chunks = self.chunk_document(file_path)
        if document_chunks:
            self.vector_store.insert_chunks(document_chunks)
        
    def chunk_document(self, file_path):
        # avoid duplicate ingestion
        if self.vector_store.document_exists(file_path):
            print(f"Document {file_path} already exists in the vector store. Skipping ingestion...")
            return None
        
        # ingest document
        document_chunks = DocumentProcessor.process(file_path)
        return document_chunks
        
    def ingest_documents(self, dir_path):
        buffer = []
        # merge_threshold = 500
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            if os.path.isfile(file_path):
                doc_chunks = self.chunk_document(file_path)
                if not doc_chunks:
                    continue
                
                buffer.extend(doc_chunks)
                # if len(buffer) >= merge_threshold:
                #     self.vector_store.insert_chunks_batch(buffer)
                #     buffer = []
                    
            elif os.path.isdir(file_path):
                self.ingest_documents(file_path)

        self.vector_store.insert_chunks_batch(buffer)
        buffer = []
        
        if len(buffer) > 0:
            self.vector_store.insert_chunks(buffer)
 
    def answer_query(self, query):
        response = self.vector_store.hybrid_search(query, k=5)
        for obj in response.objects:
            print(f"Score: {obj.metadata.score} {obj.metadata.explain_score}")
            print(f"Filename: {obj.properties['filename']}")
            print(f"Text: {obj.properties['text']}")
            print("-------------------------------")