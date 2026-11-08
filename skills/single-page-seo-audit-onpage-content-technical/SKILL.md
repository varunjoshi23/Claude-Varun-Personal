---
name: "single-page-seo-audit-onpage-content-technical"
description: "Audits a single landing page across on-page, content and technical signals against top-ranking SERP competitors for a primary keyword, then outputs a live fix tracker (competitor comparison plus Technical, On-page and Content sections) and, on request, a spreadsheet export. Runs one client or a batch of many with a fixed check catalog and a portfolio roll-up. Use for single page SEO audit, on-page audit, technical audit, competitor gap analysis, or \"why isn't this page ranking\"."
---

# Single Page SEO Audit: On-Page, Content and Technical

Audit one landing page against the pages currently ranking for its primary keyword, and return a prioritised gap list as a live fix tracker the client can work from. Scope is one URL per run. For site-wide work, run this per priority page.

This skill is standalone. It does not depend on the content brief, topical map or drafting skills, and it does not write page copy beyond the rewritten elements in Stage 7. It is industry-neutral and built to run the same way for many clients (see Running at scale).

## Bundled resources

Use these files instead of rewriting them on each run. They are what keep 50 audits consistent. Paths are relative to this skill's folder.

| File | Use it for |
|---|---|
| `references/checks.md` | The fixed check catalog: 51 stable IDs across Technical, On-page and Content. Every audit runs every check. |
| `scripts/parse_page.py` | Stage 1c: extracts the element set from saved raw HTML, including the heading list in order, counts, links, JSON-LD and keyword phrase counts. Every count you report comes from this output, never typed by hand. |
| `scripts/lab_vitals.js` | Stages 1d and 5: Chromium lab vitals and rendered-page checks when PageSpeed Insights is unavailable. |
| `scripts/validate_jsonld.py` | Non-negotiable 9: strict JSON-LD validation (comments, trailing commas, unresolved `@id`s, empty placeholders). |
| `scripts/check_audit.py` | Before preview, seeding or export: validates the client's `audit.json` against the catalog and the document shapes, and prints the per-section totals to use in the hand-over. |
| `scripts/preview_tracker.js` | Stage 7: renders `assets/tracker.html` with the client's data and screenshots every tab. |
| `scripts/to_db_ops.py` | Stage 7: splits `audit.json` into `db_write` batches of 50 or fewer for a new tracker. |
| `scripts/export_xlsx.py` | The spreadsheet export, with formula-driven summary counts. |
| `scripts/portfolio.py` | Running at scale: adds or updates the client's row in the portfolio workbook. |
| `assets/tracker.html` | The tracker page. Publish it unchanged. |

Run Python helpers with `python3 -I`. They need `beautifulsoup4`, `lxml` and `openpyxl`; the Node helpers need `playwright` with Chromium.

**One file per client: `audit.json`.** Collect everything the deliverable needs into a single file:

```json
{
  "meta": {
    "audit": {"client": "", "pageLabel": "", "url": "", "keyword": "", "secondary": "", "scope": "", "device": "", "date": "", "position": "", "basis": "", "method": []},
    "competitors": {"cols": [], "rows": [], "behind": {}, "note": ""},
    "outline": {"items": []},
    "rewrites": {"blocks": []}
  },
  "findings": [],
  "status": {}
}
```

The preview, the database seed, the spreadsheet export and the portfolio row are all generated from this file, so they cannot disagree. Leave `status` empty for a new audit. For an export, fill it from the live tracker. Stage 7 documents every field.

## Non-negotiables

