// extract_pages.js — render each page in Chromium and save verbatim copy plus source-level fields.
// Usage: node extract_pages.js pages.tsv out/pages.jsonl [crawlDelaySeconds]
//   pages.tsv: one "key<TAB>absolute URL" per line (key = short page id used in the report, e.g. home, about).
// Output per page: key, url, path, title, meta_description, og_title, og_description, jsonld (raw strings),
//   h1 (array), headings [[tag,text]], blocks [[tag,text,state]], boilerplate [[tag,text]].
//   state: "visible" | "collapsed" (in the HTML but hidden behind an accordion / Read more / tab).
// Text is textContent (authored casing, not CSS text-transform), with NBSP and runs of whitespace collapsed to one space.
const { chromium } = require('playwright');
const fs = require('fs');
const [, , listFile, outFile, delayArg] = process.argv;
const delay = Math.max(0, Number(delayArg || 2)) * 1000;
const list = fs.readFileSync(listFile, 'utf8').split('\n').map(l => l.trim()).filter(Boolean).map(l => l.split('\t'));
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1366, height: 900 } });
  const out = fs.createWriteStream(outFile);
  for (const [key, url] of list) {
    const pg = await ctx.newPage();
    try { await pg.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }); await pg.waitForTimeout(2500); }
    catch (e) { console.log('ERR', key, url, e.message); await pg.close(); continue; }
    const r = await pg.evaluate(() => {
      const norm = s => (s || '').replace(/ /g, ' ').replace(/\s+/g, ' ').trim();
      // textContent keeps authored casing but drops <br>; insert a space for each <br> first.
      document.querySelectorAll('br').forEach(br => br.replaceWith(' '));
      const BLOCK = 'p,h1,h2,h3,h4,h5,h6,li,td,th,button,label,blockquote,figcaption,dt,dd,summary';
      const BOILER = 'header,footer,nav,#masthead,#colophon,[role=banner],[role=contentinfo],[role=navigation]';
      const isBoiler = el => !!el.closest(BOILER);
      const collapsed = el => { if (el.offsetParent !== null) return false; const st = getComputedStyle(el); return st.position !== 'fixed'; };
      const blocks = [], boiler = [];
      document.querySelectorAll(BLOCK).forEach(el => {
        if (el.closest('script,style,noscript,svg')) return;
        if (el.querySelector('p,h1,h2,h3,h4,h5,h6,li,td,th,blockquote')) return;
        const t = norm(el.textContent); if (!t) return;
        const tag = el.tagName.toLowerCase();
        if (isBoiler(el)) boiler.push([tag, t]);
        else blocks.push([tag, t, collapsed(el) ? 'collapsed' : 'visible']);
      });
      const meta = n => { const m = document.querySelector(`meta[name="${n}"],meta[property="${n}"]`); return m ? norm(m.content) : ''; };
      return {
        title: norm(document.title), meta_description: meta('description'),
        og_title: meta('og:title'), og_description: meta('og:description'),
        jsonld: [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => s.textContent.trim()),
        h1: blocks.filter(x => x[0] === 'h1').map(x => x[1]),
        headings: blocks.filter(x => /^h[2-4]$/.test(x[0])).map(x => [x[0], x[1]]),
        blocks, boilerplate: boiler,
      };
    });
    r.key = key; r.url = url; r.path = new URL(url).pathname;
    out.write(JSON.stringify(r) + '\n');
    console.log(key, r.blocks.length, 'blocks', r.h1.length, 'h1');
    await pg.close();
    await new Promise(res => setTimeout(res, delay));
  }
  out.end(); await b.close();
})();
