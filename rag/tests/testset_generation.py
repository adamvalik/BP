import os
import time
import random
from utils import color_print
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import DirectoryLoader
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from ragas.testset import TestsetGenerator

DOCS_DIR = "/Users/adamvalik/Downloads/test-wiki"
SPLITTED_DOCS_DIR = f"{DOCS_DIR}/split_files"

def split_files(num_parts=20):
    """generate_with_langchain_docs cannot take the whole wiki_XX.txt at once as input,
    so I need to split it into smaller files first."""
    os.makedirs(SPLITTED_DOCS_DIR, exist_ok=True)

    cnt = 0
    for filename in os.listdir(DOCS_DIR):
        file_path = os.path.join(DOCS_DIR, filename)
        if not os.path.isfile(file_path):
            continue
        if not file_path.endswith(".txt"):
            continue
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        lines_per_part = total_lines // num_parts
        remainder = total_lines % num_parts
        
        start = 0
        for i in range(num_parts):
            end = start + lines_per_part + (1 if i < remainder else 0)
            part_lines = lines[start:end]
            start = end
            
            output_file = os.path.join(SPLITTED_DOCS_DIR, f"part_{cnt}.txt")
            cnt += 1
            with open(output_file, 'w', encoding='utf-8') as out_f:
                out_f.writelines(part_lines)

split_files()
loader = DirectoryLoader(SPLITTED_DOCS_DIR)
docs = loader.load()

generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
generator_embeddings = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2"))
generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)
    
testset_size = 20

# batch_size = len(docs) // num_batches
# for i in range(num_batches):
#     print(f"Processing batch {i+1}...")
#     start_idx = i * batch_size
#     end_idx = (i + 1) * batch_size if i < num_batches - 1 else len(docs)
#     docs_batch = docs[start_idx:end_idx]
#     dataset = generator.generate_with_langchain_docs(docs_batch, testset_size=5)
#     dataset.to_jsonl(f"tests/test-sets/testset-test-wiki-{i}.jsonl")
#     dataset.upload()
#     time.sleep(60)  # wait for the API to cool down
    
# # merge testsets
# with open("testset-test-wiki.jsonl", 'w', encoding='utf-8') as outfile:
#     for file in os.listdir("tests/test-sets"):
#         if file.startswith("testset-test-wiki-") and file.endswith(".jsonl"):
#             with open(file, 'r', encoding='utf-8') as infile:
#                 for line in infile:
#                     outfile.write(line)


dataset = generator.generate_with_langchain_docs(random.sample(docs, testset_size), testset_size=testset_size)
dataset.to_jsonl(f"tests/test-sets/testset-test-wiki.jsonl")
dataset.upload()

                    
color_print("-"*50, color="yellow")
color_print(f"Testset generation complete!")

