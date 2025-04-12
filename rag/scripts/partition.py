from unstructured.partition.text import partition_text

file_path = "/Users/adamvalik/Downloads/test-wiki/wiki_01.txt"

elements = partition_text(filename=file_path)

# group elements for each title
articles = []
current_article = None
for el in elements:
    if el.category == "Title":
        if current_article is not None:
            articles.append(current_article)
        current_article = el.text + "\n\n"   
    else:
        current_article += el.text + "\n\n"
    
print(f"Number of articles: {len(articles)}")
print(f"{articles[1]}")
    