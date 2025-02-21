from googleapiclient.discovery import build
from google.oauth2 import service_account
from tqdm import tqdm
import os

# later will be updated to DocumentManager
# TODO: recursive downloading in subfolders

class GoogleDriveDownloader:
    # folder id can be found in the URL of the folder in Google Drive
    FOLDER_ID = "1tnzT6UY-tW9Q3z4EE-1wnkvof4IIjnAr"
    CREDENTIALS_FILE = "credentials.json"

    def __init__(self, download_path: str = "downloads"):
        self.download_path = download_path

        # ensure download path exists
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

        # load Google Drive API credentials
        self.creds = service_account.Credentials.from_service_account_file(
            self.CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build("drive", "v3", credentials=self.creds)

    def list_files_in_folder(self):
        query = f"'{self.FOLDER_ID}' in parents and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        return results.get("files", [])

    def download_file(self, file_id: str, file_name: str):
        request = self.service.files().get_media(fileId=file_id)
        file_path = os.path.join(self.download_path, file_name)

        with open(file_path, "wb") as f:
            f.write(request.execute())

    def download_all_files(self):
        files = self.list_files_in_folder()

        if not files:
            print("No files found in the folder.")
            return

        print(f"Found {len(files)} files.")

        for file in tqdm(files, desc=f"Downloading files to {self.download_path}", unit="file"):
            self.download_file(file["id"], file["name"])
