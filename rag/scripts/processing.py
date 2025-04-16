from document_processor import DocumentProcessor
import os
from dotenv import load_dotenv
from tqdm import tqdm
load_dotenv()

TEST_FOLDER = "/Users/adamvalik/Downloads/test-wiki"
FROM = 0
TO = 29

# ----------------------------------------------------------------------------------------------
files = os.listdir(TEST_FOLDER)
files.remove(".DS_Store")
files.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))

num_chunks = []

for i, file_name in tqdm(enumerate(files), total=len(files)):
    # if FROM <= i <= TO:
        file_path = os.path.join(TEST_FOLDER, file_name)
        if os.path.isfile(file_path):
            document_processor = DocumentProcessor(filename=file_path)
            chunks = document_processor.process(verbose=True)
            num_chunks.append(len(chunks))
        elif os.path.isdir(file_path):
            print(f"Skipping directory: {file_path}")

# document_processor = DocumentProcessor(filename="/Users/adamvalik/Downloads/samples/multipage_agents.pdf")
# document_processor.process(verbose=True)
# print(f"File processed successfully.")

print("\n____________________")
print(f"Number of files: {len(files)}")
print(f"Number of chunks: {sum(num_chunks)}")
print(f"Average number of chunks per file: {sum(num_chunks) / len(num_chunks)}")