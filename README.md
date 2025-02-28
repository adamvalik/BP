# BP: Retrieval-Augmented Generation

This project uses Docker Compose, which is included with Docker Desktop (download from [docker.com](https://www.docker.com/products/docker-desktop/))

## Project Structure

- rag: Contains the RAG implementation and FastAPI endpoints.
- web_app: Contains the Vue.js frontend code.
- docker-compose.yml: Docker Compose configuration to manage all services.
- doc: Documentation.

### Commands inside the docker
Watch for changes in Tailwind CSS (if not already working):
```bash
docker exec -it frontend-app npx tailwindcss -i ./src/assets/tailwind.css -o ./src/assets/output.css --watch
```

Services will be available at:
- [http://localhost:8081](http://localhost:8080) - Web App frontend
- [http://localhost:8000](http://localhost:8000) - FastAPI backend
- [http://localhost:8080](http://localhost:8081) - Weaviate

API Documentation:
- [http://localhost:8000/docs](http://localhost:8000/docs) - FastAPI Swagger UI

## Testing

For testing the RAG system, setup the virtual environment and install the requirements:
```bash
cd rag
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Hybrid search is tested on dataset from: https://www.kaggle.com/datasets/jensenbaxter/10dataset-text-document-classification

Download the dataset and place it in the `txt-dataset` folder.

Insert the dataset into the database (running on localhost:8080):
```bash
python insert_data.py
```

Run the tests (optional: verbose mode, show stdout):
```bash
pytest -v -s tests/some_test.py
```

## Generating

Set the `OPENAI_API_KEY` environment variable in `.env` file.

## Google Drive Integration 

```bash
ngrok http http://localhost:8000
```
to expose the FastAPI server to the internet, so Google Drive can send notifications about changes. Run this before starting the services and set the provided URL.