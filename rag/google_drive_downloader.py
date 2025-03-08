from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
from document_processor import DocumentProcessor
from vector_store import VectorStore
from utils import color_print
from changes_state import load_page_token, save_page_token
import io
import os
import re
import uuid
import json

class GoogleDriveDownloader:
    NGROK_URL = "https://d57f-147-229-117-1.ngrok-free.app/webhook" # /webhook endpoint in FastAPI
    CREDENTIALS_FILE = "credentials.json"
    ROOT_ID_FILE = "root_url.json"

    def __init__(self):        
        # load Google Drive API credentials
        self.creds = service_account.Credentials.from_service_account_file(
            self.CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build("drive", "v3", credentials=self.creds)
        
    def save_url(self, drive_url: str):
        with open(self.ROOT_ID_FILE, "w") as f:
            json.dump({"root_url": drive_url}, f)
            
    def get_url(self):
        if not os.path.exists(self.ROOT_ID_FILE):
            return None
        with open(self.ROOT_ID_FILE, "r") as f:
            data = json.load(f)
            return data.get("root_url")
    
    def get_root_id(self):
        url = self.get_url()
        return self.extract_folder_id(url) if url else None
        
    @staticmethod
    def extract_folder_id(drive_url: str) -> str:
        pattern = re.compile(r'/folders/([^/?]+)')
        match = pattern.search(drive_url)
        if match:
            return match.group(1)
        return None
        
    def list_files_in_folder(self, folder_id):
        query = f"'{folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        return results.get("files", [])
    
    # ----------------------------------------------------------------------------------------------------
    def download_file(self, file_id: str, file_name: str, folder_path: str):
        request = self.service.files().get_media(fileId=file_id)
        file_path = os.path.join(folder_path, file_name)
        
        with open(file_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            self.file_cnt += 1
            
    def download_folder(self, folder_id, parent_path):
        files = self.list_files_in_folder(folder_id)

        if not files:
            print(f"No files found in folder {folder_id}.")
            return

        if not os.path.exists(parent_path):
            os.makedirs(parent_path)

        for file in files:
            file_name = file["name"]
            file_id = file["id"]
            mime_type = file["mimeType"]

            # recursively download subfolder's contents
            if mime_type == "application/vnd.google-apps.folder":
                subfolder_path = os.path.join(parent_path, file_name)
                print(f"Entering folder: {file_name}")
                self.download_folder(file_id, subfolder_path)
                print(f"Returning to folder: {parent_path}")
            else:
                print(f"Downloading file: {file_name}")
                self.download_file(file_id, file_name, parent_path)
    
    def download_all_files(self, download_path: str = "downloads"):
        # get the root folder ID
        root_folder_id = self.get_root_id()
        
        if not root_folder_id:
            color_print("Failed to obtain root folder ID. Provide URL of root folder.", "red")
            return
        
        print(f"Starting download for folder: {root_folder_id}")
        self.file_cnt = 0
        self.download_folder(root_folder_id, download_path)
        color_print(f"Downloaded {self.file_cnt} files to {download_path}")

    # ----------------------------------------------------------------------------------------------------
    def download_file_in_memory(self, file_id: str) -> bytes:
        request = self.service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
        self.file_cnt += 1

        file_buffer.seek(0)  # reset pointer
        return file_buffer.read()
                        
    def ingest_folder(self, folder_id, parent_path, vector_store: VectorStore):
        color_print(f"\nIngesting documents from directory: {parent_path}", color="blue")
        files = self.list_files_in_folder(folder_id)

        if not files:
            print(f"No files found in folder {folder_id}.")
            return

        buffer = []
        for file in files:
            filename = file["name"]
            file_id = file["id"]
            mime_type = file["mimeType"]

            # recursively download subfolder's contents
            if mime_type == "application/vnd.google-apps.folder":
                subfolder_path = os.path.join(parent_path, filename)
                print(f"Entering folder: {filename}")
                self.ingest_folder(file_id, subfolder_path, vector_store)
                print(f"Returning to folder: {parent_path}")
            else:
                print(f"Downloading file: {filename}")
                if vector_store.document_exists(file_id):
                    # avoid duplicate ingestion
                    color_print(f"Document {filename} already exists in the vector store. Skipping ingestion...", color="yellow")
                else:
                    bytes = self.download_file_in_memory(file_id)
                    document_processor = DocumentProcessor(filename=filename, file=bytes, file_id=file_id)
                    chunks = document_processor.process()
                    if chunks:
                        buffer.extend(chunks)
        
        if buffer:
            vector_store.insert_chunks_batch(buffer)

    def bulk_ingest(self, vector_store: VectorStore):
        # get the root folder ID
        root_folder_id = self.get_root_id()
        
        if not root_folder_id:
            color_print("Failed to obtain root folder ID. Provide URL of root folder.", "red")
            return
                
        print(f"Starting download for folder: {root_folder_id}")
        self.file_cnt = 0
        self.ingest_folder(root_folder_id, "root", vector_store)
        color_print(f"Downloaded {self.file_cnt} files and ingested them to the vector database")

    # ----------------------------------------------------------------------------------------------------
    def initialize_changes_page_token(self):
        existing_token = load_page_token()
        if existing_token:
            print(f"[Changes] Already have a page token: {existing_token}")
            return

        response = self.service.changes().getStartPageToken().execute()
        start_page_token = response.get("startPageToken")
        print(f"[Changes] Obtained start page token: {start_page_token}")
        save_page_token(start_page_token)

    def start_changes_watch(self):
        body = {
            "id": str(uuid.uuid4()),
            "type": "web_hook",
            "address": self.NGROK_URL,
            "params": {
                "ttl": "3600"  # 1 hour in seconds
            }
        }
        response = self.service.changes().watch(pageToken=load_page_token(), body=body).execute()
        print("Watch response:", response)
        return response["id"], response["resourceId"]
    
    def stop_changes_watch(self, channel_id: str, resource_id: str):
        body = {
            "id": channel_id,
            "resourceId": resource_id
        }
        self.service.channels().stop(body=body).execute()


    def sync_changes(self, vector_store: VectorStore):
        page_token = load_page_token()
        if not page_token:
            color_print("No page token found. Please initialize with `initialize_changes_page_token()` first.", "red")
            return

        next_page_token = page_token

        while True:
            response = self.service.changes().list(
                pageToken=next_page_token,
                fields="changes(fileId, file(name, mimeType, trashed)), nextPageToken, newStartPageToken"
            ).execute()

            changes = response.get("changes", [])
            for change in changes:
                self.handle_change(change, vector_store)

            # If there's more pages, continue
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                # Possibly get newStartPageToken if present, meaning we've fully synced
                new_start_page_token = response.get("newStartPageToken")
                if new_start_page_token:
                    # This is your new baseline for the next incremental sync
                    save_page_token(new_start_page_token)
                    print(f"[Changes] Sync complete. New start page token: {new_start_page_token}")
                else:
                    # Otherwise, we just re-save the last page token
                    save_page_token(page_token)
                break

            # Update our "page_token" so if something fails mid-way we won't re-process changes
            page_token = next_page_token
            save_page_token(page_token)
            
    def handle_change(self, change: dict, vector_store: VectorStore):
        """
        Decide how to handle a single change record.
        A 'change' might look like:
        {
            "fileId": "abc123",
            "file": {
                "name": "report.pdf",
                "mimeType": "application/pdf",
                "trashed": false
            }
        }
        """
        file_id = change.get("fileId")
        file_obj = change.get("file")

        # If 'file' is not in the change, it might mean the file was permanently removed.
        if not file_obj:
            # The file was removed, so remove from DB
            vector_store.delete_document(file_id)
            color_print(f"[Changes] File {file_id} was removed (no file object).", "yellow")
            return

        # Check if it was trashed
        is_trashed = file_obj.get("trashed", False)
        if is_trashed:
            vector_store.delete_document(file_id)
            color_print(f"[Changes] File {file_obj['name']} is trashed. Removed from DB.", "yellow")
            return

        # Otherwise, it's a newly created or updated file
        # We can re-download it and update our DB
        filename = file_obj["name"]
        mime_type = file_obj["mimeType"]

        # If we already have the file, remove the old version to replace it
        if vector_store.document_exists(file_id):
            vector_store.delete_document(file_id)

        # Now re-ingest
        if mime_type != "application/vnd.google-apps.folder":
            file_bytes = self.download_file_in_memory(file_id)
            doc_processor = DocumentProcessor(
                filename=filename,
                file=file_bytes,
                file_id=file_id
            )
            chunks = doc_processor.process()
            vector_store.insert_chunks(chunks)
            color_print(f"[Changes] File {filename} updated/created in DB.", "green")
        else:
            color_print(f"[Changes] Folder {filename} updated, ignoring folder ingestion.", "blue")
