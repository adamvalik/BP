from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the structure of the incoming message using Pydantic
class Message(BaseModel):
    text: str

# Simple API route to receive a message and send a reply
@app.post("/send-message")
async def send_message(message: Message):
    user_message = message.text
    # Simple logic to generate a reply
    bot_reply = f"You said: {user_message}. Here's my reply!"
    return {"reply": bot_reply}
