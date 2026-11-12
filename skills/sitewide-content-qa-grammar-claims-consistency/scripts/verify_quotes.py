#!/usr/bin/env python3
"""verify_quotes.py: every evidence quote in report data must exist word-for-word on the cited page.

Usage: python3 -I verify_quotes.py out/pages.jsonl out/report_data.json
Exit code 1 if any quote fails. Run before build_report.py; fix or drop every failure.

Matching rules (deliberately strict):
- NBSP and whitespace runs are normalised to one space on both sides; nothing else is.
- A quote may contain "…" to join two fragments from the same page; each fragment must match.
- src decides where to look: title, meta (meta description), og (og:title / og:description),
  schema (raw JSON-LD), boiler (header/footer), collapsed or text (body blocks), html (any of the above).
- The quote must be found on evidence.page. A quote that exists only on another page fails.
"""
import json, re, sys

norm = lambda s: re.sub(r'\s+', ' ', (s or '').replace(' ', ' ')).strip()


def fields(p):
    body = ' \n '.join(t for _, t, *_ in p['blocks'])
    return {
        'title': p.get('title', ''), 'meta': p.get('meta_description', ''),
        'og': p.get('og_title', '') + ' \n ' + p.get('og_description', ''),
        'schema': ' \n '.join(p.get('jsonld', [])),
        'boiler': ' \n '.join(t for _, t in p.get('boilerplate', [])),
        'text': body, 'collapsed': body, 'alt': body,
    }


def main(pages_file, data_file):
    pages = {}
    for l in open(pages_file, encoding='utf-8'):
        if l.strip():
            p = json.loads(l)
            f = {k: norm(v) for k, v in fields(p).items()}
            f['html'] = ' \n '.join(f.values())
            pages[p['key']] = f
    data = json.load(open(data_file, encoding='utf-8'))
    bad, n = [], 0
    for s in data['segments']:
        for it in s['items']:
            for e in it['evidence']:
                n += 1
                pg = pages.get(e['page'])
                if pg is None:
                    bad.append((it['title'], e['page'], 'unknown page key', e['quote']))
                    continue
                hay = pg.get(e.get('src', 'text'), pg['html'])
                for frag in [norm(x) for x in re.split(r'\s*…\s*', e['quote']) if norm(x)]:
                    if frag not in hay:
                        where = [k for k, v in pages.items() if frag in v['html']]
                        bad.append((it['title'], e['page'], e.get('src'), frag + (f'   [found on: {", ".join(where)}]' if where else '')))
    for b in bad:
        print('FAIL |', ' | '.join(str(x) for x in b))
    print(f'{n - len(bad)}/{n} evidence quotes verified')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
