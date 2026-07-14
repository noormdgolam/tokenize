"""
Final Comprehensive Audit: SEO + Technical + Content + AdSense
Checks every generated HTML page for compliance.
"""
import os, re, json, glob
from html.parser import HTMLParser
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '_src', '_data')

# ─── Helpers ────────────────────────────────────────────────────────
class TagParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = defaultdict(list)
        self.meta = {}
        self.links = {}
        self.scripts_ld = []
        self.current_tag = None
        self.current_data = ""
        self.h1_count = 0
        self.h2_count = 0
        self.h3_count = 0
        self.has_canonical = False
        self.has_hreflang = False
        self.has_og_title = False
        self.has_og_desc = False
        self.has_og_url = False
        self.has_og_type = False
        self.has_twitter_card = False
        self.has_viewport = False
        self.has_charset = False
        self.has_lang = False
        self.title_text = ""
        self.desc_text = ""
        self.in_title = False
        self.in_script_ld = False
        self.script_ld_data = ""
        self.img_count = 0
        self.img_no_alt = 0
        self.a_tags = []
        self.has_adsense_script = False
        self.ad_slot_count = 0
        self.has_nav = False
        self.has_footer = False
        self.has_main = False
        self.has_article = False
        self.has_header = False
        self.has_categories_dropdown = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'html':
            if 'lang' in attrs_dict:
                self.has_lang = True
        elif tag == 'meta':
            name = attrs_dict.get('name', '').lower()
            prop = attrs_dict.get('property', '').lower()
            content = attrs_dict.get('content', '')
            charset = attrs_dict.get('charset', '')
            if charset:
                self.has_charset = True
            if name == 'viewport':
                self.has_viewport = True
            if name == 'description':
                self.desc_text = content
            if prop == 'og:title':
                self.has_og_title = True
            if prop == 'og:description':
                self.has_og_desc = True
            if prop == 'og:url':
                self.has_og_url = True
            if prop == 'og:type':
                self.has_og_type = True
            if name == 'twitter:card':
                self.has_twitter_card = True
        elif tag == 'link':
            rel = attrs_dict.get('rel', '')
            if rel == 'canonical':
                self.has_canonical = True
            if rel == 'alternate' and 'hreflang' in attrs_dict:
                self.has_hreflang = True
        elif tag == 'title':
            self.in_title = True
        elif tag == 'script':
            stype = attrs_dict.get('type', '')
            if stype == 'application/ld+json':
                self.in_script_ld = True
                self.script_ld_data = ""
            src = attrs_dict.get('src', '')
            if 'adsbygoogle' in src:
                self.has_adsense_script = True
        elif tag == 'img':
            self.img_count += 1
            if 'alt' not in attrs_dict or not attrs_dict['alt'].strip():
                self.img_no_alt += 1
        elif tag == 'a':
            href = attrs_dict.get('href', '')
            self.a_tags.append(href)
        elif tag == 'h1':
            self.h1_count += 1
        elif tag == 'h2':
            self.h2_count += 1
        elif tag == 'h3':
            self.h3_count += 1
        elif tag == 'nav':
            self.has_nav = True
        elif tag == 'footer':
            self.has_footer = True
        elif tag == 'main':
            self.has_main = True
        elif tag == 'article':
            self.has_article = True
        elif tag == 'header':
            self.has_header = True
        
        # Check for ad slots
        cls = attrs_dict.get('class', '')
        if 'ad-slot' in cls:
            self.ad_slot_count += 1

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script' and self.in_script_ld:
            self.in_script_ld = False
            try:
                self.scripts_ld.append(json.loads(self.script_ld_data))
            except:
                self.scripts_ld.append(None)

    def handle_data(self, data):
        if self.in_title:
            self.title_text += data
        if self.in_script_ld:
            self.script_ld_data += data
        if 'Categories' in data and '▾' in data:
            self.has_categories_dropdown = True

def parse_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    parser = TagParser()
    parser.feed(content)
    return parser, content

