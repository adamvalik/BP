from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import DirectoryLoader
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from ragas.testset import TestsetGenerator

loader = DirectoryLoader("/Users/adamvalik/Downloads/txt-dataset-1/sport")
docs = loader.load()

generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
generator_embeddings = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2"))

generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)
dataset = generator.generate_with_langchain_docs(docs, testset_size=3)

dataset.to_jsonl("tests/test-sets/testset1.jsonl")
dataset.upload()