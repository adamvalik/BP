import openai
import os
from chunk import Chunk
from typing import List

class LLMWrapper:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def construct_messages(self, user_query: str, chunks: List[Chunk]):
        dev_message = (
            "You are an AI assistant that answers questions based on the provided context. "
            # context
            
            "Cite sources in this format: [File: {filename}, Section: {title}]. "
            "Use the section title if available, otherwise if it's 'Untitled' omit it completely.\n\n"
            
            "Only use the information from the context provided. "
            "If the information is insufficient, explicitly respond with: "
            "'My knowledge base does not provide information to answer this question.' "
            
            "Structure responses clearly in markdown style. "
            "Limit responses to **3 sentences** unless further clarification is required. "
        )
        
        messages = [
            {"role": "developer", "content": [{"type": "text", "text": dev_message}]},
            {"role": "user", "content": [{"type": "text", "text": f"Question: {user_query}. The context is as follows:\n\n"}]}       
        ]
        
        not_present = "Untitled"
        for chunk in chunks:
            messages[1]["content"].append({
                "type": "text",
                "text": f"File: {chunk.filename}\nTitle: {chunk.title if chunk.title else not_present}\nText: {chunk.text}"
            })
        
        return messages

    def get_stream_response(self, query: str, chunks: List[Chunk]):
        messages = self.construct_messages(query, chunks)
        
        try:
            stream = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_completion_tokens=300,
                stream=True
            )
            
            # streaming response (yield each response as it arrives)
            for response in stream:
                if response.choices[0].delta.content is not None:
                    yield response.choices[0].delta.content

        except openai.APIStatusError as e:
            yield f"[ERROR] OpenAI API Error:"
            yield f"Status Code: {e.status_code}"
            yield f"Response: {e.response}"
            
    def get_response(self, query: str, chunks: List[Chunk]):
        messages = self.construct_messages(query, chunks)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=300
            )
            
            return response.choices[0].message.content
        
        except openai.APIStatusError as e:
            return f"[ERROR] OpenAI API Error: {e.status_code} - {e.response}"


