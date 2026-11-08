#!/usr/bin/env python3
"""Extract the on-page element set from saved raw HTML.

Usage: python3 -I parse_page.py page.html https://example.com/page/ [--keywords "kw one;kw two"] [--text]
Prints JSON: title, meta, canonical, robots, OG/Twitter, JSON-LD blocks, every heading in
document order, word/paragraph/list/table counts, images (alt, size, loading), internal and
external links in the main content, tel links, keyword phrase counts, FAQ-style headings.
--text adds the full main-content text (for the first-100-words and answer-first checks).
"""
import argparse, json, re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

ap = argparse.ArgumentParser()
ap.add_argument('html'); ap.add_argument('base')
ap.add_argument('--keywords', default='', help='semicolon-separated phrases to count (case-insensitive)')
ap.add_argument('--text', action='store_true')
a = ap.parse_args()

raw = open(a.html, encoding='utf-8', errors='ignore').read()
s = BeautifulSoup(raw, 'lxml')
host = urlparse(a.base).netloc.replace('www.', '')
meta = lambda n, attr='name': (s.find('meta', attrs={attr: n}) or {}).get('content') if s.find('meta', attrs={attr: n}) else None
words = lambda t: len(re.findall(r"[A-Za-z0-9'’]+", t))

o = {}
o['title'] = s.title.get_text(strip=True) if s.title else None
o['title_len'] = len(o['title'] or '')
o['meta_desc'] = meta('description'); o['meta_desc_len'] = len(o['meta_desc'] or '')
cans = s.find_all('link', rel='canonical')
o['canonical'] = cans[0].get('href') if cans else None; o['canonical_count'] = len(cans)
o['robots'] = meta('robots'); o['viewport'] = meta('viewport')
o['lang'] = s.html.get('lang') if s.html else None
o['hreflang'] = [l.get('hreflang') for l in s.find_all('link', rel='alternate') if l.get('hreflang')]
o['og'] = {m.get('property'): m.get('content') for m in s.find_all('meta') if (m.get('property') or '').startswith('og:')}
o['twitter'] = {m.get('name'): m.get('content') for m in s.find_all('meta') if (m.get('name') or '').startswith('twitter:')}
o['shortlink'] = [l.get('href') for l in s.find_all('link', rel='shortlink')]
ld = []
for t in s.find_all('script', type='application/ld+json'):
    txt = t.string or t.get_text()
    try: ld.append(json.loads(txt))
    except Exception as e: ld.append({'_parse_error': str(e), 'raw': txt[:400]})
o['jsonld'] = ld
o['microdata_itemtypes'] = sorted({t.get('itemtype') for t in s.find_all(attrs={'itemtype': True})})

b = BeautifulSoup(raw, 'lxml')
for t in b(['script', 'style', 'noscript', 'svg', 'iframe']): t.decompose()
main = b.find('main') or b.find(attrs={'role': 'main'}) or b.find(id=re.compile('content|main', re.I)) or b.body
mc = BeautifulSoup(str(main), 'lxml')
for t in mc(['header', 'footer', 'nav']): t.decompose()
text = mc.get_text(' ', strip=True)
body_text = b.body.get_text(' ', strip=True) if b.body else ''
o['main_selector'] = main.name + ('#' + main.get('id') if main.get('id') else '')
o['word_count_main'] = words(text); o['word_count_body'] = words(body_text)
o['headings'] = [[h.name, re.sub(r'\s+', ' ', h.get_text(' ', strip=True))] for h in s.find_all(re.compile('^h[1-6]$'))]
o['h_counts'] = {f'h{i}': sum(1 for h in o['headings'] if h[0] == f'h{i}') for i in range(1, 7)}
o['paragraphs'] = len([p for p in mc.find_all('p') if p.get_text(strip=True)])
o['lists'] = len(mc.find_all(['ul', 'ol'])); o['tables'] = len(mc.find_all('table'))
imgs = s.find_all('img')
o['images'] = [{'src': i.get('src') or i.get('data-src') or '', 'alt': i.get('alt'), 'width': i.get('width'), 'height': i.get('height'), 'loading': i.get('loading')} for i in imgs]
o['img_count'] = len(imgs); o['img_missing_alt'] = sum(1 for i in imgs if not (i.get('alt') or '').strip())
il, el = [], []
for x in mc.find_all('a', href=True):
    href = x['href']
    if href.startswith(('mailto:', 'tel:', 'javascript:')): continue
    u = urljoin(a.base, href)
    rec = [re.sub(r'\s+', ' ', x.get_text(' ', strip=True))[:80], u]
    (il if urlparse(u).netloc.replace('www.', '') == host else el).append(rec)
o['internal_links_main'] = il; o['external_links_main'] = el
o['internal_urls_all'] = sorted({urljoin(a.base, x['href']).split('#')[0] for x in s.find_all('a', href=True)
                                 if not x['href'].startswith(('mailto:', 'tel:', 'javascript:', '#'))
                                 and urlparse(urljoin(a.base, x['href'])).netloc.replace('www.', '') == host})
o['tel_links'] = sorted({x['href'] for x in s.find_all('a', href=True) if x['href'].startswith('tel:')})
o['dates'] = {k: meta(k, 'property') for k in ['article:published_time', 'article:modified_time']}
o['time_tags'] = [t.get('datetime') for t in s.find_all('time')]
low = body_text.lower()
o['keyword_counts'] = {k.strip(): low.count(k.strip().lower()) for k in a.keywords.split(';') if k.strip()}
o['question_headings'] = [h[1] for h in o['headings'] if h[1].strip().endswith('?')]
if s.head:
    o['head_blocking_scripts'] = len([t for t in s.head.find_all('script', src=True) if not t.get('async') and not t.get('defer') and t.get('type') != 'module'])
    o['head_stylesheets'] = len(s.head.find_all('link', rel='stylesheet'))
o['first_100_words'] = ' '.join(text.split()[:100])
if a.text: o['main_text'] = text
print(json.dumps(o, indent=1, ensure_ascii=False))
