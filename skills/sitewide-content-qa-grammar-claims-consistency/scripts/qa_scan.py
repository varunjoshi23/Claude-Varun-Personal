#!/usr/bin/env python3
"""qa_scan.py: deterministic mechanics pass. Output is CANDIDATES only; confirm each by reading the page.

Usage: python3 -I qa_scan.py out/pages.jsonl out/scan
Writes issues.jsonl, claims.jsonl (number+claim sentences, contact strings), style.json (convention tallies).
"""
import json, re, sys, os
from collections import Counter, defaultdict
VARIANT = {'organise':'organize','organisation':'organization','optimise':'optimize','optimisation':'optimization','analyse':'analyze','behaviour':'behavior','colour':'color','favourite':'favorite','honour':'honor','labour':'labor','centre':'center','metre':'meter','programme':'program','catalogue':'catalog','cancelled':'canceled','defence':'defense','enquiry':'inquiry','fulfil':'fulfill','grey':'gray','specialise':'specialize','realise':'realize','recognise':'recognize','licence':'license','travelling':'traveling','whilst':'while','amongst':'among','towards':'toward','learnt':'learned'}
CAPS_OK = set('SEO AEO GEO SERP HTML CSS FAQ CTA API ROI ROAS GST PDF USA UK UAE NAP URL CMS SAAS B2B B2C KPI SLA SOP LLM PPC GA4 GSC CRM ERP CEO CTO COO HTTP HTTPS WWW XML JSON UTM EMI ISO ECOMMERCE'.split())
REP_OK = set('that had no very long so out on'.split())
RX = {
 'double_space': (re.compile('[ ]{2,}'), 'P2', 'Two or more consecutive spaces'),
 'space_before_punct': (re.compile('[ ]+[,;:!?]'), 'P2', 'Space before punctuation'),
 'no_space_after_punct': (re.compile('[,;:](?=[A-Za-z])'), 'P2', 'Missing space after punctuation'),
 'repeated_word': (re.compile('(?i)(?:^|[^A-Za-z])(?P<w>[A-Za-z]{2,})[ ]+(?P=w)(?:[^A-Za-z]|$)'), 'P1', 'Word repeated'),
 'multi_punct': (re.compile('[!?]{2,}|[.]{2,}|,{2,}'), 'P2', 'Repeated punctuation'),
 'unit_space': (re.compile('[0-9][ ]+%'), 'P3', 'Space before percent sign'),
 'mojibake': (re.compile('(?i)(â\u0080\u0099|â\u0080\u009c|Ã©|  |&amp;|&quot;|&#39;)'), 'P1', 'Encoding artifact or raw HTML entity'),
 'placeholder': (re.compile('(?i)(lorem ipsum|[ ]todo|[ ]tbd|xxx|insert here|your company|client name|coming soon|[{]{2})'), 'P0', 'Placeholder text left in live copy'),
 'caps_word': (re.compile('(?:^|[^A-Za-z])([A-Z]{4,})(?:[^A-Za-z]|$)'), 'P3', 'All-caps word'),
}
CONFUSE = [('(?i)(?:^|[^A-Za-z])its(?=[ ][a-z]+(?:ing|ed)[ ])', "its vs it's"),
 ('(?i)(?:^|[^A-Za-z])(could|should|would)[ ]of(?:[^A-Za-z]|$)', 'could of'),
 ('(?i)(?:^|[^A-Za-z])(alot|irregardless|definately|seperate|recieve|occured|accomodate|publically|maintainance|untill|thier|teh|buisness|succesful|neccessary|enviroment|existance|guage|liason|refered|wich)(?:[^A-Za-z]|$)', 'Common misspelling'),
 ('(?i)(?:^|[^A-Za-z])comprised of(?:[^A-Za-z]|$)', 'comprised of'),
 ('(?i)(?:^|[^A-Za-z])(less)[ ](?=clients|customers|visitors|keywords|pages|leads|people)', 'less vs fewer'),
 ('(?i)(?:^|[^A-Za-z])(then)(?:[^A-Za-z]|$)', 'then vs than check'),
 ('(?i)(?:^|[^A-Za-z])(your)[ ](?=welcome|going|the[ ]best)', "your vs you're"),
 ('(?i)(?:^|[^A-Za-z])(effect)[ ](?=the|our|your)', 'affect vs effect'),
 ('(?i)(?:^|[^A-Za-z])(everyday)[ ](?=we|they|you|our)', 'everyday vs every day')]
