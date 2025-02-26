from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from weaviate.exceptions import WeaviateConnectionError
import json

from vector_store import VectorStore
from llm_wraper import LLMWrapper
from google_drive_downloader import GoogleDriveDownloader

class QueryRequest(BaseModel):
    query: str
    rights: str
    
load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_wrapper = LLMWrapper()
gd_downloader = GoogleDriveDownloader()
gd_downloader.start_watch()

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
async def receive_webhook( 
    x_goog_resource_id: str = Header(None), 
    x_goog_resource_state: str = Header(None)
):
    print("\n=== Webhook Received ===")
    print("Headers:")
    print(f"x-goog-resource-id: {x_goog_resource_id}")
    print(f"x-goog-resource-state: {x_goog_resource_state}")
    print("========================\n")
    
    return {"status": "success"}

    
@app.get("/")
async def root():
    return {"message": "FastAPI Server is Running"}
