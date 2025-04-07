from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from weaviate.exceptions import WeaviateConnectionError
from contextlib import asynccontextmanager
import json
from reranker import Reranker

from utils import color_print
from vector_store import VectorStore
from llm_wraper import LLMWrapper
from google_drive_downloader import GoogleDriveDownloader
from rewriter import Rewriter
from log import log
from typing import List

class QueryRequest(BaseModel):
    query: str
    rights: str
    history: List[str]
    use_history: bool
    
class FolderIngestRequest(BaseModel):
    driveURL: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    # gd_downloader = GoogleDriveDownloader()
    # gd_downloader.initialize_changes_page_token()
    # channel_id, response_id = gd_downloader.start_changes_watch()
    yield
    # gd_downloader.stop_changes_watch(channel_id, response_id)
    # print("Google Drive Changes watch stopped.")


app = FastAPI(lifespan=lifespan) # uncomment for GDrive integration

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def connect_to_vector_store():
    try:
        vector_store = VectorStore()
    except WeaviateConnectionError:
        # handle weaviate connection error
        raise HTTPException(status_code=500, detail="Failed to connect to VectorStore.")
    return vector_store

@app.get("/driveurl")
def get_drive_url():
    gd_downloader = GoogleDriveDownloader()
    url = gd_downloader.get_url() if not None else ""
    return {"url": url}

@app.post("/ingest_folder")
def ingest_folder(request: FolderIngestRequest):
    gd_downloader = GoogleDriveDownloader()
    gd_downloader.save_url(request.driveURL)
    vector_store = connect_to_vector_store()

    gd_downloader.bulk_ingest(vector_store)
    vector_store.close()

    return {"message": "Ingestion started."}

@app.post("/delete_schema")
def delete_schema():
    vector_store = connect_to_vector_store()
    
    vector_store.delete_schema()
    vector_store.close()
    return {"message": "Schema deleted."}

@app.post("/query")
def query_endpoint(request: QueryRequest):
    print(f"Query: {request.query}, Rights: {request.rights}, Use History: {request.use_history}, History: {request.history}")
    
    vector_store = connect_to_vector_store()
        
    # rewrite the query to optimize for retrieval
    if request.use_history:
        rewritten_query = Rewriter.rewrite_with_history(request.query, request.history)
    else:
        rewritten_query = Rewriter.rewrite(request.query)

    color_print(f"Rewritten query: {rewritten_query}", color="yellow")
    
    if request.rights == "user":
        chunks = vector_store.hybrid_search(rewritten_query, autocut=True, k=3, rights="user")
    else:
        chunks = vector_store.hybrid_search(rewritten_query, autocut=True, k=3)
        
    color_print(f"Hybrid search returned {len(chunks)} chunks.", color="yellow")
        
    vector_store.close()    
    
    reranked_chunks = Reranker.rerank(rewritten_query, chunks)
    
    color_print(f"Reranked chunks: {len(reranked_chunks)}", color="yellow")
        
    llm_wrapper = LLMWrapper()
    response = []
    llm_query = rewritten_query if request.use_history else request.query

    def stream():
        serialized_chunks = [vars(chunk) for chunk in reranked_chunks]
        yield json.dumps({
            "text": None,
            "metadata": {
                "chunks": serialized_chunks
            }
        }) + "\n"


        for llm_response in llm_wrapper.get_stream_response(llm_query, reranked_chunks):
            response.append(llm_response)
            yield json.dumps({
                "text": llm_response, # response.choices[0].delta.content (str)
                "metadata": None
            }) + "\n"
            
        log(request.query, rewritten_query, chunks, reranked_chunks, "".join(response))
    
    color_print("Generating response...", color="yellow")
    
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
def root():
    return {"message": "FastAPI Server is Running"}

@app.get("/sync")
def sync():
    try:
        vector_store = VectorStore()
    except WeaviateConnectionError:
        # handle weaviate connection error
        raise HTTPException(status_code=500, detail="Failed to connect to VectorStore.")
    
    gd_downloader = GoogleDriveDownloader()
    gd_downloader.sync_changes(vector_store)
    vector_store.close()
    
    return {"message": "Sync completed."}
    
@app.get("/filenames")
def get_all_filenames():
    try:
        vector_store = VectorStore()
    except WeaviateConnectionError:
        # handle weaviate connection error
        raise HTTPException(status_code=500, detail="Failed to connect to VectorStore.")
    
    filenames = vector_store.get_all_filenames()
    vector_store.close()
    return {"filenames": filenames}
