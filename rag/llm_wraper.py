import openai
import os
from chunk import Chunk
from typing import List

class LLMWrapper:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def construct_messages(self, user_query: str, chunks: List[Chunk]):
        dev_message = (
            "You are a knowledgeable assistant that answers questions using the provided context. "
            "For each piece of information you use, cite the source filename in brackets. "
            "Only use the information from the context provided. "
            "If the information is insufficient, state that explicitly."
        )
        
        messages = [
            {
                "role": "developer",
                "content": [
                    {"type": "text", "text": dev_message},
                ] 
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Question: {user_query}. The context is as follows:"}
                ]
            }       
        ]
        
        for chunk in chunks:
            messages[1]["content"].append({
                "type": "text",
                "text": f"Context from file: {chunk.filename}\nText: {chunk.text}"
            })
        
        return messages

    def get_stream_response(self, query: str, chunks: List[Chunk]):
        messages = self.construct_messages(query, chunks)
        
        try:
            stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_completion_tokens=300,
                stream=True
            )
            
            # streaming response (yield each response as it arrives)
            for response in stream:
                if response.choices[0].delta.content is not None:
                    yield response.choices[0].delta.content

        except openai.error.OpenAIError as e:
            yield f"[ERROR] OpenAI API Error: {e}"
