import os
import openai

class Rewriter:
    CHATHISTORY_SIZE = 3  # number of turns to consider in chat history
    
    @staticmethod
    def rewrite(query: str) -> str:        
        prompt = (
            "You are a query rewriting assistant in a Retrieval-Augmented Generation (RAG) system that uses both "
            "semantic and keyword-based search (hybrid retrieval).\n\n"
            
            "Your task is to rewrite user queries to improve retrieval performance by:\n"
            "- Making the query **more specific, structured, and searchable**.\n"
            "- Emphasizing **important keywords or phrases** that are likely to appear in source documents.\n"
            "- Removing filler phrases like 'tell me about', 'please explain', 'can you describe', etc.\n"
            "- Avoiding full-sentence questions unless absolutely necessary.\n"
            "- Keeping the rewritten query as **concise and retrieval-friendly** as possible.\n"
            "- Never adding assumptions or new topics not present in the original query.\n"
            "- If the query is nonsensical, return it unchanged.\n\n"
            
            "Examples:\n"
            "- Input: 'Tell me something about AI agents' → Output: 'AI agents overview'\n"
            "- Input: 'Can you explain vector databases in machine learning?' → Output: 'vector databases in machine learning'\n"
            "- Input: 'asldkj123' → Output: 'asldkj123'\n"
        )
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "developer", "content": prompt},
                {"role": "user", "content": query}
            ]
        )
        
        return response.choices[0].message.content.strip()        
    
    @staticmethod
    def rewrite_with_history(query: str, history: list[str]) -> str:
        prompt = (
            "You are a query rewriting assistant in a Retrieval-Augmented Generation (RAG) system that uses both "
            "semantic and keyword-based search (hybrid retrieval).\n\n"
            
            "Your task is to rewrite user queries to improve retrieval performance by:\n"
            "- Keep the rewritten query semantically equivalent to the original while keeping the keywords.\n"
            "- Do NOT add information or assumptions not present in the original query or context.\n"
            "- If the query is nonsensical, too short, or unrewritable, just return it unchanged.\n"
        )

        if history:
            history_text = "\n\n".join(history[-Rewriter.CHATHISTORY_SIZE:])
            prompt += (
                "The user query may be a follow-up question. "
                "Use the recent chat history below **only to resolve ambiguous or incomplete queries**. "
                "Recent Chat History:\n\n"
                f"{history_text}"
            )
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "developer", "content": [{"type": "text", "text": prompt}]},
                {"role": "user", "content": [{"type": "text", "text": query}]}
            ]
        )
        
        return response.choices[0].message.content.strip()    
    
if __name__ == "__main__":
    # demonstration
    from dotenv import load_dotenv
    from utils import color_print

    load_dotenv()
    query = "hey heay how ya doin."
    color_print("Original query: ", additional_text=query)
    color_print("-"*50, color="yellow")
    
    rewritten_query = Rewriter().rewrite(query)
    color_print("Rewritten query: ", additional_text=rewritten_query)