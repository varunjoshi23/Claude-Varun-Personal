#!/usr/bin/env python3
"""build_report.py: validate report data and fill assets/report_template.html.

Usage: python3 -I build_report.py out/report_data.json out/metrics.json out/report.html
Schema: see references/report_data_schema.md. Fails loudly on any schema violation.
"""
import json, os, sys

IMPACT = {'High', 'Medium', 'Low'}
KIND = {'finding', 'decision', 'review', 'grammar'}
SRC = {'text', 'collapsed', 'title', 'meta', 'og', 'schema', 'html', 'alt', 'boiler'}
LAYOUT = {'cards', 'grammar', 'ai'}
META_REQ = ['client', 'domain', 'date', 'kicker', 'headline', 'lede', 'glance', 'decisions_heading',
            'decisions_blurb', 'not_reviewed', 'method', 'footer']


def validate(d, metrics):
    err = []
    for k in META_REQ:
        if not d.get('meta', {}).get(k):
            err.append(f'meta.{k} missing')
    if '{N}' not in d.get('meta', {}).get('lede', ''):
        err.append('meta.lede must contain {N} (filled with the verified quote count)')
    pages = d.get('pages', {})
    if len(d.get('top5', [])) != 5:
        err.append('top5 must have exactly 5 entries')
    ids = [s['id'] for s in d['segments']]
    if len(ids) != 5:
        err.append(f'expected 5 segments, got {len(ids)}')
    for s in d['segments']:
        if s.get('layout', 'cards') not in LAYOUT:
            err.append(f'{s["id"]}: bad layout')
        for k in ('name', 'blurb', 'verdict'):
            if not s.get(k):
                err.append(f'{s["id"]}: {k} missing')
        for it in s['items']:
            t = it.get('title', '?')
            if it.get('impact') not in IMPACT: err.append(f'{t}: impact must be High/Medium/Low')
            if it.get('kind') not in KIND: err.append(f'{t}: bad kind')
            if not it.get('rec'): err.append(f'{t}: rec missing')
            if it.get('kind') != 'grammar' and not it.get('why'): err.append(f'{t}: why missing')
            if not it.get('evidence'): err.append(f'{t}: no evidence')
            for e in it.get('evidence', []):
                if e.get('page') not in pages: err.append(f'{t}: page key {e.get("page")} not in pages')
                if e.get('src') not in SRC: err.append(f'{t}: bad src {e.get("src")}')
                if not e.get('quote'): err.append(f'{t}: empty quote')
    if {m['page'] for m in metrics} != set(pages):
        err.append('metrics pages do not match data pages')
    return err


def main(data_file, metrics_file, out):
    d = json.load(open(data_file, encoding='utf-8'))
    m = json.load(open(metrics_file, encoding='utf-8'))
    err = validate(d, m)
    if err:
        print('\n'.join('SCHEMA | ' + e for e in err)); sys.exit(1)
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'report_template.html'), encoding='utf-8').read()
    js = lambda o: json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
    title = f"{d['meta']['client']}: content inconsistency audit"
    html = tpl.replace('__TITLE__', title).replace('__DATA__', js(d)).replace('__METRICS__', js(m))
    open(out, 'w', encoding='utf-8').write(html)
    n = sum(len(s['items']) for s in d['segments'])
    print(f'wrote {out}: {n} findings across {len(d["segments"])} segments, {len(d["pages"])} pages')


if __name__ == '__main__':
    main(*sys.argv[1:4])
