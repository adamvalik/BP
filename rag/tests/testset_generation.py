# testset_generation.py - Testset generation script
# Author: Adam Valík <xvalik05@stud.fit.vut.cz>

import datetime
import os
import random
import shutil

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.testset import TestsetGenerator
from unstructured.partition.text import partition_text

from utils import color_print

NUM_ARTICLES = 60
TESTSET_SIZE = 20
SOURCE_FOLDER = "/Users/adamvalik/Downloads/test-wiki"
TEMP_DOCS_DIR = "tests/temp_split_docs"

def create_document_testset():
    # cleanup/create temp directory
    if os.path.exists(TEMP_DOCS_DIR):
        shutil.rmtree(TEMP_DOCS_DIR)
    os.makedirs(TEMP_DOCS_DIR, exist_ok=True)

    # load random file 
    txt_files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".txt")]
    file_path = os.path.join(SOURCE_FOLDER, random.choice(txt_files))

    color_print(f"Using file: {file_path}", color="cyan")

    elements = partition_text(filename=file_path)

    # group elements for each title to create separate articles
    articles = []
    current_article = None
    for el in elements:
        if el.category == "Title":
            if current_article is not None:
                articles.append(current_article)
            current_article = el.text + "\n\n"   
        else:
            current_article += el.text + "\n\n"

    # select random articles
    selected_articles = random.sample(articles, NUM_ARTICLES)
    selected_articles = [article for article in selected_articles if len(article) > 400]

    for i, article in enumerate(selected_articles):
        with open(os.path.join(TEMP_DOCS_DIR, f"article_{i}.txt"), "w") as out_file:
            out_file.write(article)
            
def load_documents_from_folder(folder_path, merge_batch_size=3):
    documents = []
    for filename in os.listdir(folder_path):
        if not filename.endswith(".txt"):
            continue
        full_path = os.path.join(folder_path, filename)
        with open(full_path, "r") as f:
            lines = f.readlines()

        title = lines[0].strip()
        content = "".join(lines).strip()
                
        doc = Document(
            page_content=content,
            metadata={
                "title": title,
                "headlines": [title]
            }
        )
        documents.append(doc)
    
    merged_docs = []
    for i in range(0, len(documents), merge_batch_size):
        group = documents[i:i+merge_batch_size]
        merged_content = "\n\n".join([doc.page_content for doc in group])
        merged_titles = " + ".join([doc.metadata["title"] for doc in group])

        merged_doc = Document(
            page_content=merged_content,
            metadata={
                "title": f"Combined: {merged_titles}",
                "headlines": [doc.metadata["title"] for doc in group]
            }
        )
        merged_docs.append(merged_doc)

    return merged_docs
    
def generate_testset():
    load_dotenv()
    
    # load documents
    docs = load_documents_from_folder(TEMP_DOCS_DIR)

    generator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o-mini"))
    generator_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    )
    generator = TestsetGenerator(llm=generator_llm, embedding_model=generator_embeddings)

    dataset = generator.generate_with_langchain_docs(docs, testset_size=TESTSET_SIZE)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"tests/test-sets/testset_{timestamp}.jsonl"
    dataset.to_jsonl(output_path)
    dataset.upload()

    color_print("-" * 50, color="yellow")
    color_print("Testset generation complete!", color="green")
    
if __name__ == "__main__":
    create_document_testset()
    generate_testset()
