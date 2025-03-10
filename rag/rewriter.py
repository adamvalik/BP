import openai
import os

class Rewriter:
    
    @staticmethod
    def rewrite(query: str) -> str:
        """using openai's gpt model, rewrite the query"""
        # load the openai model
        model = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        dev_message = (
            "Rewrite the query to optimize for retrieval. "
            "If a query is real nonsense, just return the original query. "
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