# ─── Audit Logic ────────────────────────────────────────────────────
def audit_page(filepath, page_type="article"):
    filename = os.path.basename(filepath)
    parser, raw = parse_html(filepath)
    issues = []
    warnings = []
    info = []

    # ── 1. TITLE TAG ──
    if not parser.title_text.strip():
        issues.append("CRITICAL: Missing <title> tag")
    elif len(parser.title_text) < 20:
        warnings.append(f"Title too short ({len(parser.title_text)} chars): '{parser.title_text}'")
    elif len(parser.title_text) > 70:
        warnings.append(f"Title too long ({len(parser.title_text)} chars) — may get truncated in SERPs")

    # ── 2. META DESCRIPTION ──
    if not parser.desc_text.strip():
        issues.append("CRITICAL: Missing meta description")
    elif len(parser.desc_text) < 50:
        warnings.append(f"Meta description too short ({len(parser.desc_text)} chars)")
    elif len(parser.desc_text) > 160:
        warnings.append(f"Meta description long ({len(parser.desc_text)} chars) — may truncate")

    # ── 3. HEADING HIERARCHY ──
    if parser.h1_count == 0:
        issues.append("CRITICAL: Missing H1 tag")
    elif parser.h1_count > 1:
        warnings.append(f"Multiple H1 tags ({parser.h1_count}) — should have exactly 1")

    # ── 4. CANONICAL & HREFLANG ──
    if not parser.has_canonical:
        issues.append("CRITICAL: Missing canonical link")
    if not parser.has_hreflang:
        warnings.append("Missing hreflang alternate link")

    # ── 5. OPEN GRAPH ──
    og_missing = []
    if not parser.has_og_title: og_missing.append("og:title")
    if not parser.has_og_desc: og_missing.append("og:description")
    if not parser.has_og_url: og_missing.append("og:url")
    if not parser.has_og_type: og_missing.append("og:type")
    if og_missing:
        warnings.append(f"Missing OG tags: {', '.join(og_missing)}")

    # ── 6. TWITTER CARD ──
    if not parser.has_twitter_card:
        warnings.append("Missing twitter:card meta tag")

    # ── 7. TECHNICAL ──
    if not parser.has_lang:
        issues.append("Missing lang attribute on <html>")
    if not parser.has_charset:
        issues.append("Missing charset meta tag")
    if not parser.has_viewport:
        issues.append("Missing viewport meta tag")

    # ── 8. SEMANTIC HTML ──
    if not parser.has_nav:
        warnings.append("Missing <nav> element")
    if not parser.has_main:
        warnings.append("Missing <main> element")
    if not parser.has_header:
        warnings.append("Missing <header> element")
    if not parser.has_footer:
        warnings.append("Missing <footer> element")

    # ── 9. SCHEMA / JSON-LD ──
    schema_types = [s.get('@type') for s in parser.scripts_ld if s]
    if page_type == "article":
        if 'Article' not in schema_types:
            warnings.append("Missing Article schema (JSON-LD)")
        if 'BreadcrumbList' not in schema_types:
            warnings.append("Missing BreadcrumbList schema")
    if 'WebSite' not in schema_types and 'Organization' not in schema_types:
        info.append("No WebSite/Organization schema (inherited from base)")

    # ── 10. ADSENSE ──
    if not parser.has_adsense_script:
        warnings.append("Missing AdSense script tag")
    if parser.ad_slot_count == 0:
        info.append("No ad slots found on this page")
    else:
        info.append(f"{parser.ad_slot_count} ad slot(s) found")

    # ── 11. CATEGORIES DROPDOWN ──
    if not parser.has_categories_dropdown:
        warnings.append("Categories dropdown NOT visible in nav")

    # ── 12. IMAGES ──
    if parser.img_no_alt > 0:
        warnings.append(f"{parser.img_no_alt}/{parser.img_count} images missing alt text")

    # ── 13. INTERNAL LINKS ──
    internal_links = [a for a in parser.a_tags if a.startswith('/') or a.startswith('#')]
    external_links = [a for a in parser.a_tags if a.startswith('http')]
    info.append(f"{len(internal_links)} internal links, {len(external_links)} external links")

    # ── 14. CONTENT LENGTH (articles only) ──
    if page_type == "article":
        text = re.sub(r'<[^>]+>', '', raw)
        word_count = len(text.split())
        if word_count < 300:
            warnings.append(f"Thin content: only ~{word_count} words")
        else:
            info.append(f"~{word_count} words")

    return issues, warnings, info

