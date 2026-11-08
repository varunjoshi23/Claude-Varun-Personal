#!/usr/bin/env python3
"""Export one client's audit to a formatted .xlsx.

Usage: python3 -I export_xlsx.py audit.json out.xlsx [--status status.json] [--tracker-url URL] [--exported YYYY-MM-DD]
status.json is the live `status` collection as {id: {state, owner, note}} (read it from the tracker first).
Sheets: Summary (COUNTIFS formulas over Findings), Competitors, Findings, Content outline, Rewrites,
Method & limits. Afterwards run the xlsx skill's recalc.py and require zero errors.
"""
import argparse, json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule
from openpyxl.utils import get_column_letter as L
ap = argparse.ArgumentParser(); ap.add_argument('audit'); ap.add_argument('out')
ap.add_argument('--status'); ap.add_argument('--tracker-url', default=''); ap.add_argument('--exported', default='')
a = ap.parse_args()
A = json.load(open(a.audit, encoding='utf-8')); M = A['meta']; au = M['audit']
status = json.load(open(a.status)) if a.status else A.get('status', {})
FN = 'Arial'; f = lambda **k: Font(name=FN, **k)
HDR = PatternFill('solid', fgColor='1F1E1D'); HF = f(bold=True, color='FFFFFF', size=10)
BOX = Border(bottom=Side(style='thin', color='E5E3DF')); WRAP = Alignment(wrap_text=True, vertical='top')
RED, AMB, GRN, BLU = 'B4332A', '9A6B10', '2F6F45', '2F5A8A'
wb = Workbook()
def head(ws, cols, widths):
    for i, (c, w) in enumerate(zip(cols, widths), 1):
        x = ws.cell(1, i, c); x.font = HF; x.fill = HDR; x.alignment = Alignment(wrap_text=True, vertical='center'); ws.column_dimensions[L(i)].width = w
    ws.row_dimensions[1].height = 30
def row(ws, r, vals, **fk):
    for i, v in enumerate(vals, 1):
        x = ws.cell(r, i, v); x.font = f(size=10, **fk); x.alignment = WRAP; x.border = BOX

# Findings
fs = wb.active; fs.title = 'Findings'
O = {'Technical': 0, 'On-page': 1, 'Content': 2}; g = lambda v: 0 if v in ('Fail', 'Warn') else (1 if v == 'Not checked' else 2)
SV = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}; EF = {'S': 0, 'M': 1, 'L': 2}; G = {0: 'Issue to resolve', 1: 'Not checked', 2: 'Passed'}
rows = sorted(A['findings'], key=lambda x: (O[x['category']], g(x['verdict']), SV[x['severity']], EF[x['effort']], x['id']))
cols = ['Section', 'Group', 'ID', 'Check', 'AI check', 'Verdict', 'Severity', 'Effort', 'Owner', 'Impact', 'Status', 'Notes', 'What is on the page now', 'Competitor pattern', 'Fix / how to check']
head(fs, cols, [11, 15, 15, 32, 8, 11, 9, 7, 10, 12, 13, 26, 60, 50, 60])
for r, x in enumerate(rows, 2):
    st = status.get(x['id'], {}); gg = g(x['verdict'])
    row(fs, r, [x['category'], G[gg], x['id'], x['check'], 'Yes' if x.get('ai') else '', x['verdict'], x['severity'], x['effort'],
                st.get('owner') or x['owner'], x['impact'], (st.get('state') or 'Open') if gg < 2 else 'n/a (passed)', st.get('note', ''),
                x['actual'], '' if x.get('competitors') == 'n/a' else x.get('competitors', ''), x['fix']])
    fs.cell(r, 3).font = Font(name='Courier New', size=9, color='6B6A67')
