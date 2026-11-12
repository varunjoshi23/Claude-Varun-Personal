---
name: "sitewide-content-qa-grammar-claims-consistency"
description: "Audits a website's key pages for where the site contradicts itself: brand-name variants, conflicting business claims (years, prices, counts, contact details, testimonials, awards), conflicting industry content, grammar errors, and how cleanly AI answer engines can quote the copy. Outputs a segmented consistency report artifact with verbatim evidence, impact ratings, a decisions list and a readability snapshot. Use for content consistency audits, content inconsistency audits, site proofreading, copy QA, claim consistency or editorial audits."
---

# Sitewide Content Consistency Audit

Read the key pages of one website and report **where the site contradicts itself**, in five fixed segments:

1. **Brand name & identity**
2. **Business claims & firm facts**
3. **Industry-content consistency** (named for the industry, e.g. Legal-content consistency)
4. **Content & grammar**
5. **AI-quotability & answer readiness**

The deliverable is a **segmented report artifact** built from `assets/report_template.html`: an overview (segment cards, top 5 fixes, a page × segment heatmap), one section per segment of grouped findings with verbatim evidence, a decisions list, and a scope & method section. It is a report a client reads, not a row-per-error tracker.

This skill reports and recommends. It does not rewrite pages and never decides which conflicting value is true.

## Bundled resources

Paths are relative to this skill's folder. Use them; do not rewrite them per run.

| File | Use it for |
|---|---|
| `references/segments.md` | The check catalog for all five segments, the High/Medium/Low rubric, industry naming for segment 3, and how to pick the top 5. Read it before Step 4. |
| `references/report_data_schema.md` | The exact shape of `report_data.json`. Read it before Step 6. |
| `scripts/extract_pages.js` | Step 2: renders each page in Chromium; saves verbatim body blocks (visible vs collapsed), header/footer boilerplate, title, meta description, Open Graph, raw JSON-LD and H1s. |
| `scripts/qa_scan.py` | Step 3: mechanical candidates (spacing, punctuation, repeated words, placeholders, word confusions), claim-sentence candidates, contact strings, style tallies. |
| `scripts/readability.py` | Step 3: per-page sentences, average and longest sentence, % over 30 words, Flesch ease, boilerplate share, H1 count. |
| `scripts/verify_quotes.py` | Step 7: every evidence quote must match the cited page word for word. Blocks the build on any failure. |
| `scripts/build_report.py` | Step 7: validates the data against the schema and fills the template. |
| `assets/report_template.html` | The report layout. Never hand-write the report HTML. |

## Hard rules

- **Verbatim or nothing.** Every evidence quote is copied from `pages.jsonl`, not retyped from memory, and passes `verify_quotes.py` against the page it cites. If it can't be quoted exactly, drop it.
- **Group, don't list.** One finding per problem, with every instance as an evidence row (page + quote + source). Seven spellings of the brand name are one finding with seven rows.
- **Never pick the true value.** Conflicting facts become `kind: "decision"` items. The recommendation says what to standardise once the client decides.
- **Leave other people's words alone.** Don't grammar-correct testimonials, reviews, quoted court opinions, statutes or third-party quotes. Inconsistent *attributions* of a testimonial are still a claims finding.
- **Every finding says why it matters.** For customers, and for search/AI systems that consolidate entities and quote facts.
- **Regulated content gets a specialist flag, not a verdict.** Legal, clinical and financial contradictions are flagged for the client's professionals (`kind: "review"`) with a disclaimer in the scope section.
- **Count every page.** State pages reviewed, pages not reviewed, and why.

## Step 0: Inputs

Ask once (AskUserQuestion), or use the defaults in brackets if the user is unavailable:

1. Pages: [15 key pages: home, about, contact, the main service/practice hubs and pages, team/bio, reviews, the top location pages, 1–2 case studies or FAQs].
2. Known canonical facts, if the client has them: founding year, years of experience, counts, prices, phone/email/address, legal name, founder name and title. These turn decisions into checks.
3. Industry, if not obvious, so segment 3 is named and scoped correctly.

## Step 1: Page inventory

- Read `/robots.txt` first: note any `Crawl-delay` and disallowed paths, and the sitemap location. Fetch the sitemap(s) and expand nested sitemaps.
- Pick the pages in scope and give each a short key (`home`, `about`, `contact`, `elijah-underwood`, `los-angeles`). Write `pages.tsv` (`key<TAB>url`).
- Record what was left out (count and type, e.g. "about 300 more URLs, mostly city pages and blog posts"). If the sample suggests a template problem (a city name swapped in, a doubled passage), say which unreviewed pages are worth checking next.

