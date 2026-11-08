#!/usr/bin/env python3
"""Validate a client's audit.json before preview, seeding or export.

Usage: python3 -I check_audit.py audit.json [--catalog ../references/checks.md]
Checks: every catalog id present exactly once (extras must be <prefix>-x<n>), allowed section/verdict/
severity/effort/owner values, required fields non-empty, Not-checked findings explain why, required meta
documents and fields, competitor table shape (client row first, Position column second), outline actions,
rewrite sections, and every JSON-LD rewrite parses strictly with all @id references resolved (via
validate_jsonld.py rules). Prints totals per section so hand-over numbers come from the data. Exit 1 on errors.
"""
import argparse, json, os, re, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('audit'); ap.add_argument('--catalog', default=os.path.join(here, '..', 'references', 'checks.md'))
a = ap.parse_args()
A = json.load(open(a.audit, encoding='utf-8'))
cat = re.findall(r'^\| ((?:tc|op|ct|ai)-[a-z0-9-]+) \|', open(a.catalog, encoding='utf-8').read(), re.M)
E, W = [], []
SEC = {'Technical', 'On-page', 'Content'}; VER = {'Pass', 'Warn', 'Fail', 'Not checked'}
SEV = {'Critical', 'High', 'Medium', 'Low'}; EFF = {'S', 'M', 'L'}; OWN = {'SEO', 'Content', 'Dev', 'Design'}
F = A.get('findings', [])
ids = [f.get('id') for f in F]
for d in sorted({i for i in ids if ids.count(i) > 1}): E.append(f'duplicate finding id {d}')
for c in cat:
    if c not in ids: E.append(f'catalog check missing: {c}')
for i in ids:
    if i not in cat and not re.fullmatch(r'(tc|op|ct)-x\d+', i or ''): E.append(f'unknown id {i} (use the catalog or <prefix>-x<n>)')
for f in F:
    i = f.get('id')
    for k in ('check', 'actual', 'fix', 'impact'):
        if not str(f.get(k, '')).strip(): E.append(f'{i}: empty {k}')
    if f.get('category') not in SEC: E.append(f'{i}: category must be one of {sorted(SEC)}')
    if f.get('verdict') not in VER: E.append(f'{i}: verdict must be one of {sorted(VER)}')
    if f.get('severity') not in SEV: E.append(f'{i}: bad severity')
    if f.get('effort') not in EFF: E.append(f'{i}: bad effort')
    if f.get('owner') not in OWN: E.append(f'{i}: bad owner')
    if f.get('verdict') == 'Not checked' and 'not checked' not in f.get('actual', '').lower(): W.append(f'{i}: Not checked finding should say why in actual')
    if (i or '').startswith('ai-') and not f.get('ai'): E.append(f'{i}: ai-* finding needs "ai": true')
    if 'competitors' not in f: E.append(f'{i}: missing competitors (use "n/a")')
M = A.get('meta', {})
au = M.get('audit', {})
for k in ('client', 'pageLabel', 'url', 'keyword', 'scope', 'device', 'date', 'position', 'basis', 'method'):
    if not au.get(k): E.append(f'meta.audit.{k} missing')
if 'scores' in au: W.append('meta.audit.scores is ignored: the tracker computes scores live')
co = M.get('competitors', {})
if not co.get('rows'): E.append('meta.competitors.rows missing')
else:
    if not co['rows'][0].get('client'): E.append('meta.competitors: client row must be first')
    if len(co.get('cols', [])) < 3 or not co['cols'][1].lower().startswith('position'): E.append('meta.competitors: column 2 must be Position')
    n = len(co.get('cols', []))
    for r in co['rows']:
        if len(r.get('cells', [])) != n: E.append(f"meta.competitors: row {r.get('cells', ['?'])[0]} has {len(r.get('cells', []))} cells, expected {n}")
    if not co.get('note'): E.append('meta.competitors.note missing (position source and limits)')
for x in M.get('outline', {}).get('items', []) or [None]:
    if x is None: E.append('meta.outline.items missing'); break
    if x.get('action') not in ('Keep', 'Modify', 'Remove', 'Add New'): E.append(f"outline '{x.get('text')}': bad action")
    if not re.fullmatch(r'H[1-6]', x.get('tag', '')): E.append(f"outline '{x.get('text')}': bad tag")
    if not x.get('rec'): E.append(f"outline '{x.get('text')}': empty rec")
adds_top = sum(1 for x in M.get('outline', {}).get('items', []) if x.get('action') == 'Add New' and x.get('tag') in ('H2',))
if adds_top > 2: E.append(f'outline adds {adds_top} new H2 sections (max 2)')
for b in M.get('rewrites', {}).get('blocks', []):
    if b.get('section') not in ('technical', 'on-page', 'content'): E.append(f"rewrite '{b.get('label')}': bad section")
    t = b.get('text', '').strip()
    if t.startswith('{'):
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as fh: fh.write(t); p = fh.name
        r = subprocess.run([sys.executable, '-I', os.path.join(here, 'validate_jsonld.py'), p], capture_output=True, text=True)
        os.unlink(p)
        if r.returncode: E.append(f"rewrite '{b.get('label')[:40]}': invalid JSON-LD: {json.loads(r.stdout)['errors'] if r.stdout.strip().startswith('{') else r.stderr}")
tot = {}
for s in ['Technical', 'On-page', 'Content']:
    xs = [f for f in F if f.get('category') == s]; ck = [f for f in xs if f.get('verdict') != 'Not checked']
    sc = round(100 * sum({'Pass': 1, 'Warn': .5}.get(f['verdict'], 0) for f in ck) / len(ck)) if ck else None
    tot[s] = {'score': sc, 'issues': sum(f['verdict'] in ('Fail', 'Warn') for f in xs), 'not_checked': sum(f['verdict'] == 'Not checked' for f in xs), 'passed': sum(f['verdict'] == 'Pass' for f in xs)}
print(json.dumps({'ok': not E, 'errors': E, 'warnings': W, 'findings': len(F), 'totals': tot}, indent=1))
sys.exit(1 if E else 0)