1. Never report a check you did not actually run. Every row in the output carries a status: `Pass`, `Fail`, `Warn`, or `Not checked (reason)`.
2. Pull the raw HTML, not just rendered text. Canonical, hreflang, schema, meta robots and JS-dependency findings are invalid without it.
3. Competitors are whoever ranks today for the primary keyword, not whoever the client names.
4. Every finding needs the evidence inline: the actual title string, the actual word count, the actual canonical value. No "title needs optimisation".
5. Recommendations are rewrite-ready. Give the replacement string, not the instruction to write one.
6. Recommend subtractively first. Before proposing anything new, look for duplicated headings, repeated blocks and padding already on the page and say what to delete or demote. Cap new top-level sections at two, and prefer changes that reuse what is there. A gap list that reads as "add eight sections" is a failed audit.
7. **Scope is this one URL.** Check only what the audited page serves: its HTTP response, its HTML and markup, and the links it contains. Do not flag issues that live on other URLs, such as old post IDs that redirect elsewhere, non-www or HTTP host redirects, or another page's markup, unless the audited page links to that URL. If you notice one, mention it once in Method and limits as out of scope, never as a finding.
8. **Check the site before calling something missing.** Before recommending an entity, a schema block, business details or a claim (opening hours, "free returns", "24/7 support", "accepting new clients"), look at the site's own related pages (location, contact, about, pricing and team pages). If the data already exists there, say so, reuse it, and frame the finding as "this page doesn't use or connect to it", not "the site lacks it". Never write "only if true" when the site already answers the question.
9. **Every code recommendation must be valid and complete.** JSON-LD, robots rules, redirects and HTML snippets must work as pasted:
   - JSON has no comments, no `/* placeholders */` and no trailing commas. Parse every JSON-LD block strictly (`json.loads`) and check that every `@id` reference resolves before it goes into the deliverable.
   - Fill values from the site's own pages (addresses, geo, hours, phone, profile links). If a value cannot be found, leave the property out and say which one in the label. Do not leave a blank to fill in.
   - Present JSON-LD as one `@graph` block that states which existing blocks it replaces and which to keep.
10. **Re-count before you report.** Every number in the hand-over message (issues, passes, not checked, scores) must come from the final data, recounted after the last edit. Do not repeat a number from memory.

---

## Stage 0: Inputs and data source

Collect in one pass. If anything is missing, ask for all of it together.

**Required**
- Client name
- Landing page URL to audit
- Primary keyword (one)
- Secondary keywords (list, optional but preferred)

**Then ask the data source question** (use the multiple-choice question tool if available):

> How should I get keyword and competitor metrics?
> - **A. Ahrefs API** (needs an API token)
> - **B. Semrush API** (needs an API key)
> - **C. I will paste the data manually** (volumes, difficulty, competitor metrics)
> - **D. Skip it, derive everything from the live SERP** (no volume or DR data, gap analysis still full)