n = len(rows) + 1; last = L(len(cols))
fs.freeze_panes = 'E2'; fs.auto_filter.ref = f'A1:{last}{n}'
dv = DataValidation(type='list', formula1='"Open,In progress,Fixed,Not doing,n/a (passed)"'); fs.add_data_validation(dv); dv.add(f'K2:K{n}')
dvo = DataValidation(type='list', formula1='"SEO,Content,Dev,Design"', allow_blank=True); fs.add_data_validation(dvo); dvo.add(f'I2:I{n}')
for t, c in (('Fail', RED), ('Warn', AMB), ('Pass', GRN)): fs.conditional_formatting.add(f'F2:F{n}', FormulaRule(formula=[f'$F2="{t}"'], font=Font(name=FN, color=c, bold=True)))
for t, c in (('Critical', RED), ('High', RED), ('Medium', AMB)): fs.conditional_formatting.add(f'G2:G{n}', FormulaRule(formula=[f'$G2="{t}"'], font=Font(name=FN, color=c, bold=True)))
fs.conditional_formatting.add(f'A2:{last}{n}', FormulaRule(formula=['OR($K2="Fixed",$K2="Not doing")'], fill=PatternFill('solid', fgColor='EEF5EF')))
fs.conditional_formatting.add(f'K2:K{n}', FormulaRule(formula=['$K2="In progress"'], font=Font(name=FN, color=AMB, bold=True)))
fs.conditional_formatting.add(f'K2:K{n}', FormulaRule(formula=['$K2="Fixed"'], font=Font(name=FN, color=GRN, bold=True)))

# Summary
sm = wb.create_sheet('Summary', 0); sm.column_dimensions['A'].width = 28
for c in 'BCDEFGHI': sm.column_dimensions[c].width = 14
sm['A1'] = f"{au['client']}: {au.get('pageLabel', 'page')} SEO audit"; sm['A1'].font = f(bold=True, size=14)
info = [('Page', au['url']), ('Primary keyword', au['keyword']), ('Secondary keywords', au.get('secondary', '')), ('Targeting', f"{au['scope']} · {au['device']}"),
        ('Audit date', au['date']), ('Current position', au['position']), ('Live tracker', a.tracker_url), ('Exported', a.exported or '')]
r = 3
for k, v in info:
    if not v: continue
    sm.cell(r, 1, k).font = f(bold=True, size=10); sm.cell(r, 2, v).font = f(size=10); sm.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9); r += 1
r0 = r + 1
for i, h in enumerate(['Section', 'Score /100', 'Checks run', 'Passed', 'Warn', 'Fail', 'Not checked', 'Open', 'Fixed'], 1):
    c = sm.cell(r0, i, h); c.font = HF; c.fill = HDR; c.alignment = Alignment(horizontal='center' if i > 1 else 'left')
R = lambda col: f'Findings!${col}$2:${col}${n}'
for j, sec in enumerate(['Technical', 'On-page', 'Content'], r0 + 1):
    s_ = f'$A{j}'; sm.cell(j, 1, sec)
    sm.cell(j, 3, f'=COUNTIFS({R("A")},{s_})-COUNTIFS({R("A")},{s_},{R("F")},"Not checked")')
    for col, v in ((4, 'Pass'), (5, 'Warn'), (6, 'Fail'), (7, 'Not checked')): sm.cell(j, col, f'=COUNTIFS({R("A")},{s_},{R("F")},"{v}")')
    sm.cell(j, 2, f'=IF(C{j}=0,0,ROUND(100*(D{j}+0.5*E{j})/C{j},0))')
    sm.cell(j, 8, f'=COUNTIFS({R("A")},{s_},{R("B")},"Issue to resolve",{R("K")},"Open")+COUNTIFS({R("A")},{s_},{R("B")},"Issue to resolve",{R("K")},"In progress")')
    sm.cell(j, 9, f'=COUNTIFS({R("A")},{s_},{R("B")},"Issue to resolve",{R("K")},"Fixed")')
    for c in range(1, 10):
        x = sm.cell(j, c); x.font = f(size=10, bold=c <= 2); x.border = BOX
        if c > 1: x.alignment = Alignment(horizontal='center')
t = r0 + 4; sm.cell(t, 1, 'Total').font = f(bold=True, size=10)
for c in range(3, 10):
    x = sm.cell(t, c, f'=SUM({L(c)}{r0 + 1}:{L(c)}{r0 + 3})'); x.font = f(bold=True, size=10); x.alignment = Alignment(horizontal='center')
