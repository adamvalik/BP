
class Rewriter:
    CHATHISTORY_SIZE = 3  # number of turns to consider in chat history
    
    @staticmethod
    def rewrite(query: str, history: list[str] = None) -> str:
        import os
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        prompt = (
            "You are a query rewriting assistant in a retrieval-based system (RAG). "
            "Your task is to rephrase the user query for optimal retrieval. "
            "If the input is nonsensical, return it unchanged. "
        )

        if history:
            history_text = "\n\n".join(history[-Rewriter.CHATHISTORY_SIZE:])
            prompt += (
                "Use the following chat history to understand the context of the query in case of follow-up question:\n"
                f"{history_text}\n"
            )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "developer", "content": prompt},
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