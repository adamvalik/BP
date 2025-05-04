# retrieval_eval.py - Retrieval testing script
# Author: Adam Valík <xvalik05@stud.fit.vut.cz>

import json

from dotenv import load_dotenv
from reranker import Reranker
from rewriter import Rewriter
from tqdm import tqdm
from utils import color_print
from vector_store import VectorStore

load_dotenv()

QUERY_FILE = "tests/test-sets/queries_retrieval_cursed.jsonl"
AUTOCUT = True
TOP_K = 1
ALPHA = 0.55
RERANKING = False
RERANKER_CUTOFF = 0.5
REWRITING = True

with open(QUERY_FILE, "r", encoding="utf-8") as f:
    test_cases = [json.loads(line) for line in f]

vector_store = VectorStore()

for REWRITING in [False, True]:
        results = []
        recall_at_1 = 0  # exact match
        recall_at_k = 0  # present in context 
        total = 0
        context_size = 0
        ranks = []


        for c in tqdm(test_cases, desc="Evaluating", unit="case"):
            query = c["query"]
            expected_id = c["expected_chunk_id"]
            
            search_query = query
            if REWRITING:
                search_query = Rewriter.rewrite(query)

            chunks = vector_store.hybrid_search(query=search_query, alpha=ALPHA, autocut=AUTOCUT, k=TOP_K)
            
            if RERANKING:
                chunks = Reranker.rerank(search_query, chunks, cutoff=RERANKER_CUTOFF)

            retrieved_ids = [c.chunk_id.split("/")[-1] for c in chunks]
            context_size += len(retrieved_ids)
            total += 1

            try:
                rank = retrieved_ids.index(expected_id) + 1
                if rank == 1:
                    recall_at_1 += 1
                recall_at_k += 1
            except ValueError:
                rank = None  # not found

            ranks.append(rank)

            results.append({
                "query": query,
                "expected_chunk_id": expected_id,
                "retrieved_ids": retrieved_ids,
                "rank": rank
            })

        ranks = [r for r in ranks if r]
        avg_rank = sum(ranks) / len(ranks) if ranks else 0
        avg_context_size = context_size / total
        summary = {
            "total": total,
            "recall@1": recall_at_1 / total,
            "in context": recall_at_k / total,
            "not found": total - recall_at_k,
            "average_rank": avg_rank,
            "average_context_size": avg_context_size,
        }

        color_print("\n=== Retrieval Evaluation Summary ===")
        color_print(f"File: {QUERY_FILE}", color="yellow")
        color_print(f"Rewriting: {REWRITING}", color="yellow")
        color_print(f"Parameters: TOP_K={TOP_K}, ALPHA={ALPHA}, RERANKING={RERANKING}, REWRITING: {REWRITING}, CUTOFF={RERANKER_CUTOFF}, AUTOCUT={AUTOCUT}", color="yellow")
        for k, v in summary.items():
            color_print(f"{k}: {v}", color="yellow")

vector_store.close()
