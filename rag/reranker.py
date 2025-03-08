from chunk import Chunk
from typing import List
from sentence_transformers import CrossEncoder

class Reranker:
    
    @staticmethod
    def rerank(query, candidate_chunks: List[Chunk]) -> List[Chunk]:
        """using cross encoder, rerank the candidate chunks based on the query"""
        # load the cross-encoder model
        cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        ranks = cross_encoder.rank(query, [chunk.text for chunk in candidate_chunks])

        reranked_chunks = []
        for rank in ranks:
            chunk = candidate_chunks[rank['corpus_id']]
            chunk.reranked_score = rank['score']
            reranked_chunks.append(chunk)

        return reranked_chunks

from vector_store import VectorStore
from utils import color_print

query = "tips on running a marathon"
vector_store = VectorStore()
chunks = vector_store.hybrid_search(query, k=10) 
vector_store.close()

if not chunks:
    print("No chunks found.")
    
color_print(f"Hybrid search returned {len(chunks)} chunks.")
for chunk in chunks:
    print(chunk.filename)
    print("-"*50)
    
reranked_chunks = Reranker.rerank(query, chunks)
    
for chunk in reranked_chunks:
    print(chunk.filename)
    print("-"*25)