## Step 2: Extract verbatim copy

```
node scripts/extract_pages.js pages.tsv out/pages.jsonl <crawl-delay seconds, default 2>
```

Respect the robots.txt crawl delay. The script uses `textContent`, so quotes keep the authored casing even when CSS displays text in capitals, and NBSP is normalised to a space. Blocks hidden behind Read more, accordions or tabs are kept and marked `collapsed`: they are crawlable, so they count, but label them in evidence (`src: "collapsed"`).

If a page fails to render, retry once, then list it under "not reviewed".

## Step 3: Deterministic passes

```
python3 -I scripts/qa_scan.py out/pages.jsonl out/scan
python3 -I scripts/readability.py out/pages.jsonl out/metrics.json
```

`qa_scan.py` output is candidates only. `readability.py` output goes into the report as is (segment 5 table).

## Step 4: Read every page and build the segments

Read `references/segments.md`, then read every page's blocks, boilerplate, title, meta, Open Graph and JSON-LD in full. Work segment by segment across all pages rather than page by page, so variants are compared side by side:

1. **Brand**: list every name variant with counts; compare title suffixes; compare people's names in copy and schema; find leftover branding from another location or template.
2. **Claims**: build the claim ledger grouped by subject (normalise "10+ years" = "a decade"), then one item per subject that conflicts, with the arithmetic shown for founding-year vs years-of-experience.
3. **Industry content**: compare the answers different pages give to the same subject question.
4. **Grammar**: one item per confirmed error, current → corrected; clear every scan candidate; end with the "Style conventions to standardize" finding using the style tallies.
5. **AI-quotability**: use metrics.json plus the reading pass.

Assign impact using the rubric. Mark `decision` / `review` / `finding` / `grammar` per the schema.

## Step 5: Overview content

- Each segment gets a one-line `verdict` for its overview card (e.g. "Seven spellings of the firm name, two names for the founder, and leftover Sacramento copy.").
- Write the **top 5 to fix first**: highest impact × number of pages, each an imperative sentence naming the concrete conflict.
- The heatmap is computed by the template from evidence page keys; nothing to write.

## Step 6: Write report_data.json

Follow `references/report_data_schema.md` exactly. Fill the `meta` block:

- `kicker`: `Content inconsistency audit · <domain> · <date>`
- `headline`: `<Client name>: where the site contradicts itself`
- `lede`: first person, plain: what was read and compared, plus "All {N} quoted snippets were checked word-for-word against the live pages."
- `method`: how pages were fetched (crawl delay respected), rendered in Chromium, what "collapsed section" means, that titles/meta/Open Graph/JSON-LD were read from source, that testimonials and third-party quotes were not grammar-checked, how readability and boilerplate share are measured.
- `not_reviewed`: count and type of excluded URLs, and which are worth checking next.
- `disclaimer`: for legal, medical or financial sites only ("Not legal advice. Points about citations and statutes flag internal inconsistencies for the firm's attorneys to confirm; they are not legal conclusions.").

## Step 7: Verify, build, publish

```
python3 -I scripts/verify_quotes.py out/pages.jsonl out/report_data.json
python3 -I scripts/build_report.py out/report_data.json out/metrics.json out/report.html
```

Fix or remove every quote that `verify_quotes.py` rejects, and rerun until it passes; never publish with failures. Then publish `out/report.html` as an artifact titled `<Client>: content inconsistency audit`. Load it once in Chromium to confirm there are no console errors before publishing.

In chat, give the link and a short summary: the counts per segment, the High items, and the decisions the client must make. Don't paste the findings into chat.

## Writing style for findings

- Title states the problem plainly with the count where useful: `"P.C" without its final period appears 14 times on 7 pages`.
- "Why it matters" connects to customers *and* to entity/AI consolidation (name matching, quoted facts, schema).
- Recommendations are concrete and copy-ready: the exact standard wording, where to apply it (copy, titles, meta, schema), and counts by page when it's a find-and-replace.
- Plain English, no jargon a business owner wouldn't use.

## Handoff

Rewrites go to the site's content skill. Technical and on-page SEO issues found along the way (missing titles, thin pages, Core Web Vitals) go to the single-page SEO audit skill; mention them in `not_reviewed` or `method` only if they affect this report's reading.
