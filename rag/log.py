# File: log.py - logging RAG pipeline
# Author: Adam Valík <xvalik05@stud.fit.vut.cz>

import json
import logging
from chunk import Chunk
from typing import List

LOG_FILE = "rag.log"
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=LOG_FILE,
    encoding="utf-8",
    filemode="a",
)

def log(
    query: str,
    rewritten_query: str,
    retrieved_chunks: List[Chunk],
    reranked_chunks: List[Chunk],
    llm_response: str,
    timings: dict = None
):
    def format_chunks(chunks):
        return [chunk.log() for chunk in chunks]

    logging.warning("-" * 50)
    logging.warning(f"Query:           {query}")
    logging.warning(f"Rewritten Query: {rewritten_query}")

    logging.warning("\nRetrieved Chunks:")
    logging.warning(json.dumps(format_chunks(retrieved_chunks), indent=4))

    logging.warning("\nReranked Chunks:")
    logging.warning(json.dumps(format_chunks(reranked_chunks), indent=4))

    logging.warning("\nLLM Response:")
    logging.warning(llm_response.strip())

    if timings:
        logging.warning("\nTimings (seconds):")
        for step, duration in timings.items():
            logging.warning(f"  {step:25}: {duration:.4f}")

    logging.warning("-" * 50 + "\n\n")
