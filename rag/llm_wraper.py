import openai
import os
from chunk import Chunk
from typing import List

class LLMWrapper:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def construct_messages(self, user_query: str, chunks: List[Chunk]):
        dev_message = (
            "You are a generator in a retrieval-based system (RAG). "
            "Your task is to answer the user's question using the information from the context. "
            "Here are retrieved relevant text chunks which form the context:\n"
        )
        
        for chunk in chunks:
            dev_message += (
                f"File: {chunk.filename}\n"
                f"Title: {chunk.title if chunk.title else 'Untitled'}\n"
                f"Text: {chunk.text}\n\n"
            )
        
        dev_message += (
            "Only use the information from the context provided. "
            "For each information you use, provide a citation to the source in format: [File: {filename}, Section: {title}]. "
            "If the title is 'Untitled', omit the title in the citation completely.\n"
            "If the provided context is insufficient to answer the question, explicitly respond with: "
            "'My knowledge base does not provide information to answer this question.' \n"
            "Structure responses clearly in markdown style. "
            "Limit responses to **3 sentences** unless further clarification is required."
        )
        
        return [
            {"role": "developer", "content": dev_message},
            {"role": "user", "content": user_query}
        ]
        

    def get_stream_response(self, query: str, chunks: List[Chunk]):
        messages = self.construct_messages(query, chunks)
        
        try:
            # streaming response (yield each response as it arrives)
            for response in self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.2,
                stream=True
            ):
                if response.choices[0].delta.content is not None:
                    yield response.choices[0].delta.content

        except openai.APIStatusError as e:
            yield f"[ERROR] OpenAI API Error: {e.status_code} - {e.response}"
            
    def get_response(self, query: str, chunks: List[Chunk]):
        messages = self.construct_messages(query, chunks)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.2,
            )
            
            return response.choices[0].message.content
        
        except openai.APIStatusError as e:
            return f"[ERROR] OpenAI API Error: {e.status_code} - {e.response}"


