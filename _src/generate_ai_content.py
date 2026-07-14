import os
import csv
import json
import time
from datetime import datetime
import google.generativeai as genai

# Configure paths
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SRC_DIR, '_data')
CSV_PATH = os.path.join(DATA_DIR, 'keywords.csv')
JSON_PATH = os.path.join(DATA_DIR, 'articles.json')

# Configure API Key (User must set this environment variable)
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY environment variable not set.")
    print("Please set it before running this script (e.g., $env:GEMINI_API_KEY='your-key').")
    exit(1)

genai.configure(api_key=API_KEY)

# Define the exact JSON schema required by our frontend
article_schema = {
    "type": "object",
    "properties": {
        "slug": {"type": "string", "description": "URL friendly slug, e.g. tokenized-real-estate-yields"},
        "title": {"type": "string", "description": "Compelling H1 title matching the keyword"},
        "category": {"type": "string", "description": "The category/hub from the input"},
        "excerpt": {"type": "string", "description": "Meta description, under 155 characters"},
        "date": {"type": "string", "description": "Publication date in YYYY-MM-DD format"},
        "key_takeaways": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Array of exactly 3 bullet points summarizing the article"
        },
        "faqs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"}
                }
            },
            "description": "Array of 2-3 highly specific FAQs and Answers for JSON-LD schema"
        },
        "content": {"type": "string", "description": "Raw HTML string containing the article body. Use varied <h2> and <h3> tags, <ul>, <p>, and <strong>. Do NOT include the H1 title in this body. Minimum 600 words equivalent."}
    },
    "required": ["slug", "title", "category", "excerpt", "date", "key_takeaways", "faqs", "content"]
}

# System Instructions to absolutely prevent AdSense "Replicated Content" rejections
system_instruction = """
You are a senior financial analyst and expert SEO writer for 'Tokenize', a US-based educational site about real-world asset tokenization.
Your goal is to write a highly original, in-depth, and fact-dense article based on the provided keyword and angle.

CRITICAL ADSENSE ORIGINALITY RULES (DO NOT FAIL THESE):
1. NO TEMPLATING DRIFT: Every article must have a UNIQUE structural flow. Do not use the same number of H2s or the same narrative arc as previous articles.
2. CONCRETE FACTS ONLY: Avoid generic filler like 'costs vary based on many factors'. Use realistic (but legally disclaimed) examples, specific SEC rules (e.g., Reg D, Reg A+), exact basis point comparisons, and concrete institutional examples.
3. TONE: Clear, authoritative, US English. Target audience is US retail and accredited investors.
4. FORMATTING: Output raw HTML for the 'content' field. Use <h2>, <h3>, <ul>, <p>, and <strong>. Do not wrap the whole response in a markdown block if outputting JSON.
"""

def generate_article(keyword, category, angle):
    print(f"\nGenerating content for: {keyword}...")
    
    prompt = f"""
    Write a comprehensive, highly original article for the following target:
    - Keyword: {keyword}
    - Category Hub: {category}
    - Specific Angle to cover: {angle}
    - Date to use: {datetime.now().strftime('%Y-%m-%d')}
    
    Remember: Ensure the HTML structure inside the 'content' field is unique to this article. Include realistic data points and deep analysis.
    Output the result EXACTLY following this JSON schema:
    {json.dumps(article_schema, indent=2)}
    """
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro",
        system_instruction=system_instruction,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.7,
        }
    )
    
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Failed to generate {keyword}: {e}")
        return None

def main():
    # Load existing articles to avoid duplicates
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            existing_articles = json.load(f)
    except FileNotFoundError:
        existing_articles = []
        
    existing_slugs = {a['slug'] for a in existing_articles}
    
    # Read the queue
    with open(CSV_PATH, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        queue = list(reader)
        
    print(f"Found {len(queue)} keywords in queue. Existing articles: {len(existing_articles)}")
    
    for row in queue:
        keyword = row['Keyword']
        category = row['Category']
        angle = row['Angle']
        
        # We need a temporary slug just to check if we already covered this exact keyword topic loosely
        temp_slug = keyword.lower().replace(' ', '-').replace(',', '').replace('.', '')
        # If a similar slug exists, we skip it (the AI will generate a better slug, but this is a rough filter)
        if any(temp_slug[:15] in s for s in existing_slugs):
             print(f"Skipping {keyword}, seems already generated.")
             continue
             
        article_data = generate_article(keyword, category, angle)
        
        if article_data:
            if article_data['slug'] in existing_slugs:
                print(f"Duplicate slug generated ({article_data['slug']}), skipping save.")
                continue
                
            existing_articles.append(article_data)
            existing_slugs.add(article_data['slug'])
            
            # Save immediately to prevent data loss
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing_articles, f, indent=2)
                
            print(f"Successfully appended: {article_data['title']}")
            
            # Sleep to respect API rate limits
            time.sleep(15)

if __name__ == '__main__':
    main()
