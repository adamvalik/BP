# File: changes_state.py - State management for page tokens 
# Author: Adam Valík <xvalik05@stud.fit.vut.cz>

import json
import os

PAGE_TOKEN_FILE = "page_token.json"

def load_page_token() -> str:
    if not os.path.exists(PAGE_TOKEN_FILE):
        return None
    with open(PAGE_TOKEN_FILE, "r") as f:
        data = json.load(f)
        return data.get("pageToken")

def save_page_token(token: str):
    with open(PAGE_TOKEN_FILE, "w") as f:
        json.dump({"pageToken": token}, f)
