import json
import datetime
from tqdm import tqdm
from dotenv import load_dotenv
from weaviate.exceptions import WeaviateConnectionError

from vector_store import VectorStore
from reranker import Reranker
from rewriter import Rewriter
from llm_wraper import LLMWrapper
from utils import color_print

from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI

# LLM metrics are more accurate and closer to human evaluation
from ragas.metrics import (
    LLMContextPrecisionWithoutReference,  # user_input, response, retrieved_contexts
    LLMContextRecall,  # user_input, reference, retrieved_contexts
    NoiseSensitivity,  # user_input, response, reference, retrieved_contexts -- mode="relevant" or "irrelevant"
    ResponseRelevancy,  # user_input, response
    Faithfulness,  # user_input, response, retrieved_contexts
    FactualCorrectness, # response, reference
)

# parameters
TESTSET = "tests/test-sets/ragas_single_hop.jsonl"
REWRITING = False
ALPHA = 0.5
AUTOCUT = True
TOP_K = 1
RERANKING = False
RERANKER_CUTOFF = 0.5

def generate_responses() -> str:
    # load the testset and connect to Weaviate
    testset = []
    with open(TESTSET, "r") as f:
        testset = [json.loads(line) for line in f]

    try:
        vector_store = VectorStore()
    except WeaviateConnectionError:
        color_print("Weaviate is not running. Please start Weaviate and try again.", color="red")
        exit()

    # generate responses for each test case 
    llm_wrapper = LLMWrapper()
    dataset = []

    for sample in tqdm(testset, desc="Generating responses", unit="test"):
        query = sample["user_input"]
        reference = sample["reference"]
        # reference_contexts = sample["reference_contexts"]

        search_query = query
        if REWRITING:
            search_query = Rewriter.rewrite(query)

        chunks = vector_store.hybrid_search(query=search_query, alpha=ALPHA, autocut=AUTOCUT, k=TOP_K)
        
        if RERANKING:
            chunks = Reranker.rerank(search_query, chunks, cutoff=RERANKER_CUTOFF)

        contexts = [chunk.text for chunk in chunks]
        response = llm_wrapper.get_response(query, chunks)

        dataset.append({
            "user_input": query,
            "retrieved_contexts": contexts,
            # "reference_contexts": reference_contexts,
            "response": response,
            "reference": reference
        })

    vector_store.close()
    color_print("All responses generated, starting to evaluate...")

    # save the dataset
    metadata_line = {
        "__metadata__": {
            "TESTSET": TESTSET,
            "REWRITING": REWRITING,
            "ALPHA": ALPHA,
            "AUTOCUT": AUTOCUT,
            "TOP_K": TOP_K,
            "RERANKING": RERANKING,
            "RERANKER_CUTOFF": RERANKER_CUTOFF,
        }
    }

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if "single_hop" in TESTSET:
        output_path = f"tests/test-sets/ragas_single_hop_results_{timestamp}.jsonl"
    elif "multi_hop" in TESTSET:
        output_path = f"tests/test-sets/ragas_multi_hop_results_{timestamp}.jsonl"
    else:
        output_path = f"tests/test-sets/ragas_results_{timestamp}.jsonl"
    
    with open(output_path, "w") as f:
        f.write(json.dumps(metadata_line) + "\n")
        for item in dataset:
            f.write(json.dumps(item) + "\n")
            
    return output_path
            
def evaluation(dataset_name: str):
    # load the dataset to evaluate
    dataset = []        
    with open(dataset_name, "r") as f:
        dataset = [json.loads(line) for line in f]

    # remove the first line (metadata) and create the evaluation dataset
    evaluation_dataset = EvaluationDataset.from_list(dataset[1:])
    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))

    result = evaluate(
        dataset=evaluation_dataset,
        metrics=[
            LLMContextPrecisionWithoutReference(),  # vyhledal jsem relevantni chunky? - retrieval is focused
            LLMContextRecall(),                     # obsahuji chunky vse k poskytnuti odpovedi? - retrieval is complete
            NoiseSensitivity(mode="irrelevant"),    # je odpoved dobra i pres sum? - system is robust
            ResponseRelevancy(),                    # je odpoved relevantni dotazu? - answer is helpful
            Faithfulness(),                         # vychazi odpoved z kontextu? - no hallucination
            FactualCorrectness(),                   # je odpoved fakticky spravna? - answer is correct
        ],
        llm=evaluator_llm
    )

    color_print("-" * 50, color="yellow")
    result.upload()

    df = result.to_pandas()
    average_metrics = df.select_dtypes(include=['number']).mean()

    color_print("-" * 50, color="yellow")
    color_print("Evaluation statistics:")
    print(average_metrics)
    color_print("-" * 50, color="yellow")
    
    # read the __metadata__ line from the dataset
    metadata_line = dataset[0]["__metadata__"]
    
    # save the results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"tests/results/ragas_evaluation_{timestamp}.jsonl" 
    with open(output_path, "w") as f:
        f.write(json.dumps(metadata_line) + "\n")
        f.write(json.dumps(average_metrics.to_dict()) + "\n")

if __name__ == "__main__":
    load_dotenv()
    
    color_print("Starting RAGAS evaluation...", color="yellow")
    dataset = generate_responses()
    evaluation(dataset_name=dataset)
    color_print("Evaluation complete!", color="green")
    
    # 1 běh 50 testu 6 metrik ~0.5 usd 