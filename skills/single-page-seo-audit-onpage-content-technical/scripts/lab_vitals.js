#!/usr/bin/env node
// Lab page checks in Chromium, for when PageSpeed Insights is unavailable.
// Usage: node lab_vitals.js URL [URL...]
// Emulates a throttled mobile device (Moto G4 profile, 4x CPU, ~1.6 Mbps, 150 ms RTT) and prints one JSON line
// per URL: status, TTFB, FCP, LCP (+ element), CLS, load, requests, KB, largest resources, rendered main-content
// words, H1s, above-the-fold CTAs, horizontal scroll. Label these as "local lab", never as field data.
const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch();
  for (const u of process.argv.slice(2)) {
    const ctx = await b.newContext({ ...devices['Moto G4'] });
    const p = await ctx.newPage();
    const c = await ctx.newCDPSession(p);
    await c.send('Network.enable');
    await c.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 1.6 * 1024 * 1024 / 8, uploadThroughput: 750 * 1024 / 8 });
    await c.send('Emulation.setCPUThrottlingRate', { rate: 4 });
    let bytes = 0, reqs = 0; const urls = {}, sizes = [];
    c.on('Network.responseReceived', e => { urls[e.requestId] = e.response.url; });
    c.on('Network.loadingFinished', e => { bytes += e.encodedDataLength; reqs++; sizes.push([e.encodedDataLength, urls[e.requestId] || '']); });
    await p.addInitScript(() => {
      window.__cls = 0; window.__lcp = null;
      new PerformanceObserver(l => { for (const e of l.getEntries()) window.__lcp = { t: e.startTime, el: e.element ? (e.element.tagName + ' ' + (e.element.currentSrc || e.element.innerText || '').slice(0, 60)) : null }; }).observe({ type: 'largest-contentful-paint', buffered: true });
      new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; }).observe({ type: 'layout-shift', buffered: true });
    });
    try {
      const r = await p.goto(u, { waitUntil: 'load', timeout: 120000 });
      await p.waitForTimeout(3000); await p.mouse.wheel(0, 3000); await p.waitForTimeout(1500);
      const d = await p.evaluate(() => {
        const n = performance.getEntriesByType('navigation')[0];
        const m = document.querySelector('main') || document.body;
        return {
          ttfb: Math.round(n.responseStart), fcp: Math.round((performance.getEntriesByName('first-contentful-paint')[0] || {}).startTime || 0),
          lcp: window.__lcp ? { ms: Math.round(window.__lcp.t), element: window.__lcp.el } : null, cls: +window.__cls.toFixed(3), load: Math.round(n.loadEventEnd),
          renderedWords: m.innerText.split(/\s+/).filter(Boolean).length,
          h1: [...document.querySelectorAll('h1')].map(h => h.innerText.trim()),
          aboveFoldCTAs: [...document.querySelectorAll('a,button')].filter(a => { const r = a.getBoundingClientRect(); return r.top < innerHeight && r.width > 0 && /(book|appoint|call|schedule|request|buy|start|contact|quote|demo|trial|sign up)/i.test(a.innerText + ' ' + (a.href || '')); }).map(a => a.innerText.trim().slice(0, 40)),
          horizontalScroll: document.documentElement.scrollWidth > innerWidth + 1
        };
      });
      sizes.sort((x, y) => y[0] - x[0]);
      console.log(JSON.stringify({ url: u, status: r.status(), ...d, requests: reqs, KB: Math.round(bytes / 1024), largest: sizes.slice(0, 5).map(x => [Math.round(x[0] / 1024) + 'KB', x[1].slice(-80)]) }));
    } catch (e) { console.log(JSON.stringify({ url: u, error: e.message.slice(0, 200) })); }
    await ctx.close();
  }
  await b.close();
})();
