#!/usr/bin/env node
// Preview the tracker locally with audit.json as mock data, before publishing.
// Usage: node preview_tracker.js ../assets/tracker.html audit.json outdir
// Writes outdir/preview.html and one full-page screenshot per tab (competitors, technical, on-page, content),
// and prints per-tab counts plus any page errors. Fix every error before publishing.
const fs = require('fs'), path = require('path'), { chromium } = require('playwright');
const [tpl, auditPath, out] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const A = JSON.parse(fs.readFileSync(auditPath, 'utf8'));
const data = { meta: A.meta, findings: Object.fromEntries(A.findings.map(f => [f.id, f])), status: A.status || {}, feedback: {} };
const mock = `window.claude={use:async n=>n==='db'?DB:n==='user'?{id:async()=>'preview',can:async()=>true}:null};const DATA=${JSON.stringify(data).replace(/</g, '\\u003c')};const snap=c=>({docs:Object.entries(DATA[c]||{}).map(([id,v])=>({id,exists:true,data:()=>v})),metadata:{fromCache:false}});const DB={collection:c=>({onSnapshot:n=>{setTimeout(()=>n(snap(c)),30);return()=>{}},add:async()=>{}}),doc:p=>({get:async()=>({exists:false}),set:async()=>{},onSnapshot:()=>()=>{}})};`;
const html = fs.readFileSync(tpl, 'utf8').replace('<script>', '<script>' + mock + '</script>\n<script>');
const pv = path.resolve(out, 'preview.html'); fs.writeFileSync(pv, html);
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  const report = {};
  for (const tab of ['competitors', 'technical', 'on-page', 'content']) {
    await p.goto('file://' + pv + '#' + tab); await p.waitForTimeout(500);
    report[tab] = await p.evaluate(() => ({
      issues: (document.getElementById('cissues') || {}).textContent, notChecked: (document.getElementById('cnc') || {}).textContent,
      passed: (document.getElementById('cpass') || {}).textContent, compRows: document.querySelectorAll('#bextra table tbody tr').length,
      outlineRows: document.querySelectorAll('.ol-row').length, rewriteBlocks: document.querySelectorAll('.rw').length,
      scores: [...document.querySelectorAll('.scorecard .big')].map(x => x.textContent)
    }));
    await p.screenshot({ path: path.join(out, `tab-${tab}.png`), fullPage: true });
  }
  console.log(JSON.stringify({ preview: pv, report, errors: errs }, null, 1));
  await b.close(); process.exit(errs.length ? 1 : 0);
})();
