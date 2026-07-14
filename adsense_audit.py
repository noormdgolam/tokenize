"""
AdSense Approval Audit
Checks every requirement Google needs to approve an AdSense account.
"""
import os, re, json, glob
from html.parser import HTMLParser
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '_src', '_data')

def load(f):
    with open(os.path.join(DATA, f), 'r', encoding='utf-8') as fh:
        return json.load(fh)

def read(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        return f.read()

def strip_html(html):
    return re.sub(r'<[^>]+>', ' ', html)

def word_count(text):
    return len(text.split())

def main():
    articles = load('articles.json')
    site = load('site.json')
    try:
        legal = load('legal.json')
    except:
        legal = []

    legal_slugs = {p['slug'] for p in legal}
    html_files = sorted(glob.glob(os.path.join(ROOT, '*.html')))

    P = "PASS"
    F = "FAIL"
    W = "WARN"

    results = []

    def check(category, name, status, detail=""):
        results.append((category, name, status, detail))

    # ═══════════════════════════════════════════════════════════════
    # 1. CONTENT QUANTITY & QUALITY
    # ═══════════════════════════════════════════════════════════════
    check("CONTENT", "Total article count", P if len(articles) >= 30 else F,
          f"{len(articles)} articles (need 30+)")

    total_pages = len(html_files)
    check("CONTENT", "Total HTML pages", P if total_pages >= 30 else F,
          f"{total_pages} pages")

    # Word counts
    short = []
    very_short = []
    good = []
    for a in articles:
        raw = strip_html(a.get('content', ''))
        wc = word_count(raw)
        if wc < 300:
            very_short.append((a['slug'], wc))
        elif wc < 600:
            short.append((a['slug'], wc))
        else:
            good.append((a['slug'], wc))

    check("CONTENT", "Articles with 600+ words",
          P if len(very_short) == 0 and len(short) <= 5 else (W if len(very_short) == 0 else F),
          f"{len(good)} good, {len(short)} thin (300-600w), {len(very_short)} very thin (<300w)")

    if very_short:
        for slug, wc in very_short[:5]:
            check("CONTENT", f"  Thin content: {slug}", F, f"Only {wc} words")

    # Check for duplicate content
    contents = {}
    dup_count = 0
    for a in articles:
        raw = strip_html(a.get('content', ''))[:200]
        if raw in contents:
            dup_count += 1
        contents[raw] = a['slug']
    check("CONTENT", "No duplicate article content", P if dup_count == 0 else F,
          f"{dup_count} potential duplicates found" if dup_count else "All unique")

    # ═══════════════════════════════════════════════════════════════
    # 2. REQUIRED LEGAL PAGES (AdSense mandatory)
    # ═══════════════════════════════════════════════════════════════
    required_legal = {
        'privacy-policy': 'Privacy Policy',
        'terms-of-service': 'Terms of Service',
        'about-us': 'About Us',
        'contact': 'Contact',
        'disclaimer': 'Disclaimer'
    }
    for slug, name in required_legal.items():
        exists = os.path.exists(os.path.join(ROOT, f"{slug}.html"))
        check("LEGAL", f"{name} page exists", P if exists else F,
              f"/{slug}.html" if exists else "MISSING — Required for AdSense")

    # Check Privacy Policy mentions AdSense/cookies
    pp_path = os.path.join(ROOT, 'privacy-policy.html')
    if os.path.exists(pp_path):
        pp = read(pp_path).lower()
        has_adsense_mention = 'adsense' in pp or 'google ad' in pp
        has_cookie_mention = 'cookie' in pp
        has_opt_out = 'opt out' in pp or 'opt-out' in pp or 'ads settings' in pp.lower()
        check("LEGAL", "Privacy Policy mentions AdSense", P if has_adsense_mention else F,
              "Mentions Google AdSense" if has_adsense_mention else "Must disclose Google AdSense usage")
        check("LEGAL", "Privacy Policy mentions cookies", P if has_cookie_mention else F,
              "Mentions cookies" if has_cookie_mention else "Must disclose cookie usage")
        check("LEGAL", "Privacy Policy has opt-out link", P if has_opt_out else W,
              "Has opt-out reference" if has_opt_out else "Should link to Google Ads Settings")

    # ═══════════════════════════════════════════════════════════════
    # 3. ADSENSE SCRIPT & AD PLACEMENT
    # ═══════════════════════════════════════════════════════════════
    # Check global AdSense script in base template
    base_html = read(os.path.join(ROOT, '_src', '_templates', 'base.html'))
    has_global_adsense = 'adsbygoogle.js' in base_html
    check("ADSENSE", "Global AdSense script in base template", P if has_global_adsense else F,
          "Script loaded via base.html" if has_global_adsense else "MISSING — Must load adsbygoogle.js globally")

    # Check pub ID placeholder
    pub_id = site.get('adsense_pub_id', '')
    is_placeholder = pub_id == 'ca-pub-0000000000000000' or not pub_id
    check("ADSENSE", "AdSense Publisher ID configured",
          W if is_placeholder else P,
          f"Currently: {pub_id}" + (" (placeholder — update before going live!)" if is_placeholder else ""))

    # Count ad slots per page type
    article_ad_counts = []
    for a in articles:
        fp = os.path.join(ROOT, f"{a['slug']}.html")
        if os.path.exists(fp):
            content = read(fp)
            count = content.count('ad-slot')
            article_ad_counts.append((a['slug'], count))

    avg_ads = sum(c for _, c in article_ad_counts) / len(article_ad_counts) if article_ad_counts else 0
    no_ads = [(s, c) for s, c in article_ad_counts if c == 0]
    too_many = [(s, c) for s, c in article_ad_counts if c > 5]

    check("ADSENSE", "Average ad slots per article",
          P if 2 <= avg_ads <= 5 else W,
          f"{avg_ads:.1f} slots/article")

    check("ADSENSE", "Articles with zero ad slots",
          P if len(no_ads) == 0 else F,
          f"{len(no_ads)} articles have no ads" if no_ads else "All articles have ads")

    check("ADSENSE", "No excessive ad density",
          P if len(too_many) == 0 else W,
          f"{len(too_many)} articles with >5 ad slots" if too_many else "All within limits")

    # Check ad slot types present in article template
    article_tmpl = read(os.path.join(ROOT, '_src', '_templates', 'article.html'))
    slot_types = {
        'ABOVE ARTICLE': 'Above-article ad' in article_tmpl or 'ABOVE ARTICLE' in article_tmpl,
        'MID ARTICLE': 'MID ARTICLE' in base_html or 'MID ARTICLE' in article_tmpl,
        'END OF POST': 'END OF POST' in article_tmpl or 'MULTIPLEX' in article_tmpl,
        'SKYSCRAPER': 'SKYSCRAPER' in article_tmpl,
    }
    for slot, present in slot_types.items():
        check("ADSENSE", f"Ad slot: {slot}", P if present else W,
              "Present in template" if present else "Not found")

    # Check index page ads
    index_content = read(os.path.join(ROOT, 'index.html'))
    index_ads = index_content.count('ad-slot')
    check("ADSENSE", "Index page ad slots", P if index_ads >= 1 else W,
          f"{index_ads} ad slot(s) on homepage")

    # ═══════════════════════════════════════════════════════════════
    # 4. COOKIE CONSENT (GDPR/AdSense requirement)
    # ═══════════════════════════════════════════════════════════════
    has_cookie_banner = 'cookie-banner' in base_html
    has_accept_btn = 'acceptCookies' in base_html or 'Accept' in base_html
    has_privacy_link_in_banner = 'privacy-policy' in base_html.lower()

    check("CONSENT", "Cookie consent banner present", P if has_cookie_banner else F,
          "Banner found in base.html" if has_cookie_banner else "MISSING — Required for GDPR/AdSense")
    check("CONSENT", "Accept button in banner", P if has_accept_btn else F,
          "Accept button found" if has_accept_btn else "MISSING")
    check("CONSENT", "Privacy Policy linked in banner", P if has_privacy_link_in_banner else W,
          "Links to Privacy Policy" if has_privacy_link_in_banner else "Should link to Privacy Policy")

    # ═══════════════════════════════════════════════════════════════
    # 5. NAVIGATION & UX (AdSense reviewers check this)
    # ═══════════════════════════════════════════════════════════════
    has_nav_links = 'nav_links' in str(base_html) or 'navlinks' in base_html
    has_footer_links = 'footer_links' in str(base_html) or 'footlinks' in base_html

    check("NAVIGATION", "Main navigation present", P if has_nav_links else F,
          "Navigation links in header")
    check("NAVIGATION", "Footer links present", P if has_footer_links else F,
          "Footer links present")

    # Check essential nav links
    nav_links = site.get('nav_links', [])
    nav_urls = [l['url'] for l in nav_links]
    check("NAVIGATION", "Home link in nav", P if '/' in nav_urls else W, "")
    check("NAVIGATION", "About link accessible", P if '/about-us.html' in nav_urls else W,
          "In nav" if '/about-us.html' in nav_urls else "In footer only — acceptable")

    footer_links = site.get('footer_links', [])
    footer_urls = [l['url'] for l in footer_links]
    check("NAVIGATION", "Privacy Policy in footer", P if '/privacy-policy.html' in footer_urls else F, "")
    check("NAVIGATION", "Terms of Service in footer", P if '/terms-of-service.html' in footer_urls else F, "")
    check("NAVIGATION", "Contact in footer", P if '/contact.html' in footer_urls else W, "")

    # ═══════════════════════════════════════════════════════════════
    # 6. TECHNICAL SEO (affects AdSense approval)
    # ═══════════════════════════════════════════════════════════════
    sitemap_exists = os.path.exists(os.path.join(ROOT, 'sitemap.xml'))
    robots_exists = os.path.exists(os.path.join(ROOT, 'robots.txt'))
    rss_exists = os.path.exists(os.path.join(ROOT, 'rss.xml'))

    check("TECHNICAL", "sitemap.xml exists", P if sitemap_exists else F, "")
    check("TECHNICAL", "robots.txt exists", P if robots_exists else F, "")
    check("TECHNICAL", "RSS feed exists", P if rss_exists else W, "Helps with content discovery")

    if robots_exists:
        robots = read(os.path.join(ROOT, 'robots.txt'))
        check("TECHNICAL", "robots.txt allows crawling", P if 'Allow: /' in robots else F,
              "Allows all crawlers" if 'Allow: /' in robots else "May be blocking crawlers")
        check("TECHNICAL", "robots.txt has Sitemap", P if 'Sitemap:' in robots else W, "")

    # Check mobile responsiveness (viewport meta)
    check("TECHNICAL", "Mobile-responsive design",
          P if 'viewport' in base_html else F,
          "Viewport meta tag in base template" if 'viewport' in base_html else "MISSING viewport")

    # HTTPS ready (check canonical URLs)
    uses_https = 'https://' in site.get('url', '')
    check("TECHNICAL", "HTTPS in canonical URLs", P if uses_https else W,
          f"Site URL: {site.get('url', 'not set')}")

    # ═══════════════════════════════════════════════════════════════
    # 7. CONTENT POLICY COMPLIANCE
    # ═══════════════════════════════════════════════════════════════
    # Check for financial disclaimer (important for finance niche)
    disclaimer_exists = os.path.exists(os.path.join(ROOT, 'disclaimer.html'))
    check("POLICY", "Financial disclaimer page", P if disclaimer_exists else F,
          "Present — important for YMYL finance niche")

    # Check article template has author bio (E-E-A-T signal)
    has_author_bio = 'author-bio' in article_tmpl or 'author_bio' in article_tmpl
    check("POLICY", "Author bio on articles (E-E-A-T)", P if has_author_bio else W,
          "Author bio section in article template" if has_author_bio else "Add author info for credibility")

    # Check for breadcrumbs (navigation signal)
    has_breadcrumbs = 'BreadcrumbList' in article_tmpl or 'breadcrumb' in article_tmpl.lower()
    check("POLICY", "Breadcrumb navigation", P if has_breadcrumbs else W,
          "BreadcrumbList schema + visual breadcrumbs" if has_breadcrumbs else "Add breadcrumbs")

    # Schema markup
    has_article_schema = '"Article"' in article_tmpl
    has_faq_schema = '"FAQPage"' in article_tmpl
    check("POLICY", "Article structured data", P if has_article_schema else W, "")
    check("POLICY", "FAQ structured data", P if has_faq_schema else W, "")

    # ═══════════════════════════════════════════════════════════════
    # 8. DOMAIN & SITE IDENTITY
    # ═══════════════════════════════════════════════════════════════
    has_brand = bool(site.get('brand'))
    has_logo = 'logo' in base_html.lower()
    check("IDENTITY", "Brand name configured", P if has_brand else F, site.get('brand', 'NOT SET'))
    check("IDENTITY", "Logo present in header", P if has_logo else W, "")
    
    placeholder_url = 'example.com' in site.get('url', '')
    check("IDENTITY", "Production domain set",
          W if placeholder_url else P,
          f"Currently: {site.get('url', 'NOT SET')}" + (" (update to real domain before applying!)" if placeholder_url else ""))

    # ═══════════════════════════════════════════════════════════════
    # PRINT RESULTS
    # ═══════════════════════════════════════════════════════════════
    print("=" * 70)
    print("  GOOGLE ADSENSE APPROVAL AUDIT")
    print("=" * 70)

    categories_order = ["CONTENT", "LEGAL", "ADSENSE", "CONSENT", "NAVIGATION", "TECHNICAL", "POLICY", "IDENTITY"]
    category_names = {
        "CONTENT": "Content Quantity & Quality",
        "LEGAL": "Required Legal Pages",
        "ADSENSE": "AdSense Script & Placement",
        "CONSENT": "Cookie Consent (GDPR)",
        "NAVIGATION": "Navigation & UX",
        "TECHNICAL": "Technical SEO",
        "POLICY": "Content Policy & E-E-A-T",
        "IDENTITY": "Domain & Site Identity"
    }

    total_pass = sum(1 for r in results if r[2] == P)
    total_fail = sum(1 for r in results if r[2] == F)
    total_warn = sum(1 for r in results if r[2] == W)

    for cat in categories_order:
        cat_results = [r for r in results if r[0] == cat]
        if not cat_results:
            continue

        cat_pass = sum(1 for r in cat_results if r[2] == P)
        cat_total = len(cat_results)

        print(f"\n{'─' * 70}")
        print(f"  {category_names.get(cat, cat)} ({cat_pass}/{cat_total})")
        print(f"{'─' * 70}")

        for _, name, status, detail in cat_results:
            icon = "[PASS]" if status == P else "[FAIL]" if status == F else "[WARN]"
            color_name = name
            line = f"  {icon} {color_name}"
            if detail:
                line += f" — {detail}"
            print(line)

    # FINAL VERDICT
    print(f"\n{'=' * 70}")
    print(f"  ADSENSE APPROVAL VERDICT")
    print(f"{'=' * 70}")
    print(f"\n  [PASS] {total_pass}  |  [WARN] {total_warn}  |  [FAIL] {total_fail}")
    print(f"  Total checks: {total_pass + total_warn + total_fail}")

    approval_score = total_pass / (total_pass + total_warn + total_fail) * 100
    print(f"\n  Readiness Score: {approval_score:.0f}%")

    if total_fail == 0 and total_warn <= 3:
        print("\n  VERDICT: READY FOR ADSENSE APPLICATION")
        print("  Your site meets all critical AdSense requirements.")
    elif total_fail == 0:
        print("\n  VERDICT: LIKELY TO BE APPROVED")
        print("  No critical failures. Address warnings to improve chances.")
    elif total_fail <= 2:
        print("\n  VERDICT: NEEDS MINOR FIXES")
        print("  Fix the FAIL items before applying.")
    else:
        print("\n  VERDICT: NOT READY")
        print("  Multiple critical issues must be resolved first.")

    # Action items
    fails = [r for r in results if r[2] == F]
    warns = [r for r in results if r[2] == W]
    if fails or warns:
        print(f"\n{'─' * 70}")
        print("  ACTION ITEMS")
        print(f"{'─' * 70}")
        if fails:
            print("\n  Must fix before applying:")
            for _, name, _, detail in fails:
                print(f"    [FAIL] {name} — {detail}")
        if warns:
            print("\n  Recommended improvements:")
            for _, name, _, detail in warns:
                print(f"    [WARN] {name} — {detail}")

    print(f"\n{'=' * 70}")

if __name__ == '__main__':
    main()