Also ask, in the same question block:
- **Targeting scope: global, or a named location.** This decides the competitor set and every recommendation, so never infer it from the client's address or an address on the page. A global target and a local target produce different competitor sets and contradictory advice.
- Target country and language for the SERP (default: client's primary market; ask if unknown)
- Device for the SERP check (default: mobile)

### Handling API credentials

Ask the user to save the token to a file or an environment variable rather than pasting it into the chat. Read it from there. If they paste it anyway, use it and never echo it back in any output, artifact, or file.

- Ahrefs v3: `GET https://api.ahrefs.com/v3/site-explorer/overview` and `/keywords-explorer/overview`, bearer token.
- Semrush: `https://api.semrush.com/` with `key=`, report types `phrase_this`, `phrase_related`, `domain_ranks`.

If an API call fails, say so in one line and continue with SERP-derived data. Never block the audit on a credential problem.

### Option C: manual data

Ask for whatever they have, in any format:
- Keyword, monthly volume, difficulty, current client position
- Competitor domains with DR/AS and page-level backlink counts

Accept a paste, a CSV, or a screenshot. Normalise it into one table before continuing.

### Option D: no tool data

Proceed. Mark every volume, difficulty and authority field `Not available (no tool data)`. The content and technical gap analysis does not depend on it. Say this plainly once, do not repeat the caveat in every section.

---

## Stage 1: Collect the client page

### 1a. Fetch raw HTML

Try in this order, stop at the first that works:

1. `curl` or Python `requests` for the raw HTML and response headers. Follow redirects and log the chain.
2. If the network blocks it, use the web fetch tool for content, and note that header-level and raw-markup checks are degraded.
3. If the page is JS-rendered or gated, use a browser tool if one is available in the session.

Expect the shell to be blocked. Sandbox egress is commonly refused for arbitrary hosts, and the PageSpeed Insights API with it. When that happens do not retry or route around it: use a browser tool and read the rendered DOM with a script, which gives headings, schema, link and image counts accurately. Record what the DOM cannot give (response headers, the redirect chain, whether body copy exists in raw HTML) as `Not checked` with the reason, and exclude those checks from the scores rather than counting them as passes.

Save the HTML to a file and parse it with a script. Do not eyeball it.

```bash
curl -sSL -D headers.txt -A "Mozilla/5.0 (compatible; SEO-audit)" "$URL" -o page.html
```

Capture from headers: final status code, redirect chain, `X-Robots-Tag`, `Content-Type`, HSTS, server-side caching hints.

### 1b. JS dependency check

Compare the raw HTML text content against the rendered text content. If the main body copy is absent from raw HTML, flag it `Critical for AI visibility`: most LLM crawlers do not execute JavaScript, so the page is effectively empty to them.

### 1c. Extract the full element set

Parse and record: title, meta description, canonical, meta robots, viewport, lang, hreflang set, OG and Twitter tags, every heading in document order with level, word count of main content, paragraph count, image count with alt text present or missing, internal link count with anchors, external link count with targets, every JSON-LD and microdata block, publish and modified dates, author block, table and list counts, FAQ or Q&A blocks, CTA elements.

Run `scripts/parse_page.py page.html <url> --keywords "<primary>;<secondary...>" --text` and keep its output; it covers every item above. Keep the full heading list in document order, H1 to H6 including footer headings, because it becomes the Content outline in Stage 4. Take every count you report (headings per level, words, links, images) from this output.

Then read the site's own pages that the audited page links to and that hold facts it should reuse: location, contact, about and team pages. Record their JSON-LD (`@id`s, address, geo, opening hours, phone, `sameAs` profile links) and any facts they state: availability, guarantees, service areas, pricing, languages, credentials. Non-negotiable 8 depends on this, and so do the JSON-LD rewrites in Stage 7.

### 1d. Page speed

PageSpeed Insights API, mobile and desktop:

```
https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=$URL&strategy=mobile&category=performance&category=seo&category=accessibility&category=best-practices
```

It works without a key at low volume; use `&key=` if the user has one. The keyless quota runs out quickly when you audit many clients. Ask for a key once per batch. When the API is unavailable, run `node scripts/lab_vitals.js <url>` and label its numbers "local lab" with the throttling profile, never as PageSpeed or field data. Record lab LCP, INP/TBT, CLS, performance score, page weight, request count, render-blocking resources, and field CrUX data if present. Field data beats lab data when both exist, say which one you are quoting.

### 1e. Indexing

- `robots.txt`: fetch and check whether the URL path is allowed, for Googlebot and for the AI crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended).
- Meta robots and `X-Robots-Tag`: look for `noindex`, `nofollow`, `noarchive`, `nosnippet`, `max-snippet`.
- Canonical: self-referencing, absolute, matching the live URL, and consistent with the sitemap entry.
- Sitemap: find it from robots.txt, confirm the URL is listed.
- Index status proxy: search `site:` plus the exact URL, and the exact title string in quotes. Treat the result as indicative only. If Search Console is connected, use it instead and say so.

---

## Stage 2: Collect the SERP and competitors

