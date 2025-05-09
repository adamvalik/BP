# BP: Retrieval-Augmented Generation (RAG)

This project uses Docker Compose, which is included with Docker Desktop (download from [docker.com](https://www.docker.com/products/docker-desktop/))

## Project Structure

- `doc/`: Documentation.
- `rag/`: Contains the RAG implementation and FastAPI endpoints.
- `web_app/`: Contains the Vue.js frontend code.
- `docker-compose.yml`: Docker Compose configuration to manage all services.
```
.
├── doc
│   ├── excel@fit - student conference
│   ├── tex - thesis source code
│   └── xvalik05_bp.pdf - bachelor thesis
├── rag
│   ├── scripts
│   │   └── python scripts to operate the backend and database
│   ├── tests
│   │   ├── test-sets - test sets and results of the evaluation
│   │   ├── ragas_evaluation.py - evaluation script
│   │   ├── retrieval_eval.py - retrieval test script
│   │   ├── test_benchmark_insert.py - benchmark for insert methods
│   │   └── testset_generation.py - test set generation script
│   ├── .env.example - example of environment variables (turn into .env)
│   ├── api.py - FastAPI app
│   ├── Dockerfile 
│   ├── document_processor.py 
│   ├── embedding_model.py
│   ├── google_drive_downloader.py
│   ├── changes_state.py
│   ├── chunk.py
│   ├── llm_wrapper.py
│   ├── log.py
│   ├── requirements_eval.txt - libraries for evaluation
│   ├── requirements_multiformat.txt - libraries for multiformat document support
│   ├── requirements.txt - libraries for the system
│   ├── reranker.py
│   ├── rewriter.py
│   ├── utils.py
│   └── vector_store.py
├── web_app
│   ├── public
│   ├── src
│   │   ├── router
│   │   │   └── index.js
│   │   ├── views
│   │   │   └── HomeView.vue - frontend implementation
│   │   ├── App.vue
│   │   └── main.js
│   ├── Dockerfile
│   └── config files
└── docker-compose.yml
```

## Technologies Used
This project integrates several modern tools to build a RAG system. The implementation follows the official documentation of each technology:
- [Unstructured.io](https://docs.unstructured.io/open-source/introduction/overview/) - for document processing
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse) - for streaming responses
- [NLTK Sentence Tokenizer](https://www.nltk.org/api/nltk.tokenize.sent_tokenize.html) - for sentence splitting
- [Hugging Face AutoTokenizer](https://huggingface.co/docs/transformers/v4.49.0/en/model_doc/auto#transformers.AutoTokenizer) - for tokenization
- [Hugging Face Sentence Transformer](https://sbert.net/docs/sentence_transformer/pretrained_models.html) - for embeddings
- [Hugging Face Cross Encoder](https://sbert.net/docs/cross_encoder/pretrained_models.html) - for reranking
- [Weaviate](https://weaviate.io/developers/weaviate) - open-source vector database with hybrid search 
- [OpenAI API](https://platform.openai.com/docs/guides/text?api-mode=chat) - for LLM completions
- [Google Drive API](https://developers.google.com/workspace/drive/api/guides/about-sdk) - cloud storage integration
- [RAGAs](https://docs.ragas.io/en/stable) - RAG evaluation framework
- [Ngrok](https://ngrok.com/docs) - for exposing the FastAPI server to the internet
  
## Build
Setup the environment variables in `.env` file. Use `.env.example` as a template. Update the `rag/Dockerfile` if you want to support documents in various formats (needs additional tools and libraries).

```bash
docker compose up --build
```

Services will be available at:
- [http://localhost:8081](http://localhost:8080) - Web App frontend
- [http://localhost:8000](http://localhost:8000) - FastAPI backend
- [http://localhost:8080](http://localhost:8081) - Weaviate

API Documentation:
- [http://localhost:8000/docs](http://localhost:8000/docs) - FastAPI Swagger UI

## Google Drive Integration 

For Google Drive integration, you need to set up the Google Drive API and obtain credentials. Follow these steps:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the Google Drive API for your project.
4. Create a service account and download the `credentials.json` file.
5. Move the `credentials.json` file to the `rag` directory.

Expose the FastAPI server to the internet, so Google Drive can send notifications about changes. 
You can use [ngrok](https://ngrok.com/) for this purpose.
```bash
ngrok http http://localhost:8000
```
Set the provided URL in `.env` file.

## Testing

For testing the RAG system, setup the virtual environment and install the requirements:
```bash
cd rag
python -m venv venv
source venv/bin/activate
pip install -r requirements_eval.txt
```

System was tested on dataset from [kaggle Plain text Wikipedia (SimpleEnglish)](https://www.kaggle.com/datasets/ffatty/plain-text-wikipedia-simpleenglish)

Use the `insert_data.py` script to insert data into the Weaviate vector store and test the system with scripts in the `tests` directory. 
