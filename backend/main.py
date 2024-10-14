from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# response model
class ResponseModel(BaseModel):
    reply_msg: str
    metadata: dict

# incoming message model
class Message(BaseModel):
    text: str

@app.post("/send-message")
async def send_message(message: Message):
    user_message = message.text
    response = f"You said: {user_message}. OK, well done, that's all for now!"
    metadata = {
        "score": 0.8,
        "link": "path/to/some/resource.pptx",
        "context": "context of the message"
    }
    return ResponseModel(reply_msg=response, metadata=metadata)