1. Search the primary keyword for the stated country, language and device.
2. Record the full SERP layout: ad count, AI Overview present or not and which domains it cites, featured snippet and its format and holder, People Also Ask questions verbatim, video pack, image pack, local pack, shopping, forum or Reddit results, sitelinks.
3. Take the **top 5 organic results that are the same page type as the client page**. Drop pure directories, aggregators and the client's own domain unless they are the actual competitive set. If the SERP is dominated by a page type the client does not match (for example all listicles against a product page), stop and say so: the primary keyword may be an intent mismatch, and that is the headline finding.
4. Record the position of every competitor and of the client page. Positions go into the Competitor comparison as their own column.
   - Label the source honestly. If the search tool is not Google, or shows no local pack, the column note must say so, and positions are "indicative".
   - Run the search a second time before you publish. If a position moved, show both (e.g. "#7, then not in top 9").
   - Name what holds the positions you dropped (directories, other page types) in the column note.
   - If the client is not found, write "Not in top N", where N is the number of results you actually saw. Never guess a number.

**Review gate.** Show the competitor list, the detected SERP intent, and the SERP feature summary in a short block. Ask whether to proceed or swap any competitor. Default to proceeding if the user does not respond or says to keep going. Keep this to one message, do not pause anywhere else in the run.

5. For each approved competitor, run Stage 1a and 1c. Speed data for competitors is optional; collect it only if the client page scores poorly, so there is a benchmark.

---

## Stage 3: On-page audit

Score the client page against each check. Record the actual value, the verdict, the competitor pattern, and the fix. The checks in Stages 3 to 5 map to the stable IDs in `references/checks.md`. Use those IDs and check names exactly, and give every catalog check a verdict.

| Check | Pass condition | Also capture |
|---|---|---|
| Title tag | Primary keyword present, ideally in the first 60 characters by pixel width, unique, under ~580px | The 5 competitor titles verbatim, and the pattern across them |
| Meta description | 140 to 160 characters, primary keyword, a reason to click, no truncation | Whether Google is rewriting it in the live SERP |
| H1 | Exactly one, contains the primary keyword or a close variant, not identical to the title | Competitor H1 formulations |
| Heading hierarchy | No skipped levels, H2s describe real sections, secondary keywords and entities distributed across them | Count of H2 and H3 vs the competitor median |
| URL | Readable, keyword present, hyphenated, no params or stop-word bloat, shallow depth | Competitor URL depth |
| First 100 words | Primary keyword appears naturally, and the query is answered | See the AI readiness block below |
| Keyword placement | Covered in title, H1, first paragraph, at least one H2, URL, one image alt, one internal anchor | Secondary keyword coverage, one row each |
| Semantic coverage | Entities, subtopics and modifiers that appear across 3+ competitors are present on the client page | Build the missing-entity list, this is the core content gap |
| Images | Every meaningful image has descriptive alt text, filenames are readable, next-gen format, explicit dimensions | Competitor image count, presence of original diagrams or screenshots |
| Internal links | Contextual links out to related money and support pages, descriptive anchors, no orphan state | Competitor internal link count and anchor style |
| External links | Cites authoritative sources for claims and statistics | Competitor citation count |
| CTA and conversion | Clear primary action above the fold and repeated, matched to intent | What competitors offer at the same point |
| Freshness | Visible published and updated date, content reflects current state | Competitor last-updated dates |

Do not report a keyword density figure, and do not set one as a target. Report coverage and placement instead.

---

## Stage 4: Content audit versus competitors

Build a side-by-side matrix: client plus the 5 competitors as columns.

**Depth and structure**
- Word count, and the competitor median and range. Frame the client number as a gap against the median, never as a target to hit.
- Section count, and which sections every competitor has that the client lacks. Name them.
- Format mix: tables, lists, images, diagrams, embedded tools, calculators, video.
- Reading level and sentence length.

**Industry expertise and E-E-A-T**
- Named author with credentials and a bio, or none.
- First-hand evidence: original data, screenshots, test results, case studies, named clients, pricing specifics.
- Claims backed by a cited source versus asserted.
- Depth markers a practitioner would notice: real numbers, edge cases, named tools, process detail, trade-offs. Generic advice is the gap to call out.
- Trust signals: reviews, certifications, awards, contact and company information.

