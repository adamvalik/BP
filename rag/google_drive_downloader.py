from operator import sub
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
import os
import uuid
import time

class GoogleDriveDownloader:
    # folder id can be found in the URL of the folder in Google Drive
    FOLDER_ID = "1tnzT6UY-tW9Q3z4EE-1wnkvof4IIjnAr"
    NGROK_URL = "https://7d0b-147-251-15-54.ngrok-free.app/webhook" # /webhook endpoint in FastAPI
    CREDENTIALS_FILE = "credentials.json"

    def __init__(self, download_path: str = "downloads"):
        self.file_cnt = 0
        self.download_path = download_path

        # ensure download path exists
        self.ensure_download_path()

        # load Google Drive API credentials
        self.creds = service_account.Credentials.from_service_account_file(
            self.CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build("drive", "v3", credentials=self.creds)
        
    def ensure_download_path(self):
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def list_files_in_folder(self, folder_id):
        query = f"'{folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        return results.get("files", [])


    def download_file(self, file_id: str, file_name: str, folder_path: str):
        request = self.service.files().get_media(fileId=file_id)
        file_path = os.path.join(folder_path, file_name)
        
        with open(file_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            self.file_cnt += 1
            
    def download_file_full_path(self, file_id: str, full_path: str):
        request = self.service.files().get_media(fileId=file_id)
        
        with open(full_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                
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

    def download_all_files(self):
        print(f"Starting download for folder: {self.FOLDER_ID}")
        self.file_cnt = 0
        self.download_folder(self.FOLDER_ID, self.download_path)
        print("\033[32m"+f"Downloaded {self.file_cnt} files to {self.download_path}"+"\033[0m")

    def start_watch_folder(self, folder_id):
        body = {
            "id": str(uuid.uuid4()),
            "type": "web_hook",
            "address": self.NGROK_URL,
            "params": {
                "ttl": "3600"  # 1 hour
            }
        }
        request = self.service.files().watch(fileId=folder_id, body=body)
        response = request.execute()
        print("Watch response:", response)

    def list_subfolders(self, folder_id):
        subfolders = []
        query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get("files", [])

        for folder in folders:
            subfolder_id = folder["id"]
            subfolder_name = folder["name"]
            print(f"Found subfolder: {subfolder_name} ({subfolder_id})")
            subfolders.append(subfolder_id)

            # recursively list subfolders
            subfolders.extend(self.list_subfolders(subfolder_id))
        
        return subfolders

    def start_watch(self):
        self.start_watch_folder(self.FOLDER_ID)
        time.sleep(1)

        # watch also all subfolders
        subfolders = self.list_subfolders(self.FOLDER_ID)
        for subfolder_id in subfolders:
            self.start_watch_folder(subfolder_id)
            time.sleep(1)
            
    def get_full_path(self, file_id):
        # this method creates problems
        path_parts = []
        current_id = file_id

        while True:
            try:
                file_metadata = self.service.files().get(fileId=current_id, fields="id, name, parents").execute()
                name = file_metadata["name"]
                parents = file_metadata.get("parents", [])

                path_parts.insert(0, name)

                if not parents:
                    break
                
                current_id = parents[0]
                
                if current_id == self.FOLDER_ID:
                    break
            
            except Exception as e:
                print(f"Error getting full path: {e}")
                break

        # join the parts to form the full path
        full_path = os.path.join(self.download_path, *path_parts)
        print(f"Full path: {full_path}")
        return full_path

    def download_or_update_file(self, file_id):
        try:            
            self.ensure_download_path()
            full_path = self.get_full_path(file_id)
            self.download_file_full_path(file_id, full_path)
            
            print(f"File downloaded or updated: {full_path}")

        except Exception as e:
            print(f"Error downloading file: {e}")

    def delete_local_file(self, file_id):
        pass
    # this is not working as I can not get the full path of the file that was deleted
    #     try:
    #         # full_path = self.get_full_path(file_id)
            
    #         if os.path.exists(full_path):
    #             os.remove(full_path)
    #             print(f"Local file deleted: {full_path}")
    #         else:
    #             print(f"Local file not found: {full_path}")

    #     except Exception as e:
    #         print(f"Error deleting file: {e}")
