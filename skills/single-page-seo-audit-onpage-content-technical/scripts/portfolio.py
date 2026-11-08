#!/usr/bin/env python3
"""Add or update one client's row in the portfolio workbook (one row per client, many clients).

Usage: python3 -I portfolio.py portfolio.xlsx audit.json --tracker-url URL [--status status.json]
Creates the workbook if missing. The row is keyed on Client + Page URL, so re-running a client replaces
its row instead of duplicating it. Columns: client, page, keyword, scope, audit date, position, tracker
link, the three section scores, issues open/fixed, not checked, high-severity open issues, and the top
three open issues (by severity, then effort). Scores are computed here from the same rule the tracker uses.
"""
import argparse, json, os
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.formatting.rule import CellIsRule
ap = argparse.ArgumentParser(); ap.add_argument('book'); ap.add_argument('audit'); ap.add_argument('--tracker-url', default=''); ap.add_argument('--status')
a = ap.parse_args()
A = json.load(open(a.audit, encoding='utf-8')); au = A['meta']['audit']; F = A['findings']
st = json.load(open(a.status)) if a.status else A.get('status', {})
state = lambda i: (st.get(i) or {}).get('state', 'Open')
COLS = ['Client', 'Page URL', 'Primary keyword', 'Targeting', 'Audit date', 'Position', 'Tracker', 'Technical', 'On-page', 'Content',
        'Issues open', 'Issues fixed', 'Not checked', 'High/Critical open', 'Top open issue 1', 'Top open issue 2', 'Top open issue 3']
def score(sec):
    ck = [f for f in F if f['category'] == sec and f['verdict'] != 'Not checked']
    return round(100 * sum({'Pass': 1, 'Warn': .5}.get(f['verdict'], 0) for f in ck) / len(ck)) if ck else None
iss = [f for f in F if f['verdict'] in ('Fail', 'Warn')]
open_ = [f for f in iss if state(f['id']) in ('Open', 'In progress')]
SV = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}; EF = {'S': 0, 'M': 1, 'L': 2}
top = sorted(open_, key=lambda f: (SV[f['severity']], EF[f['effort']], f['id']))[:3]
vals = [au['client'], au['url'], au['keyword'], au['scope'], au['date'], au['position'], a.tracker_url, score('Technical'), score('On-page'), score('Content'),
        len(open_), sum(state(f['id']) == 'Fixed' for f in iss), sum(f['verdict'] == 'Not checked' for f in F),
        sum(f['severity'] in ('High', 'Critical') for f in open_)] + [f"{f['severity']}: {f['check']} ({f['category']})" for f in top] + [''] * (3 - len(top))
if os.path.exists(a.book): wb = load_workbook(a.book); ws = wb.active
else:
    wb = Workbook(); ws = wb.active; ws.title = 'Portfolio'
    for i, c in enumerate(COLS, 1):
        x = ws.cell(1, i, c); x.font = Font(name='Arial', bold=True, color='FFFFFF', size=10); x.fill = PatternFill('solid', fgColor='1F1E1D'); x.alignment = Alignment(wrap_text=True, vertical='center')
    for i, w in enumerate([22, 40, 26, 22, 11, 22, 30, 10, 10, 10, 10, 10, 11, 12, 40, 40, 40], 1): ws.column_dimensions[ws.cell(1, i).column_letter].width = w
    ws.freeze_panes = 'C2'; ws.sheet_view.showGridLines = False
target = None
for r in range(2, ws.max_row + 1):
    if ws.cell(r, 1).value == au['client'] and ws.cell(r, 2).value == au['url']: target = r; break
target = target or ws.max_row + 1
for i, v in enumerate(vals, 1):
    x = ws.cell(target, i, v); x.font = Font(name='Arial', size=10); x.alignment = Alignment(wrap_text=True, vertical='top')
if a.tracker_url: ws.cell(target, 7).hyperlink = a.tracker_url; ws.cell(target, 7).font = Font(name='Arial', size=10, color='2F5A8A', underline='single')
last = ws.max_row
ws.auto_filter.ref = f'A1:Q{last}'
ws.conditional_formatting = type(ws.conditional_formatting)()
for col in 'HIJ':
    ws.conditional_formatting.add(f'{col}2:{col}{last}', CellIsRule(operator='lessThan', formula=['40'], font=Font(name='Arial', bold=True, color='B4332A')))
    ws.conditional_formatting.add(f'{col}2:{col}{last}', CellIsRule(operator='between', formula=['40', '69'], font=Font(name='Arial', bold=True, color='9A6B10')))
    ws.conditional_formatting.add(f'{col}2:{col}{last}', CellIsRule(operator='greaterThanOrEqual', formula=['70'], font=Font(name='Arial', bold=True, color='2F6F45')))
wb.save(a.book); print(json.dumps({'book': a.book, 'row': target, 'client': au['client'], 'scores': vals[7:10], 'open': vals[10]}))
