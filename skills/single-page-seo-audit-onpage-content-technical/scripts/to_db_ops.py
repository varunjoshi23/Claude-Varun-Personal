#!/usr/bin/env python3
"""Turn audit.json into db_write batches for a NEW tracker (no existing documents).

Usage: python3 -I to_db_ops.py audit.json outdir
Writes outdir/ops_01.json, ops_02.json ... each a JSON array of at most 50 `set` ops (the db_write limit):
meta/audit, meta/competitors, meta/outline, meta/rewrites, then findings/<id>. Send them one call at a time,
waiting ~2 s between calls. For an existing tracker, read versions first and use update/set with ifVersion.
"""
import json, os, sys
A = json.load(open(sys.argv[1], encoding='utf-8')); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
ops = [{'op': 'set', 'path': f'meta/{k}', 'data': A['meta'][k]} for k in ('audit', 'competitors', 'outline', 'rewrites') if k in A['meta']]
ops += [{'op': 'set', 'path': f"findings/{f['id']}", 'data': f} for f in A['findings']]
for n, i in enumerate(range(0, len(ops), 50), 1):
    p = os.path.join(out, f'ops_{n:02d}.json'); json.dump(ops[i:i + 50], open(p, 'w'), ensure_ascii=False); print(p, len(ops[i:i + 50]))
