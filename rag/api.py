from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import json

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# # response model
class ResponseModel(BaseModel):
    reply_msg: str
    metadata: dict

# incoming message model
class Message(BaseModel):
    text: str

@app.post("/message-immediate", response_model=ResponseModel)
async def send_message(msg: Message):
    response = f"You said: {msg.text}. OK, well done, that's all for now!"
    metadata = {
        "score": 0.8,
        "link": "path/to/some/resource.pptx",
        "context": "context of the message"
    }
    return ResponseModel(reply_msg=response, metadata=metadata)


async def stream_response(msg: str):
    response = f"You asked: {msg}. That is a very interesting question. The good news is that I can provide you with an answer. The bad news is that I don't have any backend logic implemented yet, so I simply don't know. Please try to find the answer elsewhere or come back in May 2025, when this bachelor thesis will be completed!".split(" ")
    metadata = {
        "score": 0.8,
        "link": "path/to/some/resource.pptx",
        "context": "context of the message"
    }

    for index, part in enumerate(response):
        chunk = {
            "text": part + " ",
            "metadata": metadata if index == len(response) - 1 else None
        }
        yield json.dumps(chunk) + "\n"
        await asyncio.sleep(0.1)

@app.post("/message-streaming")
async def send_message(msg: Message):
    return StreamingResponse(stream_response(msg.text), media_type="application/json")