**Keyword and intent targeting**
- Does the page type match the dominant SERP intent? Transactional, commercial, informational, navigational.
- Primary keyword targeted cleanly, or diluted across multiple pages on the client domain. Check for cannibalisation with a `site:` search on the primary keyword.
- Secondary keyword coverage: one row per keyword, present or missing, and where to place it.
- Query fan-out: the PAA questions and related searches the page does not answer.

**Industry segments and audience coverage**
- Which verticals, use cases, company sizes, geographies or personas competitors address that the client page does not.
- Which objections and comparison questions competitors handle.
- Pricing, timeline and process transparency compared across the set.

**AI readiness and AEO**

This block carries equal weight to classic on-page. Check each:

| Check | Pass condition |
|---|---|
| Answer first | The first 1 to 2 sentences directly answer the primary query, before any setup or brand preamble |
| Standalone opening summary | The opening paragraph works as an extractable 40 to 60 word answer with no dependency on surrounding context |
| Self-contained chunks | Each section stands alone when extracted: no "as mentioned above", no pronouns referring back across headings |
| Question-shaped headings | H2 and H3 match how users and LLMs phrase the query, where intent is informational |
| Definition clarity | Key terms and entities defined explicitly near first use |
| Extractable formats | Comparison tables, step lists and specification lists rather than the same content in prose |
| Direct-answer blocks | A short answer block near the top for each major question the page covers |
| Statistics and citations | Quotable figures with a named source and date |
| Schema | Valid JSON-LD for the page type, plus Organization, Author, Breadcrumb, and FAQ where genuine |
| Entity consistency | Brand, product and author names consistent with the rest of the site and with external profiles |
| Crawler access | AI crawlers not blocked in robots.txt, unless that is a deliberate client policy, in which case note it and move on |
| No-JS content | Main content present in raw HTML |

Where the client page fails one of these and competitors pass, check whether those competitors are the ones cited in the AI Overview, if one appeared on the SERP. That link is the strongest argument in the deliverable.

**Content outline**

Build the outline from the heading list in Stage 1c. It replaces any separate "heading changes" block.
- **One row per heading, in the order it appears on the live page.** Do not reorder the rows into the recommended structure.
- Each row carries:
  - `tag`: H1 to H6.
  - `text`: the current heading, verbatim.
  - `action`: exactly one of `Keep`, `Modify`, `Remove`, `Add New`.
  - `new`: the replacement heading, only when the text changes.
  - `rec`: what to do with the section, rewrite-ready and specific (what to cut, what to add, which link, which fact).
- **A section that should move stays in its real position** with action `Modify`. Its `rec` says where it moves to, and the rows it will sit above say so too. Never list a heading twice.
- **`Add New` rows sit where the new heading should go**, never at the end by default. At most two new top-level sections (non-negotiable 6). New FAQ questions are H3 rows inside the existing FAQ.
- `Remove` rows say where any useful sentence goes before the section is deleted.
- **Footer or utility headings** (labels marked up as H4, etc.) are rows too, usually `Modify`: change the tag to `<p>` or `<div>`.

---

## Stage 5: Technical audit

