import os
import json
import re
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Paths
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(SRC_DIR, '_data')
TEMPLATES_DIR = os.path.join(SRC_DIR, '_templates')

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
        return json.load(f)

def inject_mid_article_content(content):
    """Inject AdSense slot and Newsletter opt-in after the second <h2> tag"""
    injection_html = '''
<div class="ad-slot"><div class="box">AD SLOT — MID ARTICLE (Responsive)</div></div>
<div style="background:var(--surface-2); border:1px solid var(--line); border-radius:8px; padding:24px; margin:40px 0; text-align:center;">
    <h3 style="color:var(--teal); margin-bottom:12px; font-family:'Inter', sans-serif;">Never miss an update on Tokenization</h3>
    <p style="color:var(--muted); margin-bottom:20px; font-size:0.95rem;">Join 10,000+ investors receiving our weekly insights directly to their inbox.</p>
    <form style="display:flex; gap:12px; max-width:400px; margin:0 auto;" onsubmit="event.preventDefault(); alert('Subscribed!');">
        <input type="email" placeholder="Enter your email" required style="flex:1; padding:12px; border-radius:6px; border:1px solid var(--line); background:var(--ink); color:var(--text); font-size:1rem;">
        <button type="submit" style="padding:12px 24px; border-radius:6px; border:none; background:var(--teal); color:var(--ink); cursor:pointer; font-weight:600; font-size:1rem;">Subscribe</button>
    </form>
</div>
'''
    parts = re.split(r'(<h2.*?>.*?</h2>)', content, flags=re.IGNORECASE)
    
    if len(parts) > 4: # Means we found at least two h2 tags (part 1 text, part 2 h2, part 3 text, part 4 h2, part 5 text...)
        parts.insert(4, injection_html)
        return ''.join(parts)
    return content

def main():
    print("Loading data...")
    site = load_json('site.json')
    articles = load_json('articles.json')
    try:
        legal_pages = load_json('legal.json')
    except:
        legal_pages = []
    
    # Process content to include ads and newsletter
    for article in articles:
        article['content_with_ads'] = inject_mid_article_content(article.get('content', ''))
        
    # Generate categories
    unique_categories = set(a.get('category', 'Uncategorized') for a in articles)
    site['categories'] = sorted([
        {"name": c, "slug": c.lower().replace(' ', '-')}
        for c in unique_categories
    ], key=lambda x: x['name'])
    
    # Setup Jinja
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    
    def render_and_save(template_name, output_filename, **context):
        template = env.get_template(template_name)
        html = template.render(site=site, **context)
        out_path = os.path.join(ROOT_DIR, output_filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Generated {output_filename}")

    # 1. Generate index.html
    render_and_save('index.html', 'index.html', articles=articles)
    
    # 2. Generate search.html
    render_and_save('search.html', 'search.html')
    
    # 3. Generate html sitemap
    render_and_save('html_sitemap.html', 'sitemap.html', articles=articles, legal_pages=legal_pages)

    # 4. Generate legal pages
    for page in legal_pages:
        render_and_save('legal.html', f"{page['slug']}.html", page=page)

    # 4. Generate article pages
    for article in articles:
        related = [a for a in articles if a['slug'] != article['slug']][:3]
        render_and_save('article.html', f"{article['slug']}.html", article=article, related=related)
        
    # 4.5 Generate category pages
    for cat in site['categories']:
        cat_articles = [a for a in articles if a.get('category', 'Uncategorized') == cat['name']]
        render_and_save('category.html', f"category-{cat['slug']}.html", 
                        articles=cat_articles, 
                        category_name=cat['name'],
                        category_slug=cat['slug'])
        
    # 5. Generate search_index.json
    search_index = [
        {"title": a["title"], "slug": a["slug"], "excerpt": a["excerpt"]}
        for a in articles
    ]
    with open(os.path.join(ROOT_DIR, 'search_index.json'), 'w', encoding='utf-8') as f:
        json.dump(search_index, f)
    print("Generated search_index.json")

    # 6. Generate PWA files
    manifest = {
        "name": site["brand"],
        "short_name": site["brand"],
        "start_url": "/",
        "display": "standalone",
        "background_color": site["theme"]["ink"],
        "theme_color": site["theme"]["ink"],
        "icons": [] 
    }
    with open(os.path.join(ROOT_DIR, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f)
    print("Generated manifest.json")
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    sw_code = f"""
const CACHE_NAME = 'site-cache-{timestamp}';
const urlsToCache = [
  '/',
  '/index.html',
  '/search.html',
  '/search_index.json'
];

self.addEventListener('install', event => {{
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
}});

self.addEventListener('activate', event => {{
  event.waitUntil(
    caches.keys().then(cacheNames => {{
      return Promise.all(
        cacheNames.map(cacheName => {{
          if (cacheName !== CACHE_NAME) {{
            return caches.delete(cacheName);
          }}
        }})
      );
    }})
  );
}});

self.addEventListener('fetch', event => {{
  event.respondWith(
    caches.match(event.request)
      .then(response => {{
        if (response) return response;
        return fetch(event.request);
      }})
  );
}});
"""
    with open(os.path.join(ROOT_DIR, 'sw.js'), 'w', encoding='utf-8') as f:
        f.write(sw_code.strip())
    print("Generated sw.js")

    # 7. Generate sitemap.xml
    urls = ['/', '/index.html', '/search.html'] + [f"/{p['slug']}.html" for p in legal_pages] + [f"/{a['slug']}.html" for a in articles] + [f"/category-{c['slug']}.html" for c in site['categories']]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        sitemap += f"  <url>\n    <loc>{site['url']}{u}</loc>\n    <changefreq>weekly</changefreq>\n  </url>\n"
    sitemap += "</urlset>"
    with open(os.path.join(ROOT_DIR, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap)
    print("Generated sitemap.xml")

    # 8. Generate robots.txt
    robots = f"User-agent: *\nAllow: /\n\nSitemap: {site['url']}/sitemap.xml\n"
    with open(os.path.join(ROOT_DIR, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(robots)
    print("Generated robots.txt")

    # 9. Generate rss.xml
    rss = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{site['title']}</title>
  <link>{site['url']}</link>
  <description>{site['description']}</description>
  <atom:link href="{site['url']}/rss.xml" rel="self" type="application/rss+xml" />
"""
    for a in articles:
        rss += f"""  <item>
    <title>{a['title']}</title>
    <link>{site['url']}/{a['slug']}.html</link>
    <description>{a['excerpt']}</description>
    <pubDate>{a['date']} 12:00:00 GMT</pubDate>
  </item>\n"""
    rss += "</channel>\n</rss>"
    with open(os.path.join(ROOT_DIR, 'rss.xml'), 'w', encoding='utf-8') as f:
        f.write(rss)
    print("Generated rss.xml")
    
    print("Static site generation complete.")

if __name__ == '__main__':
    main()
