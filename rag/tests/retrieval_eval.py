import json
import csv
from vector_store import VectorStore
from reranker import Reranker
from tqdm import tqdm
from utils import color_print

QUERY_FILE = "tests/test-sets/queries_retrieval.jsonl"
OUTPUT_CSV = "retrieval_eval_results.csv"
TOP_K = 1
ALPHA = 0.5
RERANKING = False
AUTOCUT = True

with open(QUERY_FILE, "r", encoding="utf-8") as f:
    test_cases = [json.loads(line) for line in f]

# for TOP_K in [1, 2]:
#     for RERANKING in [False, True]:        

for ALPHA in [0.0, 0.25, 0.4, 0.5, 0.6, 0.75, 1.0]:
        results = []
        recall_at_1 = 0  # exact match
        recall_at_k = 0  # present in context 
        total = 0
        context_size = 0
        ranks = []

        vector_store = VectorStore()

        for c in tqdm(test_cases, desc="Evaluating", unit="case"):
            query = c["query"]
            expected_id = c["expected_chunk_id"]

            chunks = vector_store.hybrid_search(query=query, k=TOP_K, alpha=ALPHA, autocut=AUTOCUT)
            if RERANKING:
                chunks = Reranker.rerank(query, chunks)

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

        vector_store.close()

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
        color_print(f"Parameters: TOP_K={TOP_K}, ALPHA={ALPHA}, RERANKING={RERANKING}, AUTOCUT={AUTOCUT}", color="yellow")
        for k, v in summary.items():
            color_print(f"{k}: {v}", color="yellow")
            
        color_print("====================================\n")

        # with open(OUTPUT_CSV, "w", newline='', encoding="utf-8") as csvfile:
        #     fieldnames = ["query", "expected_chunk_id", "retrieved_ids", "rank"]
        #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #     writer.writeheader()
        #     for row in results:
        #         writer.writerow(row)