| Check | Pass condition |
|---|---|
| Status and redirects | 200 on the canonical URL, no chain, no redirect from the linked version |
| Canonical | Self-referencing, absolute, matches the indexed and sitemap URL, one per page |
| Indexability | No `noindex` in meta or header, allowed in robots.txt, present in the sitemap, appears indexed |
| HTTPS | Valid certificate, no mixed content, HTTP version redirects to HTTPS |
| Mobile | Responsive viewport meta, no horizontal scroll, tap targets adequate |
| Core Web Vitals | LCP under 2.5s, INP under 200ms, CLS under 0.1, on mobile field data where available |
| Page weight | Total bytes and request count, largest offenders named |
| Render blocking | Blocking CSS and JS in the head, unused payload |
| Image delivery | Compressed, lazy-loaded below the fold, LCP image not lazy-loaded, dimensions set |
| Structured data | Valid, no errors, matches visible content, eligible rich result types named |
| hreflang | Correct and reciprocal, if the site is multi-regional |
| Breadcrumbs | Present in markup and in schema |
| Internal link depth | Clicks from the homepage, and whether any internal link points to the page at all |
| Duplicate and thin | No near-duplicate on the domain targeting the same keyword |
| Pagination and faceting | Handled correctly, if applicable |
| 404 and soft 404 | Page is not a soft 404, outbound internal links on the page resolve |

Validate structured data against the actual markup you parsed, do not infer it from the rendered page.

---

## Stage 6: Prioritise

Every finding gets four fields:

- **Severity**: `Critical` blocks indexing or ranking outright, `High` is a clear competitive gap, `Medium` is an improvement, `Low` is hygiene.
- **Effort**: `S` under an hour, `M` under a day, `L` more than a day or needs dev or design.
- **Impact area**: Rankings, AI visibility, CTR, Conversion, UX, or Crawl.
- **Owner**: Content, SEO, Dev, or Design.

Sort by severity, then by effort ascending inside each severity band, so the quick critical wins sit at the top. Produce a `Do this week` list of at most 7 items from the top of that sort, for the hand-over message.

Anything that is a gap against 4 or more of the 5 competitors is at least `High`, regardless of how small it looks.

**Three sections, not four.** Every finding's `category` is exactly one of `Technical`, `On-page` or `Content`. AI readiness checks are not a fourth category. Each goes into the section it belongs to, with `ai: true` so it shows an AI tag:

| AI readiness check | Section |
|---|---|
| Schema, AI crawler access, no-JS content | Technical |
| Question-shaped headings, entity consistency (OG/Twitter, names) | On-page |
| Answer first, standalone summary, self-contained chunks, definitions, extractable formats, statistics and citations | Content |

**Verdicts:** `Pass`, `Warn`, `Fail` or `Not checked`. `Not checked` is its own verdict, never a Warn and never a Pass. Its `actual` says why the check was not run, and its `fix` says how to run it.

**No duplicate lists.** Every competitor gap must be a finding, with the competitor count in its `competitors` field. Do not also publish a separate "content gaps" list.

---

## Stage 7: Deliverable

The deliverable is a live fix tracker, not a static report. The agency and the client work from it over weeks, so viewers must be able to change status and leave notes.

Build it as a self-contained HTML page published as an artifact with the `db` and `user` capabilities. **Do not use a Dashboard artifact type for this**: viewers cannot write to one, so it cannot track anything. If the session has no artifact capability, write the page to a self-contained HTML file in the working directory with the findings inline, and say plainly that status tracking needs an artifact.

**Use the bundled template.** `assets/tracker.html` is the finished tracker page, and its layout, styling and behaviour are the standard. Publish it as it is. Change only the `<title>` text, using the same words as the artifact title. Do not redesign it, restyle it or hardcode findings into it. Every client-specific value comes from the database, so the same file serves every audit.

**Build order.**
1. Write the client's `audit.json`.
2. Run `python3 -I scripts/check_audit.py audit.json`. Fix every error; it also validates each JSON-LD rewrite.
3. Run `node scripts/preview_tracker.js assets/tracker.html audit.json <outdir>`. Look at the four tab screenshots, and fix anything that renders wrong or reports a page error.
4. Publish `assets/tracker.html` (title: "<Client>: <pageLabel> SEO audit").
5. Declare capabilities.
6. Run `python3 -I scripts/to_db_ops.py audit.json <outdir>` and send each `ops_NN.json` as one `db_write` call, about 2 seconds apart.
7. Re-read one document of each kind to confirm the writes landed.

