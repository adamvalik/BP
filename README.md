# BP

This project uses Docker Compose, which is included with Docker Desktop (download from [docker.com](https://www.docker.com/products/docker-desktop/))

## Project Structure

- backend: Contains the FastAPI backend code.
- web_app: Contains the Vue.js frontend code.
- docker-compose.yml: Docker Compose configuration to manage all services.

### Commands inside the docker
Watch for changes in Tailwind CSS (if not already working):
```bash
docker exec -it vue_frontend npx tailwindcss -i ./src/assets/tailwind.css -o ./src/assets/output.css --watch
```

Services will be available at:
- [http://localhost:8081](http://localhost:8080) - Web App frontend
- [http://localhost:8000](http://localhost:8000) - FastAPI backend
- [http://localhost:9200](http://localhost:9200) - Elasticsearch
- [http://localhost:8080](http://localhost:8081) - Weaviate

API Documentation:
- [http://localhost:8000/docs](http://localhost:8000/docs) - FastAPI Swagger UI
- [http://localhost:8000/redoc](http://localhost:8000/redoc) - FastAPI Redoc UI
