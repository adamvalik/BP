from document_processor import DocumentProcessor
import os

TEST_FOLDER = "txt-dataset/food"
FROM = 1
TO = 10

# ----------------------------------------------------------------------------------------------
files = os.listdir(TEST_FOLDER)
files.sort(key=lambda x: int(x.split(".")[0].split((TEST_FOLDER.split("/")[-1]).join("_"))[1]))

for i, file_name in enumerate(files, start=1):
    if FROM <= i <= TO:
        file_path = os.path.join(TEST_FOLDER, file_name)
        if os.path.isfile(file_path):
            document_processor = DocumentProcessor(file_path)
            document_processor.process(verbose=True)
        elif os.path.isdir(file_path):
            print(f"Skipping directory: {file_path}")