import pytest
from vector_store import VectorStore
from reranker import Reranker

# query + expected most relevant document
queries_and_expected = [
    ("Why is it risky to hike alone without experience?", "/Users/adamvalik/Downloads/test-wiki/wiki_10.txt_554"),
    ("How does the ovum travel from the ovary to the uterus?", "/Users/adamvalik/Downloads/test-wiki/wiki_10.txt_703"),
    ("When did McDonald's switch from beef tallow to vegetable oil for fries?", "/Users/adamvalik/Downloads/test-wiki/wiki_10.txt_707"),
    ("When was the Arab League officially created?", "/Users/adamvalik/Downloads/test-wiki/wiki_10.txt_804"),
    ("Does acetaminophen use in early childhood increase the risk of asthma?", "/Users/adamvalik/Downloads/test-wiki/wiki_10.txt_841"),
    ("How did Edward Jenner prove that cowpox could protect against smallpox?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_0"),
    ("Why do some artists choose independent labels over major record companies?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_9"),
    ("Who was the first U.S. president born as an American citizen after 1776?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_46"),
    ("What is the difference between sexual orientation and sexual preference?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_76"),
    ("How did rugby football get its name and origin?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_114"),
    ("What does the prefix 'anti' mean in words like 'antisocial' or 'anti-glare'?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_120"),
    ("What medical option exists for women with severe semen allergies who want to get pregnant?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_137"),
    ("What was the significance of the Supreme Court case Brown v. Board of Education?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_147"),
    ("What is symmetric multiprocessing in computer systems?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_166"),
    ("What talk shows has Rosie O'Donnell hosted during her career?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_181"),
    ("What are chalkboard gags and couch gags in The Simpsons?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_215"),
    ("What is the largest known species of turtle, living or extinct?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_244"),
    ("When did the Taliban regain full control of Afghanistan after 2001?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_263"),
    ("Why is titanium used in aerospace engineering instead of steel or aluminum?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_274"),
    ("Why do Hebrew learners need to study grammar before reading without vowels?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_276"),
    ("Why did Sega choose Sonic the Hedgehog as their mascot instead of Doctor Eggman?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_286"),
    ("How did the game 'Final Fantasy Adventure' relate to the Mana series?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_290"),
    ("How did Operation Fortitude contribute to the success of the Normandy invasion?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_399"),
    ("Why was the Fender Precision Bass considered an improvement over the double bass?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_424"),
    ("What are the major challenges facing the education system in Nepal?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_432"),
    ("Why did Terry Fox have his leg amputated?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_441"),
    ("How does the diaphragm help a person breathe in and out?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_471"),
    ("What adaptations help cacti survive in hot, dry climates?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_484"),
    ("What happened when Viacom and CBS merged in 2019?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_494"),
    ("Why did Margaret Thatcher resign as Prime Minister in 1990?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_501"),
    ("What was groundbreaking about Wendy Carlos’s album 'Switched on Bach'?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_521"),
    ("Why does Greenland have the lowest population density in the world?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_546"),
    ("How does Tony Manero try to escape his life in Saturday Night Fever?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_548"),
    ("How did Henry Ford’s assembly line change manufacturing?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_551"),
    ("Why did the American colonies decide to declare independence from Great Britain in 1776?", "/Users/adamvalik/Downloads/test-wiki/wiki_09.txt_555"),
]

@pytest.fixture(scope="module")
def vector_store():
    store = VectorStore()
    yield store
    store.close()

@pytest.mark.parametrize("query, expected_chunk_id", queries_and_expected)
def test_query_hybrid_exact(vector_store, query, expected_chunk_id):
    chunks = vector_store.hybrid_search(query, k=3, autocut=True)
    reranked_chunks = Reranker.rerank(query, chunks)
    
    if not reranked_chunks:
        assert False, "Found nothing."
    else:
        assert expected_chunk_id == reranked_chunks[0].chunk_id, f"[exact] found {reranked_chunks[0].chunk_id}"    
        assert expected_chunk_id in [c.chunk_id for c in reranked_chunks], f"[context] found {[c.chunk_id for c in reranked_chunks]}"

