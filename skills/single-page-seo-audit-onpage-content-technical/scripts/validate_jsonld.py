#!/usr/bin/env python3
"""Strictly validate a JSON-LD recommendation before it goes into a deliverable.

Usage: python3 -I validate_jsonld.py block.json [--known-id URL ...]
Fails (exit 1) on: comments (/* */ or //), trailing commas, anything json.loads rejects, a node that is
only {"@id": X} where X is neither defined in the block nor passed with --known-id, a missing @context,
and empty-string values (placeholders). Prints a short report either way.
"""
import argparse, json, re, sys
ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--known-id', action='append', default=[])
a = ap.parse_args()
src = open(a.file, encoding='utf-8').read()
errs = []
stripped = re.sub(r'"(?:[^"\\]|\\.)*"', '""', src)          # ignore string contents
if '/*' in stripped or re.search(r'(^|[^:])//', stripped): errs.append('contains a comment (JSON has no comments)')
if re.search(r',\s*[}\]]', stripped): errs.append('trailing comma')
try:
    d = json.loads(src)
except Exception as e:
    print(json.dumps({'valid': False, 'errors': errs + [f'json.loads: {e}']}, indent=1)); sys.exit(1)
defined, refs, empties = set(), [], []
def walk(x, path='$'):
    if isinstance(x, dict):
        if '@id' in x and len(x) > 1: defined.add(x['@id'])
        if set(x) == {'@id'}: refs.append((x['@id'], path))
        for k, v in x.items():
            if v == '' : empties.append(f'{path}.{k}')
            walk(v, f'{path}.{k}')
    elif isinstance(x, list):
        for i, v in enumerate(x): walk(v, f'{path}[{i}]')
walk(d)
if not (isinstance(d, dict) and '@context' in d): errs.append('missing top-level @context')
known = defined | set(a.known_id)
dangling = sorted({r for r, _ in refs if r not in known})
if dangling: errs.append('unresolved @id references: ' + ', '.join(dangling))
if empties: errs.append('empty values (placeholders?): ' + ', '.join(empties[:10]))
types = []
for n in (d.get('@graph') if isinstance(d, dict) and '@graph' in d else [d]):
    if isinstance(n, dict): types.append(n.get('@type'))
print(json.dumps({'valid': not errs, 'errors': errs, 'nodes': types, 'defined_ids': sorted(defined)}, indent=1, ensure_ascii=False))
sys.exit(0 if not errs else 1)
