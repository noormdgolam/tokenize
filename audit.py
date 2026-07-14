import os, json, glob

def check_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    return {
        'title': '<title>' in content,
        'description': 'name="description"' in content,
        'h1': '<h1' in content,
        'size': len(content)
    }

html_files = glob.glob('*.html')
print(f"Total HTML files: {len(html_files)}")

articles_file = '_src/_data/articles.json'
with open(articles_file, 'r', encoding='utf-8') as f:
    articles = json.load(f)
print(f"Total articles in JSON: {len(articles)}")

print("Index check:", check_file('index.html'))
article_path = articles[-1]['slug'] + '.html'
print(f"Article check ({article_path}):", check_file(article_path))
