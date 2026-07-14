import os, json, glob
from bs4 import BeautifulSoup

def run_audit():
    with open('_src/_data/articles.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    issues = []
    total_words = 0
    
    for article in articles:
        slug = article['slug']
        file_path = f"{slug}.html"
        if not os.path.exists(file_path):
            issues.append(f"Missing HTML: {slug}")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            article_body = soup.find('div', class_='article-content')
            if article_body:
                words = len(article_body.text.split())
                total_words += words
                if words < 100:
                    issues.append(f"{slug}: Low word count ({words} words)")
            else:
                issues.append(f"{slug}: Missing article-content class")
                
            # Quick check JSON-LD
            scripts = soup.find_all('script', type='application/ld+json')
            if len(scripts) < 2:
                issues.append(f"{slug}: Missing Schema JSON-LD")

    avg_words = total_words / len(articles) if articles else 0
    print(f"Audit Complete. Issues found: {len(issues)}")
    print(f"Average body word count per article: {avg_words:.0f}")
    if issues:
        for i in issues[:10]: print(i)

if __name__ == "__main__":
    run_audit()
