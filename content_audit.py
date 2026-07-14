import json
import re

def check_low_quality():
    print("Starting Content Quality Audit...")
    try:
        with open('_src/_data/articles.json', 'r', encoding='utf-8') as f:
            articles = json.load(f)
    except Exception as e:
        print("Error loading articles:", e)
        return

    low_word_count_threshold = 200 # Just the body content
    ai_cliches = [
        "in conclusion", "it is important to note", "delve into", "testament to", 
        "tapestry", "moreover", "furthermore", "in summary", "landscape"
    ]
    
    issues_found = []
    
    for article in articles:
        slug = article.get('slug', 'unknown')
        content = article.get('content', '')
        excerpt = article.get('excerpt', '')
        faqs = article.get('faqs', [])
        takeaways = article.get('key_takeaways', [])
        
        # 1. Word Count Check
        words = len(re.findall(r'\b\w+\b', content))
        if words < low_word_count_threshold:
            issues_found.append({
                "slug": slug,
                "issue": f"Low word count in body ({words} words)"
            })
            
        # 2. AI Cliche Check
        content_lower = content.lower()
        found_cliches = [cliche for cliche in ai_cliches if cliche in content_lower]
        if len(found_cliches) > 2: # more than 2 cliches might mean it's poorly prompted
            issues_found.append({
                "slug": slug,
                "issue": f"High AI cliché usage: {', '.join(found_cliches)}"
            })
            
        # 3. Missing Enriched Data
        if not faqs:
            issues_found.append({
                "slug": slug,
                "issue": "Missing FAQs"
            })
        if not takeaways:
            issues_found.append({
                "slug": slug,
                "issue": "Missing Key Takeaways"
            })
            
        # 4. Short Excerpt
        if len(excerpt.split()) < 10:
            issues_found.append({
                "slug": slug,
                "issue": f"Excerpt too short ({len(excerpt.split())} words)"
            })
            
        # 5. Missing Subheadings
        if "<h2>" not in content and "<h3>" not in content:
            issues_found.append({
                "slug": slug,
                "issue": "Missing H2/H3 subheadings in content body"
            })

    print(f"\nAudit complete. Checked {len(articles)} articles.")
    print(f"Total quality issues flagged: {len(issues_found)}")
    
    if issues_found:
        print("\n--- Low Quality Flags ---")
        # Group by issue
        from collections import defaultdict
        grouped = defaultdict(list)
        for issue in issues_found:
            grouped[issue['issue']].append(issue['slug'])
            
        for issue_text, slugs in grouped.items():
            print(f"\n[!] {issue_text} ({len(slugs)} articles):")
            for slug in slugs[:5]: # show up to 5 examples
                print(f"    - {slug}")
            if len(slugs) > 5:
                print(f"    ...and {len(slugs) - 5} more.")
    else:
        print("\nExcellent! No low quality content markers found.")

if __name__ == "__main__":
    check_low_quality()
