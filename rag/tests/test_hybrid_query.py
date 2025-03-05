import pytest
from vector_store import VectorStore

# test the hybrid search on dataset from:
# https://www.kaggle.com/datasets/jensenbaxter/10dataset-text-document-classification

# query + expected most relevant document
queries_and_expected = [
    ("what were the potential risks for shareholders in a proposed financial merger?", "txt-dataset/business/business_77.txt"),
    ("what impact did Howl's Moving Castle have on box office?", "txt-dataset/entertainment/entertainment_78.txt"),
    ("how do phthalates end up in food products?", "txt-dataset/food/food_85.txt"),
    ("what should I learn to get started with graphic design?", "txt-dataset/graphics/graphics_9.txt"),
    ("how did the balance of power strategies contribute to the fragility of peace in Europe before WW1?", "txt-dataset/historical/historical_89.txt"),
    ("what are the side effects of Depo Provera", "txt-dataset/medical/medical_645.txt"),
    ("how did Michael Howard plan to fund tax cuts during his leadership?", "txt-dataset/politics/politics_271.txt"),
    ("is there a food named after space?", "txt-dataset/space/space_62.txt"),
    ("who is Mido?", "txt-dataset/sport/sport_100.txt"),
    ("Linux investment strategies", "txt-dataset/technologie/technologie_12.txt"),
    ("", "No results found"),  # test empty query
    ("!!!???", "No results found"),  # special characters
]

@pytest.fixture(scope="module")
def vector_store():
    store = VectorStore()
    yield store
    store.close()

# utility function to print debug info
def print_debug_info(query, expected_filename, chunks):
    print("\n--- Debug Info ---")
    print(f"Query: {query}")
    print(f"Expected: {expected_filename}")
    if chunks:
        print(f"Total Results: {len(chunks)}")
        for chunk in chunks:
            print(f"Filename: {chunk.filename}")
            print(f"Score: {chunk.score} | Explain Score: {chunk.explain_score}")
            print(f"Text Snippet: {chunk.text[:100]}...")
            print("-------------------------------")

@pytest.mark.parametrize("query, expected_filename", queries_and_expected)
def test_query_hybrid_exact(vector_store, query, expected_filename):
    """Test for exact top-1 match"""
    chunks = vector_store.hybrid_search(query, k=1)
    
    if not chunks:
        assert expected_filename == "No results found", f"Expected '{expected_filename}' for '{query}' but found nothing."
    else:
        print_debug_info(query, expected_filename, chunks)
        filename = chunks[0].filename
        assert filename == expected_filename, f"Exact Mismatch for '{query}': Expected '{expected_filename}', found {filename}"    
    
@pytest.mark.parametrize("query, expected_filename", queries_and_expected)
def test_query_hybrid_autocut(vector_store, query, expected_filename):
    """Test with autocut method"""
    chunks = vector_store.hybrid_search(query, k=1, autocut=True)
    
    if not chunks:
        assert expected_filename == "No results found", f"Expected '{expected_filename}' for '{query}' but found nothing."
    else:
        print_debug_info(query, expected_filename, chunks)
        filenames = [chunk.filename for chunk in chunks]
        assert expected_filename in filenames, f"Autocut Mismatch for '{query}': Expected '{expected_filename}', not found in {filenames}"

@pytest.mark.parametrize("query, expected_filename", queries_and_expected)
def test_query_hybrid_top3(vector_store, query, expected_filename):
    """Test for top-3 relevance ranking"""
    chunks = vector_store.hybrid_search(query, k=3)
    
    if not chunks:
        assert expected_filename == "No results found", f"Expected '{expected_filename}' for '{query}' but found nothing."
    else:
        print_debug_info(query, expected_filename, chunks)
        filenames = [chunk.filename for chunk in chunks]
        assert expected_filename in filenames, f"Top-3 Mismatch for '{query}': Expected '{expected_filename}', not found in {filenames}"

@pytest.mark.parametrize("query, expected_filename", queries_and_expected)
def test_query_hybrid_autocut_top3(vector_store, query, expected_filename):
    """Test for top-3 autocut relevance ranking"""
    chunks = vector_store.hybrid_search(query, k=3, autocut=True)
    
    if not chunks:
        assert expected_filename == "No results found", f"Expected '{expected_filename}' for '{query}' but found nothing."
    else:
        print_debug_info(query, expected_filename, chunks)
        filenames = [chunk.filename for chunk in chunks]
        assert expected_filename in filenames, f"Top-3 Autocut Mismatch for '{query}': Expected '{expected_filename}', not found in {filenames}"
