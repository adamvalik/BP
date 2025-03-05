from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from weaviate.exceptions import WeaviateConnectionError
from contextlib import asynccontextmanager
import json

from vector_store import VectorStore
from llm_wraper import LLMWrapper
from google_drive_downloader import GoogleDriveDownloader

class QueryRequest(BaseModel):
    query: str
    rights: str
    
class FolderIngestRequest(BaseModel):
    driveURL: str
    

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    gd_downloader = GoogleDriveDownloader()
    gd_downloader.initialize_changes_page_token()
    channel_id, response_id = gd_downloader.start_changes_watch()
    yield
    gd_downloader.stop_changes_watch(channel_id, response_id)
    print("Google Drive Changes watch stopped.")


app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/driveurl")
async def get_drive_url():
    gd_downloader = GoogleDriveDownloader()
    url = gd_downloader.get_url() if not None else ""
    return {"url": url}

@app.post("/ingest_folder")
async def ingest_folder(request: FolderIngestRequest):
    gd_downloader = GoogleDriveDownloader()
    gd_downloader.save_url(request.driveURL)
    try:
        vector_store = VectorStore()
    except WeaviateConnectionError:
        # handle weaviate connection error
        raise HTTPException(status_code=500, detail="Failed to connect to VectorStore.")

    gd_downloader.bulk_ingest(vector_store)
    vector_store.close()

    return {"message": "Ingestion started."}

@app.post("/delete_schema")
async def delete_schema():
    try:
        vector_store = VectorStore()
    except WeaviateConnectionError:
        # handle weaviate connection error
        raise HTTPException(status_code=500, detail="Failed to connect to VectorStore.")
    
    vector_store.delete_schema()
    vector_store.close()
    return {"message": "Schema deleted."}

@app.post("/query")
def query_endpoint(request: QueryRequest):
    try:
        vector_store = VectorStore()
    except WeaviateConnectionError:
        # handle weaviate connection error
        raise HTTPException(status_code=500, detail="Failed to connect to VectorStore.")

    chunks = vector_store.hybrid_search(request.query) # returns List[Chunk]
    # chunks = vector_store.hybrid_search(request.query, request.rights)
    vector_store.close()
    if not chunks:
        # handle [] no chunks found
        pass
    
    llm_wrapper = LLMWrapper()

    def stream():
        serialized_chunks = [vars(chunk) for chunk in chunks]
        yield json.dumps({
            "text": None,
            "metadata": {
                "chunks": serialized_chunks
            }
        }) + "\n"

        for llm_response in llm_wrapper.get_stream_response(request.query, chunks):
            yield json.dumps({
                "text": llm_response, # response.choices[0].delta.content (str)
                "metadata": None
            }) + "\n"
    
    return StreamingResponse(stream(), media_type="application/json")

@app.post("/webhook")
async def receive_notification( 
    x_goog_resource_id: str = Header(None), 
    x_goog_resource_state: str = Header(None)
):
    print("\n=== Webhook Received ===")
    print("Headers:")
    print(f"x-goog-resource-id: {x_goog_resource_id}")
    print(f"x-goog-resource-state: {x_goog_resource_state}")
    print("========================\n")
    
    if x_goog_resource_state == "change":
        try:
            vector_store = VectorStore()
        except WeaviateConnectionError:
            # handle weaviate connection error
            raise HTTPException(status_code=500, detail="Failed to connect to VectorStore.")
        
        gd_downloader = GoogleDriveDownloader()
        gd_downloader.sync_changes(vector_store)
        vector_store.close()
        
    return {"status": "success"} # ACK
    
@app.get("/")
async def root():
    return {"message": "FastAPI Server is Running"}

@app.get("/filenames")
async def get_all_filenames():
    try:
        vector_store = VectorStore()
    except WeaviateConnectionError:
        # handle weaviate connection error
        raise HTTPException(status_code=500, detail="Failed to connect to VectorStore.")
    
    filenames = vector_store.get_all_filenames()
    vector_store.close()
    return {"filenames": filenames}
