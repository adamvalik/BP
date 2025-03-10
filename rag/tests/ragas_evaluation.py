from vector_store import VectorStore
from weaviate.exceptions import WeaviateConnectionError
from reranker import Reranker
from llm_wraper import LLMWrapper
from utils import color_print

from dotenv import load_dotenv
load_dotenv()

import json
# load the testset
testset = []
with open("tests/test-sets/testset1.jsonl", "r") as f:
    for line in f:
        testset.append(json.loads(line))

try:
    vector_store = VectorStore()
except WeaviateConnectionError:
    color_print("Weaviate is not running. Please start Weaviate and try again.", color="red")
    exit()

dataset = []
for test_sample in testset:
    query = test_sample["user_input"]
    reference = test_sample["reference"]
    reference_contexts = test_sample["reference_contexts"]
    
    chunks = vector_store.hybrid_search(query, k=3)
    if not chunks:
        color_print("No chunks found for query: ", color="red", additional_text=query)
        continue
    
    reranked_chunks = Reranker.rerank(query, chunks)
    contexts = [chunk.text for chunk in reranked_chunks]
    
    llm_wrapper = LLMWrapper()
    response = llm_wrapper.get_response(query, reranked_chunks)

    dataset.append(
        {
            "user_input": query,
            "retrieved_contexts": contexts,
            "reference_contexts": reference_contexts,
            "response": response,
            "reference": reference
        }
    )    

vector_store.close()

# evaluation
from ragas import EvaluationDataset
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
from ragas.metrics import (
    LLMContextPrecisionWithoutReference,  # user_input, response, retrieved_contexts
    LLMContextPrecisionWithReference,  # user_input, reference, retrieved_contexts
    NonLLMContextPrecisionWithReference,  # retrieved_contexts, reference_contexts
    LLMContextRecall,  # user_input, reference, retrieved_contexts
    NonLLMContextRecall,  # retrieved_contexts, reference_contexts
    NoiseSensitivity,  # user_input, response, reference, retrieved_contexts -- mode="relevant" or "irrelevant"
    ResponseRelevancy,  # user_input, response
    Faithfulness,  # user_input, response, retrieved_contexts
    FaithfulnesswithHHEM,  # user_input, response, retrieved_contexts -- clasifier model (T5) trained to detect hallucinations
    FactualCorrectness, # response, reference
)
# LLM metrics are more accurate and closer to human evaluation

evaluation_dataset = EvaluationDataset.from_list(dataset)
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
result = evaluate(
    dataset=evaluation_dataset,
    # uncomment the chosen metrics to evaluate
    metrics=[
        # LLMContextPrecisionWithoutReference(),
        # LLMContextPrecisionWithReference(),
        # NonLLMContextPrecisionWithReference(),
        # LLMContextRecall(),
        # NonLLMContextRecall(),
        # NoiseSensitivity(),
        # NoiseSensitivity(mode="irrelevant"),
        # ResponseRelevancy(),
        # Faithfulness(),
        # FaithfulnesswithHHEM(), # exceeds the token limit
        # FactualCorrectness()
    ],
    llm=evaluator_llm)

color_print("-"*50, color="yellow")
result.upload()

df = result.to_pandas()
average_metrics = df.select_dtypes(include=['number']).mean()

# mean of all metrics
color_print("-"*50, color="yellow")
color_print("Evaluation statistics:")
print(average_metrics)
color_print("-"*50, color="yellow")

