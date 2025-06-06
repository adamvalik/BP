from vector_store import VectorStore
from weaviate.classes.query import Filter

v = VectorStore()

files = ["space_35.txt","sport_99.txt","space_1.txt","sample_company.pdf","space_47.txt","sport_98.txt","intern_info.pdf"]

for file in files:
    v.collection.data.delete_many(
        where=Filter.by_property("filename").equal(file)
    )

v.close()