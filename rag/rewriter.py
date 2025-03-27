
class Rewriter:
    
    @staticmethod
    def rewrite(query: str) -> str:
        """using openai's gpt model, rewrite the query"""
        # load the openai model
        import os
        import openai
        
        model = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        dev_message = (
            "You are a query rewriting assistant in a retrieval-based system (RAG). "
            "Your task is to rephrase user queries to improve retrieval quality for both semantic and keyword search. "
            "Ensure the rewritten query preserves the original intent, improves clarity, and is more specific if possible. "
            "If the query is nonsensical or unrewritable (e.g. random characters or very short), return it unchanged. "
            "Do NOT add keywords or assumptions beyond the user's input.\n\n"
            "Examples:\n"
            "- Input: 'how does law work usa' → Output: 'legal system in the United States'\n"
            "- Input: 'asdkljwe' → Output: 'asdkljwe'\n"
        )

        response = model.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": dev_message},
                {"role": "user", "content": query}
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