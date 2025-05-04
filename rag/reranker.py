# File: reranker.py - Reranker module
# Author: Adam Valík <xvalik05@stud.fit.vut.cz>

from chunk import Chunk
from typing import List

from sentence_transformers import CrossEncoder


class Reranker:
    @staticmethod
    def rerank(query: str, candidate_chunks: List[Chunk], cutoff: float = 0.5) -> List[Chunk]:
        if not candidate_chunks:
            return []
        
        # load the cross-encoder model
        cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        reranks = cross_encoder.rank(query, [chunk.text for chunk in candidate_chunks])

        # rerank the chunks
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
        # shift the scores to be non-negative
        scores = [chunk.reranked_score for chunk in chunks]
        shifted_scores = [s - min(scores) for s in scores]

        # calculate the threshold based on the cutoff and the maximum score
        threshold = cutoff * max(shifted_scores)

        # filter the chunks based on the threshold
        filtered_chunks = []
        for chunk, shifted_score in zip(chunks, shifted_scores):
            if shifted_score >= threshold:
                filtered_chunks.append(chunk)
        
        return filtered_chunks
