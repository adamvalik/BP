from vector_store import VectorStore
from reranker import Reranker
from llm_wraper import LLMWrapper
from rewriter import Rewriter
from utils import color_print
from weaviate.exceptions import WeaviateConnectionError
from dotenv import load_dotenv

def get_response_for_query(query: str):
    try:
        vector_store = VectorStore()
    except WeaviateConnectionError:
        color_print("Weaviate is not running. Please start Weaviate and try again.", color="red")
        exit()
    
    rewritten_query = Rewriter.rewrite(query)

    chunks = vector_store.hybrid_search(rewritten_query)
    vector_store.close()
    
    reranked_chunks = Reranker.rerank(query, chunks)
    
    llm_wrapper = LLMWrapper()
    return llm_wrapper.get_response(query, reranked_chunks)


if __name__ == "__main__":
    load_dotenv()
    query = input("Query: ")
    print("-"*50)
    response = get_response_for_query(query)
    print("-"*50)
    color_print("Response: ", color="green", additional_text=response)
    print()
    
