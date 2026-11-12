#!/usr/bin/env python3
"""readability.py: per-page readability snapshot for the AI-quotability segment.

Usage: python3 -I readability.py out/pages.jsonl out/metrics.json

Measured on each page's paragraph text (p, li, blockquote, dd, td) excluding header/footer.
- sentences, avg words/sentence, longest sentence, % of sentences over 30 words, Flesch reading ease:
  measured on the page's UNIQUE paragraphs (those not counted as boilerplate).
- boiler: share of the page's paragraph characters that repeat on more than half the pages in scope
  (8 or more of 15). null when the page has no paragraph text.
- h1: count of H1 elements in the rendered page.
"""
import json, re, sys, math
from collections import defaultdict

PARA = {'p', 'li', 'blockquote', 'dd', 'td'}
SENT = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9“"‘(])')


def syllables(w):
    w = re.sub(r'[^a-z]', '', w.lower())
    if not w:
        return 0
    groups = re.findall(r'[aeiouy]+', w)
    n = len(groups)
    if w.endswith('e') and n > 1 and not w.endswith(('le', 'ee')):
        n -= 1
    return max(1, n)


def main(src, dst):
    pages = [json.loads(l) for l in open(src, encoding='utf-8') if l.strip()]
    seen = defaultdict(set)
    for p in pages:
        for tag, t, *_ in p['blocks']:
            if tag in PARA and len(t) > 40:
                seen[t].add(p['key'])
    thresh = math.floor(len(pages) / 2) + 1
    rows = []
    for p in pages:
        paras = [t for tag, t, *_ in p['blocks'] if tag in PARA]
        total = sum(len(t) for t in paras)
        boiler_chars = sum(len(t) for t in paras if len(seen.get(t, ())) >= thresh)
        unique = [t for t in paras if len(seen.get(t, ())) < thresh]
        sents = [s for t in unique for s in SENT.split(t) if len(s.split()) >= 3]
        words = [len(s.split()) for s in sents]
        nw = sum(words) or 1
        syl = sum(syllables(w) for s in sents for w in s.split())
        flesch = round(206.835 - 1.015 * (nw / max(1, len(sents))) - 84.6 * (syl / nw)) if sents else None
        rows.append({'page': p['key'], 'sentences': len(sents),
                     'avg': round(nw / len(sents), 1) if sents else 0,
                     'max': max(words) if words else 0,
                     'over30': round(100 * sum(w > 30 for w in words) / len(words)) if words else 0,
                     'flesch': flesch,
                     'boiler': round(100 * boiler_chars / total) if total else None,
                     'h1': len(p['h1'])})
    json.dump(rows, open(dst, 'w'), indent=1)
    print(f'{len(rows)} pages; boilerplate threshold = {thresh}+ of {len(pages)} pages')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