CONFUSE = [(re.compile(p), n) for p, n in CONFUSE]
CLAIM_HINT = re.compile('(?i)(year|yrs|decade|experience|client|customer|project|campaign|brand|team|member|employee|staff|countr|cities|office|found|establish|since|rating|review|award|certif|partner|rank|traffic|growth|increase|revenue|roi|lead|conversion|guarantee|refund|turnaround|deliver|hour|day|week|month|price|pricing|cost|starting at|per month|retainer|discount|percent|%)')
HAS_NUM = re.compile('(?i)(?:^|[^A-Za-z])([0-9]+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|fifteen|twenty|thirty|forty|fifty|sixty|hundred|thousand|million|dozen|half)(?:[^A-Za-z]|$)')
EMAIL = re.compile('[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}')
PHONE = re.compile('[+]?[0-9][0-9 ()-]{7,}[0-9]')
SENT = re.compile('(?<=[.!?])[ ]+(?=[A-Z0-9])')
TITLECASE = re.compile('^(?:[A-Z][a-z0-9]*[ ]){2,}[A-Z][a-z0-9]*$')
def ctx(text, a, b, pad=70): return ' '.join(text[max(0, a - pad):min(len(text), b + pad)].split())
def main(src, out):
    os.makedirs(out, exist_ok=True)
    issues, claims = [], []
    style = {'uk': Counter(), 'us': Counter(), 'oxford_yes': 0, 'oxford_no': 0, 'heading_title': 0, 'heading_sentence': 0, 'curly_quote': 0, 'straight_quote': 0, 'em_dash': 0, 'en_dash': 0, 'hyphen_spaced': 0}
    titles, h1s = Counter(), Counter()
    def add(url, where, sev, check, note, snippet):
        issues.append({'url': url, 'where': where, 'severity': sev, 'check': check, 'note': note, 'snippet': snippet})
    for line in open(src, encoding='utf-8'):
        p = json.loads(line); url = p['key']
        PARA = {'p','li','blockquote','dd','td'}
        text = '\n'.join(b[1] for b in p['blocks'] if b[0] in PARA)
        titles[p['title']] += 1
        for h in p['h1']: h1s[h] += 1
        chunks = {'title': p['title'], 'meta_description': p['meta_description']}
        for i, b in enumerate(p['blocks']): chunks[b[0] + '#' + str(i) + ('(collapsed)' if len(b) > 2 and b[2] == 'collapsed' else '')] = b[1]
        for where, chunk in chunks.items():
            for check, (rx, sev, note) in RX.items():
                for m in rx.finditer(chunk):
                    if check == 'repeated_word' and m.group('w').lower() in REP_OK: continue
                    if check == 'caps_word' and m.group(1) in CAPS_OK: continue
                    if check == 'no_space_after_punct' and re.search('[0-9][,:][0-9]', chunk[max(0, m.start() - 1):m.end() + 1]): continue
                    add(url, where, sev, check, note, ctx(chunk, m.start(), m.end()))
            for rx, name in CONFUSE:
                for m in rx.finditer(chunk):
                    add(url, where, 'P1', 'word_confusion', name, ctx(chunk, m.start(), m.end()))
        for blk in text.split('\n'):
            for s in [x.strip() for x in SENT.split(' '.join(blk.split())) if x.strip()]:
                if s[0].islower(): add(url, 'body', 'P2', 'lowercase_start', '', s[:200])
                if s.count('(') != s.count(')'): add(url, 'body', 'P2', 'unbalanced_bracket', '', s[:200])
                if HAS_NUM.search(s) and CLAIM_HINT.search(s): claims.append({'url': url, 'sentence': s})
                low = ' ' + s.lower() + ' '
                for uk, us in VARIANT.items():
                    if re.search(r'\b' + uk, low): style['uk'][uk] += 1
                    if re.search(r'\b' + us, low): style['us'][us] += 1
                if re.search('(?i),[ ][a-z]+[ ]and[ ]', s): style['oxford_yes'] += 1
                elif re.search('(?i)[a-z]+,[ ][a-z]+[ ]and[ ]', s): style['oxford_no'] += 1
        style['curly_quote'] += text.count('’') + text.count('“'); style['straight_quote'] += text.count("'") + text.count('"')
        style['em_dash'] += text.count('—'); style['en_dash'] += text.count('–'); style['hyphen_spaced'] += len(re.findall('[ ]-[ ]', text))
        for _, h in p['headings']:
            if TITLECASE.match(h): style['heading_title'] += 1
            elif h[:1].isupper(): style['heading_sentence'] += 1
        full = ' '.join(b[1] for b in p['blocks']) + ' ' + ' '.join(t for _, t in p.get('boilerplate', []))
        for m in EMAIL.finditer(full): claims.append({'url': url, 'sentence': 'CONTACT_EMAIL: ' + m.group(0)})
        for m in PHONE.finditer(full): claims.append({'url': url, 'sentence': 'CONTACT_PHONE: ' + m.group(0)})
    for t, n in titles.items():
        if n > 1: add('SITEWIDE', 'title', 'P1', 'duplicate_title', str(n), t)
    for t, n in h1s.items():
        if n > 1: add('SITEWIDE', 'h1', 'P2', 'duplicate_h1', str(n), t)
    for name, rows in (('issues.jsonl', issues), ('claims.jsonl', claims)):
        with open(os.path.join(out, name), 'w') as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    style['uk'] = dict(style['uk']); style['us'] = dict(style['us'])
    json.dump(style, open(os.path.join(out, 'style.json'), 'w'), indent=1)
    print('issues', len(issues), 'claims', len(claims))
main(sys.argv[1], sys.argv[2])
