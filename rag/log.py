from typing import List
import logging
from chunk import Chunk
import json

LOG_FILE = "rag.log"
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=LOG_FILE,
    encoding="utf-8",
    filemode="a"
)

def log(query: str, rewritten_query: str, retrieved_chunks: List[Chunk], reranked_chunks: List[Chunk], llm_response: str):
    def format_chunks(chunks):
        return [chunk.log() for chunk in chunks]

    logging.warning("-" * 50)
    logging.warning(f"Query:           {query}")
    logging.warning(f"Rewritten Query: {rewritten_query}")

    logging.warning("\nRetrieved Chunks:")
    logging.warning(json.dumps(format_chunks(retrieved_chunks), indent=4))  # Pretty-print retrieved chunks

    logging.warning("\nReranked Chunks:")
    logging.warning(json.dumps(format_chunks(reranked_chunks), indent=4))  # Pretty-print reranked chunks

    logging.warning("\nLLM Response:")
    logging.warning(llm_response.strip())  # Avoid excess newlines

    logging.warning("-" * 50 + "\n\n")    
