### Run Docker Compose to start all services
```bash
docker compose up --build
```

### To view logs for all services, use:
```bash
docker compose logs -f
```

### To stop all services, use:
```bash
docker compose down
```

Services will be available at:
- [http://localhost:8081](http://localhost:8081) - Web App frontend
- [http://localhost:8000](http://localhost:8000) - FastAPI backend
- [http://localhost:9200](http://localhost:9200) - Elasticsearch
- [http://localhost:8080](http://localhost:8080) - Weaviate

API Documentation:
- [http://localhost:8000/docs](http://localhost:8000/docs) - FastAPI Swagger UI
- [http://localhost:8000/redoc](http://localhost:8000/redoc) - FastAPI Redoc UI