Declare:

```json
{"db": {"rules": [
  {"path": "", "read": "view", "write": "interact"},
  {"path": "findings", "read": "view", "write": "admin"},
  {"path": "meta", "read": "view", "write": "admin"}
]}, "user": {}}
```

Findings and meta stay editor-only, so a status update cannot overwrite the audit itself.

**Documents** (the template reads exactly these shapes):
- `meta/audit`: `client`, `pageLabel` (short page name for the H1, e.g. "managed IT services page"), `url`, `keyword`, `scope`, `device`, `date`, `position` (an honest one-line label), `basis` (one line on how scores are calculated), `method` (array of paragraphs). Do not store scores: the page calculates them live from the findings.
- `meta/competitors`: `cols`, `rows`, `behind`, `note`.
  - `cols`: column headers. Required order: Page, Position*, Ranking URL, then comparison columns.
  - `rows`: `{client?: true, cells: [...]}`. The client row comes first, then competitors sorted by position.
  - `behind`: `{columnIndex: 1}` for each column where the client trails most of the set. Those client cells render red.
  - `note`: the position source and its limits, what held the dropped positions, and where the client already leads.
- `meta/outline`: `{items: [{tag, text, action, new?, rec}]}`, in page order (Stage 4).
- `meta/rewrites`: `{blocks: [{section, label, before?, text}]}`. `section` is `technical`, `on-page` or `content`, and decides which tab shows the block.
  - On-page: title, meta description, H1.
  - Content: the answer-first opening paragraph.
  - Technical: the JSON-LD `@graph` (non-negotiable 9). It replaces named existing blocks.
  - The label states the character or word count, or which blocks the JSON-LD replaces.
- `findings/<id>`: `id`, `category` (`Technical` | `On-page` | `Content`), `ai` (true for AI readiness checks), `check`, `verdict` (`Pass` | `Warn` | `Fail` | `Not checked`), `severity`, `effort`, `owner`, `impact`, `actual`, `competitors` (`n/a` when not applicable), `fix`.
  - IDs are prefixed `tc-`, `op-`, `ct-` or `ai-`.
- `status/<id>`: written by viewers: `state`, `owner`, `note`, `by`, `byName`, `at`.
- `feedback/<auto>`: written by viewers: `text`, `section`, `byName`, `at`.
- `data/users/<id>/profile`: each viewer's own display name.

**What the template renders** (it needs no edits; this is so you can describe it and check it in the preview):
1. **Header:** client, audited URL, keyword, scope, device, audit date, position label.
2. **Overall progress:** one bar counting only Fail and Warn findings, with Open, In progress, Fixed and Not doing chips. Passes and not-checked items are never in the denominator.
3. **Three score cards:** Technical, On-page, Content. Each shows its score /100, open issues and "need work of checked". Clicking a card opens that section. Below the cards is one line on how scores are calculated.
4. **Section tabs:**
   - **Competitor comparison** is the first tab and opens by default. It shows the comparison table under a one-line intro, with no repeated heading inside the tab.
   - **Technical**, **On-page** and **Content** each have:
     - their own progress bar
     - a filter bar: search, status, severity, owner, Hide done, and a "Your name" box for status stamps
     - **Issues to resolve**: a table of ID, Severity, Issue (with verdict and AI tag), Effort, Owner and Status. Clicking a row expands what is on the page now, the competitor pattern, the fix, status and owner controls, notes and a last-changed stamp.
     - **Not checked**: a separate table with the same controls, shown only when the section has any. The fix field reads "How to check it".
     - the section's **Rewritten elements**, with Copy buttons
     - **Content tab only:** the **Content outline**, filterable by action
     - **Checks passed**: a reference table, collapsed by default
   - Each tab has its own link: `#competitors`, `#technical`, `#on-page`, `#content`.
5. **Method and limits:** scope, data source, competitor selection, what was not checked and why, and what is indicative only.
6. **Send a note to Claude:** a feedback box. Read `feedback` first whenever the tracker is picked back up.

