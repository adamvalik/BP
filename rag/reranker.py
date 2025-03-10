from chunk import Chunk
from typing import List
from sentence_transformers import CrossEncoder

class Reranker:
    
    @staticmethod
    def rerank(query: str, candidate_chunks: List[Chunk]) -> List[Chunk]:
        """using cross encoder, rerank the candidate chunks based on the query"""
        if not candidate_chunks:
            return []
        
        # load the cross-encoder model
        cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        reranks = cross_encoder.rank(query, [chunk.text for chunk in candidate_chunks])

        reranked_chunks = []
        for rerank in reranks:
            chunk = candidate_chunks[rerank['corpus_id']]
            chunk.reranked_score = float(rerank['score']) #TypeError: Object of type float32 is not JSON serializable
            reranked_chunks.append(chunk)

        return reranked_chunks

if __name__ == "__main__":
    # demonstration
    from vector_store import VectorStore
    from utils import color_print

    query = "tips on running a marathon"
    vector_store = VectorStore()
    chunks = vector_store.hybrid_search(query, k=10) 
    vector_store.close()
        
    color_print(f"Hybrid search returned {len(chunks)} chunks.")
    for i, chunk in enumerate(chunks):
        print(f"{i}. {chunk.chunk_id}")
        
    color_print("-"*50, color="yellow")
    reranked_chunks = Reranker.rerank(query, chunks)
    color_print("Reranked chunks:")
        
    for i, chunk in enumerate(reranked_chunks):
        print(f"{i}. {chunk.chunk_id}")



