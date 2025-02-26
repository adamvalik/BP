import pytest
from vector_store import VectorStore

# test the hybrid search on dataset from:
# https://www.kaggle.com/datasets/jensenbaxter/10dataset-text-document-classification

# query + expected most relevant document
queries_and_expected = [
    ("what were the potential risks for shareholders in a proposed financial merger?", "business_77.txt"),
    ("what impact did Howl's Moving Castle have on box office?", "entertainment_78.txt"),
    ("how do phthalates end up in food products?", "food_85.txt"),
    ("what should I learn to get started with graphic design?", "graphics_9.txt"),
    ("how did the balance of power strategies contribute to the fragility of peace in Europe before WW1?", "historical_89.txt"),
    ("what are the side effects of Depo Provera", "medical_645.txt"),
    ("how did Michael Howard plan to fund tax cuts during his leadership?", "politics_271.txt"),
    ("is there a food named after space?", "space_62.txt"),
    ("who is Mido?", "sport_100.txt"),
    ("Linux investment strategies", "technologie_12.txt"),
    ("", "No results found"),  # test empty query
    ("!!!???", "No results found"),  # special characters
]

@pytest.fixture(scope="module")
def vector_store():
    store = VectorStore()
    yield store
    store.close()

# utility function to print debug info
def print_debug_info(query, expected_filename, objects):
    print("\n--- Debug Info ---")
    print(f"Query: {query}")
    print(f"Expected: {expected_filename}")
    if objects:
        print(f"Total Results: {len(objects)}")
        for obj in objects:
            print(f"Score: {obj.metadata.score} | Explain Score: {obj.metadata.explain_score}")
            print(f"Filename: {obj.properties['filename']}")
            print(f"Text Snippet: {obj.properties['text'][:100]}...")
            print("-------------------------------")

@pytest.mark.parametrize("query, expected_filename", queries_and_expected)
def test_query_hybrid_exact(vector_store, query, expected_filename):
    """Test for exact top-1 match"""
    objects = vector_store.hybrid_search(query, k=1)
    
    if not objects:
        assert expected_filename == "No results found", f"Expected '{expected_filename}' for '{query}' but found nothing."
    else:
        print_debug_info(query, expected_filename, objects)
        filename = objects[0].properties["filename"]
        assert filename == expected_filename, f"Exact Mismatch for '{query}': Expected '{expected_filename}', found {filename}"    
    
@pytest.mark.parametrize("query, expected_filename", queries_and_expected)
def test_query_hybrid_autocut(vector_store, query, expected_filename):
    """Test with autocut method"""
    objects = vector_store.hybrid_search_autocut(query, k=1)
    
    if not objects:
        assert expected_filename == "No results found", f"Expected '{expected_filename}' for '{query}' but found nothing."
    else:
        print_debug_info(query, expected_filename, objects)
        filenames = [obj.properties["filename"] for obj in objects]
        assert expected_filename in filenames, f"Autocut Mismatch for '{query}': Expected '{expected_filename}', not found in {filenames}"

@pytest.mark.parametrize("query, expected_filename", queries_and_expected)
def test_query_hybrid_top3(vector_store, query, expected_filename):
    """Test for top-3 relevance ranking"""
    objects = vector_store.hybrid_search(query, k=3)
    
    if not objects:
        assert expected_filename == "No results found", f"Expected '{expected_filename}' for '{query}' but found nothing."
    else:
        print_debug_info(query, expected_filename, objects)
        filenames = [obj.properties["filename"] for obj in objects]
        assert expected_filename in filenames, f"Top-3 Mismatch for '{query}': Expected '{expected_filename}', not found in {filenames}"

@pytest.mark.parametrize("query, expected_filename", queries_and_expected)
def test_query_hybrid_autocut_top3(vector_store, query, expected_filename):
    """Test for top-3 autocut relevance ranking"""
    objects = vector_store.hybrid_search_autocut(query, k=3)
    
    if not objects:
        assert expected_filename == "No results found", f"Expected '{expected_filename}' for '{query}' but found nothing."
    else:
        print_debug_info(query, expected_filename, objects)
        filenames = [obj.properties["filename"] for obj in objects]
        assert expected_filename in filenames, f"Top-3 Autocut Mismatch for '{query}': Expected '{expected_filename}', not found in {filenames}"
