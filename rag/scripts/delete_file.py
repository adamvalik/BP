from vector_store import VectorStore

v = VectorStore()

v.delete_document("/Users/adamvalik/Downloads/samples/sample_ai_agents.docx")

v.close()