**Behaviour** (built into the template; keep it if you ever change the file): controls are gated on `user.can("data.write")` with a read-only banner; one subscription per collection; a 10-second staleness banner; notes debounced to 900 ms; one write at a time per document; correct rendering against an empty database.

**Updating a published tracker.** Edit findings and meta with `db_write` and `ifVersion`. Remove a finding only after checking `status/<id>` holds nothing the client entered. When you remove or recategorise findings, check the text of the other findings for references to them. Republish the page only when the template itself changes.

**Hand over with the access rule**, in one line: the client needs Contributor level or above to update status, and Viewer or Commenter is read-only. Include the Do this week list and the recounted totals (non-negotiable 10).

**Spreadsheet export.** When the user asks for a spreadsheet or tracking file:
1. Read the live database first (`findings`, `status`, `feedback`, `meta`) so statuses and notes are current, and refresh `audit.json` from it.
2. Run `python3 -I scripts/export_xlsx.py audit.json <Client>-<page>-SEO-audit.xlsx --tracker-url <url> --exported <date>`.
3. Run the xlsx skill's `recalc.py`. Require zero formula errors, and check that the section scores match `check_audit.py`'s totals before sending.

The workbook uses Arial and has six sheets:
- **Summary**: audit details, and a Technical / On-page / Content / Total table whose numbers are all `COUNTIFS` formulas over Findings.
- **Competitors**: the comparison with its Position column.
- **Findings**: one row per finding, with Status and Owner dropdowns, verdict and severity colours, and filters.
- **Content outline.**
- **Rewrites.**
- **Method & limits.**

---

## Running at scale (many clients)

The skill runs the same way for every client. These rules keep 50 audits consistent and comparable.

**Batch input.** For more than one client, ask for a list (a sheet, CSV or table). One row per client:
- client
- page URL
- primary keyword
- secondary keywords (semicolon-separated)
- targeting (global, or the named location)
- country
- language
- device

Ask the Stage 0 data-source question once for the whole batch, and ask for API keys once. Check the list for missing fields and ask about all of them in one message.

**Per client, the full run.** Every client gets every stage and every catalog check. Never shorten later clients to save time: if the batch is too large for one session, stop at a client boundary and say exactly which clients are done.

**Review gate in batch mode.** Do not stop for approval on each client's competitor set. Proceed with the top five same-type pages, list each client's set in the hand-over, and swap any the user rejects afterwards.

**Network.** If the sandbox blocks hosts:
- Request access once for all the batch's client domains.
- Request access once per client for its competitor domains, after Stage 2.
- Never route around a block.
- Record anything you could not reach as `Not checked`.

**One tracker per client.** Never put two clients in one tracker. Titles follow "<Client>: <pageLabel> SEO audit". Keep each client's `audit.json`, keyed by client and page, so a re-audit can update the same tracker.

**Portfolio.** After each client, run `python3 -I scripts/portfolio.py portfolio.xlsx audit.json --tracker-url <url>`. It writes one row per client and page: scores, open and fixed issues, high-severity open issues, the top three open issues, and the tracker link. Re-running a client updates its row instead of adding a duplicate. Send the portfolio at the end of the batch.

**Re-audits.** To re-audit a client:
- Re-run the stages and rebuild `audit.json` with the same IDs.
- Update the existing tracker's `findings` and `meta` with `ifVersion`. Never touch `status` or `feedback`, which belong to the client.
- Refresh the portfolio row.

**Hand-over per batch.** For each client:
- its tracker link
- the three section scores and open issues, from `check_audit.py`
- the Do this week items
- anything not checked

End with the portfolio workbook.

## Handoff

Close with a short block listing what a later stage could reuse: the approved competitor set, the missing-entity and question list, the recommended outline, and the internal link targets identified. This is a convenience only. Do not call another skill, and do not assume one will run.