from document_processor import DocumentProcessor
import os
from dotenv import load_dotenv
load_dotenv()

TEST_FOLDER = "/Users/adamvalik/Downloads/test-wiki"
FROM = 9   
TO = 9

# ----------------------------------------------------------------------------------------------
# files = os.listdir(TEST_FOLDER)
# files.remove(".DS_Store")
# files.sort(key=lambda x: int(x.split("_")[-1].split(".")[0]))

# for i, file_name in enumerate(files):
#     if FROM <= i <= TO:
#         file_path = os.path.join(TEST_FOLDER, file_name)
#         if os.path.isfile(file_path):
#             document_processor = DocumentProcessor(filename=file_path)
#             document_processor.process(verbose=True)
#         elif os.path.isdir(file_path):
#             print(f"Skipping directory: {file_path}")

document_processor = DocumentProcessor(filename="/Users/adamvalik/Downloads/samples/multipage_agents.pdf")
document_processor.process(verbose=True)
print(f"File processed successfully.")