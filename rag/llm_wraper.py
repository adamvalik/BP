import openai
import os
from chunk import Chunk
from typing import List

class LLMWrapper:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    @staticmethod    
    def construct_messages(user_query: str, chunks: List[Chunk]):

        dev_message = (
            "You are a factual answer generator in a Retrieval-Augmented Generation (RAG) system.\n\n"
            
            "You will receive a user query and a list of context chunks retrieved from a document store. "
            "Each chunk contains text from a specific file, with optional section titles or page numbers.\n\n"

            "Your job is to answer the user's question using **only** the provided context. "
            "Cite the sources used in your answer using the format: [File: filename, Section: title, Page: page]. "
            "If section or page is missing, omit them from the citation.\n\n"

            "**Rules:**\n"
            "- Do NOT use any knowledge outside the context.\n"
            "- Do NOT speculate or invent information.\n"
            "- If at least one chunk contains relevant information, answer using only that content.\n"
            "- Do NOT include a fallback message unless **none** of the chunks are even partially relevant.\n"
            "- Do NOT try to give an exhaustive answer — partial answers are acceptable.\n"
            "- Do NOT explain what is missing.\n"
            "- Format your answer using **markdown**, be **short and factual**, and avoid repetition.\n\n"

            "If there is truly no relevant information in any chunk, respond with:\n"
            "`My knowledge base does not provide information for this query.`\n\n"
            
            "Context:\n"
        )
        
        for chunk in chunks:
            citation = f"[File: {chunk.filename}"
            if chunk.title:
                citation += f", Section: {chunk.title}"
            if chunk.page:
                citation += f", Page: {chunk.page}"
            citation += "]"
            dev_message += (
                f"{citation}\n{chunk.text}\n\n"
            )
        
        # print("Prompt:\n", dev_message)
        return [
            {"role": "developer", "content": dev_message},
            {"role": "user", "content": user_query}
        ]

    def get_stream_response(self, query: str, chunks: List[Chunk]):
        messages = LLMWrapper.construct_messages(query, chunks)
        
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
        messages = LLMWrapper.construct_messages(query, chunks)
        
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