# ─── Run Full Audit ─────────────────────────────────────────────────
def main():
    html_files = glob.glob(os.path.join(ROOT, '*.html'))
    
    # Load articles data for cross-referencing
    with open(os.path.join(DATA, 'articles.json'), 'r', encoding='utf-8') as f:
        articles = json.load(f)
    article_slugs = {a['slug'] for a in articles}
    
    total_issues = 0
    total_warnings = 0
    pages_with_issues = 0
    results = {}
    
    print("=" * 70)
    print("  FINAL COMPREHENSIVE AUDIT — SEO + Technical + Content + AdSense")
    print("=" * 70)
    print(f"\nScanning {len(html_files)} HTML files...\n")
    
    for filepath in sorted(html_files):
        filename = os.path.basename(filepath)
        slug = filename.replace('.html', '')
        
        if slug in article_slugs:
            page_type = "article"
        elif slug.startswith("category-"):
            page_type = "category"
        elif slug == "index":
            page_type = "index"
        elif slug == "search":
            page_type = "search"
        elif slug == "sitemap":
            page_type = "sitemap"
        else:
            page_type = "legal"
        
        issues, warnings, info = audit_page(filepath, page_type)
        results[filename] = {"issues": issues, "warnings": warnings, "info": info, "type": page_type}
        
        if issues or warnings:
            pages_with_issues += 1
        total_issues += len(issues)
        total_warnings += len(warnings)

    # ─── Check sitemap.xml ──────────────────────────────────────────
    sitemap_path = os.path.join(ROOT, 'sitemap.xml')
    sitemap_issues = []
    if os.path.exists(sitemap_path):
        with open(sitemap_path, 'r', encoding='utf-8') as f:
            sitemap_content = f.read()
        sitemap_urls = re.findall(r'<loc>(.*?)</loc>', sitemap_content)
        for hf in html_files:
            fn = os.path.basename(hf)
            if fn not in ['sitemap.html']:  # sitemap page itself doesn't need to be in xml sitemap
                expected_url_part = f"/{fn}"
                found = any(expected_url_part in u for u in sitemap_urls)
                if not found:
                    sitemap_issues.append(f"  Missing from sitemap.xml: {fn}")
    else:
        sitemap_issues.append("  CRITICAL: sitemap.xml not found!")

    # ─── Check robots.txt ───────────────────────────────────────────
    robots_path = os.path.join(ROOT, 'robots.txt')
    robots_issues = []
    if os.path.exists(robots_path):
        with open(robots_path, 'r', encoding='utf-8') as f:
            robots = f.read()
        if 'Sitemap:' not in robots:
            robots_issues.append("  robots.txt missing Sitemap directive")
        if 'User-agent:' not in robots:
            robots_issues.append("  robots.txt missing User-agent directive")
    else:
        robots_issues.append("  CRITICAL: robots.txt not found!")

    # ─── Check RSS feed ─────────────────────────────────────────────
    rss_path = os.path.join(ROOT, 'rss.xml')
    rss_issues = []
    if os.path.exists(rss_path):
        with open(rss_path, 'r', encoding='utf-8') as f:
            rss = f.read()
        rss_items = re.findall(r'<item>', rss)
        if len(rss_items) != len(articles):
            rss_issues.append(f"  RSS has {len(rss_items)} items but {len(articles)} articles exist")
    else:
        rss_issues.append("  CRITICAL: rss.xml not found!")

    # ─── DUPLICATE TITLES / DESCRIPTIONS ────────────────────────────
    all_titles = defaultdict(list)
    all_descs = defaultdict(list)
    for filepath in sorted(html_files):
        fn = os.path.basename(filepath)
        p, _ = parse_html(filepath)
        if p.title_text.strip():
            all_titles[p.title_text.strip()].append(fn)
        if p.desc_text.strip():
            all_descs[p.desc_text.strip()].append(fn)
    dup_titles = {t: files for t, files in all_titles.items() if len(files) > 1}
    dup_descs = {d: files for d, files in all_descs.items() if len(files) > 1}

    # ─── Print Results ──────────────────────────────────────────────
    # Print critical issues first
    critical_pages = {fn: r for fn, r in results.items() if r['issues']}
    if critical_pages:
        print("🔴 CRITICAL ISSUES")
        print("-" * 50)
        for fn, r in sorted(critical_pages.items()):
            print(f"\n  📄 {fn} [{r['type']}]")
            for issue in r['issues']:
                print(f"     ❌ {issue}")

    # Print warnings grouped by type
    warning_pages = {fn: r for fn, r in results.items() if r['warnings']}
    if warning_pages:
        print(f"\n\n⚠️  WARNINGS ({total_warnings} total)")
        print("-" * 50)
        
        # Group common warnings 
        warning_counts = defaultdict(int)
        warning_files = defaultdict(list)
        for fn, r in sorted(warning_pages.items()):
            for w in r['warnings']:
                warning_counts[w] += 1
                warning_files[w].append(fn)
        
        for w, count in sorted(warning_counts.items(), key=lambda x: -x[1]):
            if count > 5:
                print(f"\n  ⚠️  {w}")
                print(f"     Affects {count} pages (e.g. {', '.join(warning_files[w][:3])}...)")
            elif count > 1:
                print(f"\n  ⚠️  {w}")
                print(f"     Affects: {', '.join(warning_files[w])}")
            else:
                print(f"\n  ⚠️  [{warning_files[w][0]}] {w}")

    # Sitemap/robots/rss
    print(f"\n\n📋 INFRASTRUCTURE FILES")
    print("-" * 50)
    if sitemap_issues:
        for s in sitemap_issues:
            print(f"  ⚠️ {s}")
    else:
        print(f"  ✅ sitemap.xml — {len(re.findall(r'<url>', open(sitemap_path, encoding='utf-8').read()))} URLs indexed")
    
    if robots_issues:
        for r in robots_issues:
            print(f"  ⚠️ {r}")
    else:
        print(f"  ✅ robots.txt — Valid")
    
    if rss_issues:
        for r in rss_issues:
            print(f"  ⚠️ {r}")
    else:
        print(f"  ✅ rss.xml — {len(rss_items)} items")

    # Duplicates
    print(f"\n\n🔍 DUPLICATE DETECTION")
    print("-" * 50)
    if dup_titles:
        for title, files in dup_titles.items():
            print(f"  ⚠️ Duplicate title: \"{title[:60]}...\"")
            for f in files:
                print(f"     → {f}")
    else:
        print(f"  ✅ All {len(all_titles)} titles are unique")
    
    if dup_descs:
        for desc, files in dup_descs.items():
            print(f"  ⚠️ Duplicate meta description: \"{desc[:60]}...\"")
            for f in files:
                print(f"     → {f}")
    else:
        print(f"  ✅ All {len(all_descs)} meta descriptions are unique")

    # Summary
    print(f"\n\n{'=' * 70}")
    print(f"  AUDIT SUMMARY")
    print(f"{'=' * 70}")
    
    type_counts = defaultdict(int)
    for r in results.values():
        type_counts[r['type']] += 1
    
    print(f"\n  Total pages scanned:     {len(html_files)}")
    for t, c in sorted(type_counts.items()):
        print(f"    - {t}: {c}")
    print(f"\n  🔴 Critical issues:      {total_issues}")
    print(f"  ⚠️  Warnings:            {total_warnings}")
    print(f"  📄 Pages with problems:  {pages_with_issues}")
    print(f"  ✅ Clean pages:          {len(html_files) - pages_with_issues}")
    
    # Score
    max_score = len(html_files) * 10  # 10 points per page
    deductions = total_issues * 5 + total_warnings * 1
    score = max(0, max_score - deductions)
    pct = round(score / max_score * 100, 1)
    
    grade = "A+" if pct >= 95 else "A" if pct >= 90 else "B+" if pct >= 85 else "B" if pct >= 80 else "C" if pct >= 70 else "D" if pct >= 60 else "F"
    
    print(f"\n  📊 SEO Health Score:      {score}/{max_score} ({pct}%) — Grade: {grade}")
    print(f"\n{'=' * 70}")

if __name__ == '__main__':
    main()
