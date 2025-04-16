from chunk import Chunk
from typing import List
from sentence_transformers import CrossEncoder

class Reranker:
    @staticmethod
    def rerank(query: str, candidate_chunks: List[Chunk], cutoff: float = 0.5) -> List[Chunk]:
        """using cross encoder, rerank the candidate chunks based on the query"""
        if not candidate_chunks:
            return []
        
        # load the cross-encoder model
        cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        reranks = cross_encoder.rank(query, [chunk.text for chunk in candidate_chunks])

        reranked_chunks = []
        for rerank in reranks:
            chunk = candidate_chunks[rerank['corpus_id']]
            chunk.reranked_score = float(rerank['score'])
            reranked_chunks.append(chunk)
        
        # filter out the chunks with low reranked scores
        if cutoff > 0:
            reranked_chunks = Reranker.filter_by_relative_score(reranked_chunks, cutoff)
        return reranked_chunks
    
    @staticmethod
    def filter_by_relative_score(chunks: List[Chunk], cutoff: float) -> List[Chunk]:
        scores = [chunk.reranked_score for chunk in chunks]
        shifted_scores = [s - min(scores) for s in scores]

        threshold = cutoff * max(shifted_scores)

        filtered_chunks = []
        for chunk, shifted_score in zip(chunks, shifted_scores):
            if shifted_score >= threshold:
                filtered_chunks.append(chunk)
        
        return filtered_chunks


if __name__ == "__main__":
    # demonstration
    from vector_store import VectorStore
    from utils import color_print

    query = "tips on running marathon"
    vector_store = VectorStore()
    chunks = vector_store.hybrid_search(query, autocut=True, k=3) 
    vector_store.close()
        
    color_print(f"Hybrid search returned {len(chunks)} chunks.")
    for i, chunk in enumerate(chunks):
        print(f"{i}. score: {chunk.score:.2f} - {chunk.chunk_id}")
        
    color_print("-"*50, color="yellow")
    reranked_chunks = Reranker.rerank(query, chunks, cutoff=0.5)
    color_print("Reranked chunks:")
        
    for i, chunk in enumerate(reranked_chunks):
        print(f"{i}. score: {chunk.reranked_score:.2f} - {chunk.chunk_id}")