sm.cell(t + 2, 1, 'Issues fixed (excl. passed & not checked)').font = f(bold=True, size=10)
x = sm.cell(t + 2, 2, f'=IF((H{t}+I{t})=0,0,I{t}/(H{t}+I{t}))'); x.number_format = '0%'; x.font = f(bold=True, size=10)
note = 'Score = (Pass×1 + Warn×0.5 + Fail×0) ÷ checks run × 100, per section; Not-checked rows are excluded. Every number here is a formula over the Findings sheet: change a Verdict or Status there and it updates. AI readiness checks are scored inside their section (AI check = Yes).'
c = sm.cell(t + 4, 1, note); c.font = f(italic=True, size=9, color='6B6A67'); c.alignment = WRAP
sm.merge_cells(start_row=t + 4, start_column=1, end_row=t + 4, end_column=9); sm.row_dimensions[t + 4].height = 42

# Competitors
co = M['competitors']; cs = wb.create_sheet('Competitors', 1)
head(cs, co['cols'], [26, 18, 24] + [16] * (len(co['cols']) - 3))
beh = {int(k) for k in co.get('behind', {})}
for r, rw in enumerate(co['rows'], 2):
    row(cs, r, rw['cells'], bold=bool(rw.get('client')))
    if rw.get('client'):
        for i in beh: cs.cell(r, i + 1).font = f(size=10, bold=True, color=RED)
nr = len(co['rows']) + 3; c = cs.cell(nr, 1, co.get('note', '')); c.font = f(italic=True, size=9, color='6B6A67'); c.alignment = WRAP
cs.merge_cells(start_row=nr, start_column=1, end_row=nr, end_column=len(co['cols'])); cs.row_dimensions[nr].height = 70; cs.freeze_panes = 'B2'

# Content outline
os_ = wb.create_sheet('Content outline'); items = M.get('outline', {}).get('items', [])
head(os_, ['#', 'Tag', 'Current heading (page order)', 'Action', 'New heading', 'Recommendation'], [5, 6, 48, 10, 40, 90])
AC = {'Keep': GRN, 'Modify': AMB, 'Remove': RED, 'Add New': BLU}
for r, x in enumerate(items, 2):
    row(os_, r, [r - 1, x['tag'], x['text'], x['action'], x.get('new', ''), x['rec']])
    os_.cell(r, 3).alignment = Alignment(wrap_text=True, vertical='top', indent=max(0, int(x['tag'][1]) - 2) * 2)
    os_.cell(r, 4).font = f(size=10, bold=True, color=AC.get(x['action'], '000000'))
    if x['action'] == 'Remove': os_.cell(r, 3).font = f(size=10, strike=True, color='6B6A67')
os_.freeze_panes = 'C2'; os_.auto_filter.ref = f'A1:F{len(items) + 1}'

# Rewrites
rw = wb.create_sheet('Rewrites'); head(rw, ['Section', 'Element', 'Now', 'Replace with'], [11, 34, 60, 90])
SN = {'technical': 'Technical', 'on-page': 'On-page', 'content': 'Content'}
for r, b in enumerate(M.get('rewrites', {}).get('blocks', []), 2):
    row(rw, r, [SN.get(b['section'], b['section']), b['label'], b.get('before', ''), b['text']])
    if b['text'].lstrip().startswith('{'): rw.cell(r, 4).font = Font(name='Courier New', size=9); rw.row_dimensions[r].height = 409

# Method
me = wb.create_sheet('Method & limits'); me.column_dimensions['A'].width = 130
me['A1'] = 'Method and limits'; me['A1'].font = f(bold=True, size=12)
for i, p in enumerate(au.get('method', []), 3):
    c = me.cell(i, 1, p); c.font = f(size=10); c.alignment = WRAP
for ws in wb.worksheets: ws.sheet_view.showGridLines = False
wb.save(a.out); print(json.dumps({'saved': a.out, 'findings': len(rows)}))
