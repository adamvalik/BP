from unstructured.partition.text import partition_text
import os
from tqdm import tqdm

dir_path = "/Users/adamvalik/Downloads/test-wiki"

num_articles = 0
for filename in tqdm(os.listdir(dir_path)):
    if not filename.endswith(".txt"):
        continue
    file_path = os.path.join(dir_path, filename)
    elements = partition_text(filename=file_path)
    
    for i, el in enumerate(elements):    
        # remove the titles if they are not needed
        if el.category == "Title" and el.text.endswith((":", ".", ">")):
            el.category = "NarrativeText"
        # title is followed by another title, categorize it as narrative text, it is likely a list of items
        if el.category == "Title" and i + 1 < len(elements) and elements[i + 1].category == "Title":
            el.category = "NarrativeText"
            j = i + 1
            while i < len(elements) and elements[j].category == "Title":
                elements[j].category = "NarrativeText"
                j += 1
        # remove formulas as titles
        if el.category == "Title" and el.text.split("_")[0] == "formula":
            el.category = "NarrativeText"

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

    num_articles += len(articles)
        
        
print(f"Total number of articles: {num_articles}")
    