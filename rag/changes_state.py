import json
import os

PAGE_TOKEN_FILE = "page_token.json"

def load_page_token() -> str:
    """
    Load the saved page token from disk, or return None if not found.
    """
    if not os.path.exists(PAGE_TOKEN_FILE):
        return None
    with open(PAGE_TOKEN_FILE, "r") as f:
        data = json.load(f)
        return data.get("pageToken")

def save_page_token(token: str):
    """
    Save the page token to disk so we can pick up where we left off.
    """
    with open(PAGE_TOKEN_FILE, "w") as f:
        json.dump({"pageToken": token}, f)
