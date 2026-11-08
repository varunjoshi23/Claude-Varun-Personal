# Check catalog

Every audit runs every check below, for every client. Each check becomes one finding with exactly this `id`, `section` and `check` name. Stable IDs are what make 50 trackers comparable: the portfolio roll-up and any cross-client report match findings by `id`.

Rules:
- Every check gets a verdict: `Pass`, `Warn`, `Fail` or `Not checked`. Never drop a check.
- A check that does not apply (for example hreflang on a single-market site, or local relevance on a global target) is `Pass`, with `actual` starting "Not applicable:" and the reason.
- A client-specific extra check uses its section prefix plus `-x1`, `-x2` (e.g. `ct-x1`). Use one only when nothing below covers the issue.
- `ai: true` marks AI readiness checks, which render with an AI tag.

## Technical (`tc-`, plus AI checks)

| id | check | ai | Pass condition |
|---|---|---|---|
| tc-status | Status and redirects | | 200 on the canonical URL, no redirect chain |
| tc-canonical | Canonical | | One canonical, self-referencing, absolute, matches the sitemap |
| tc-index | Indexability | | No noindex in meta or header, allowed in robots.txt, listed in the sitemap |
| tc-gsc | Index status (Search Console) | | URL Inspection says indexed; usually `Not checked` without GSC access |
| tc-https | HTTPS / HSTS / mixed content | | Valid TLS, HSTS header, no mixed content |
| tc-mobile | Mobile rendering | | Responsive viewport, no horizontal scroll at 412px |
| tc-cwv | Core Web Vitals | | LCP < 2.5s, INP < 200ms, CLS < 0.1 (field data if available, else lab, and say which) |
| tc-weight | Page weight and render-blocking | | Reasonable bytes and requests, no render-blocking scripts in head |
| tc-imgdelivery | Image delivery | | LCP/above-fold images not lazy, below-fold lazy, dimensions set, modern formats |
| tc-breadcrumb | Breadcrumbs | | Visible trail and BreadcrumbList schema starting at Home |
| tc-depth | Internal link depth | | Linked from nav or the homepage, within 3 clicks |
| tc-links | Outbound internal links resolve | | Every internal URL linked from the page returns 200 |
| tc-dup | Near-duplicate pages | | No other page on the domain targets the same keyword with similar content |
| tc-hreflang | hreflang | | Correct and reciprocal if multi-regional, else Not applicable |
| ai-schema-entity | Primary entity schema connected to the page | yes | JSON-LD for the page's main entity (Organization, LocalBusiness subtype, Product, Service...) with full properties, connected by `@id` to the site's existing entities |
| ai-schema-faq | FAQ / Q&A schema | yes | Valid and matches visible text, if the page has an FAQ |
| ai-crawlers | AI crawler access | yes | GPTBot, ClaudeBot, PerplexityBot, Google-Extended allowed (or a deliberate policy noted) |
| ai-nojs | Content present without JavaScript | yes | Main content in raw HTML |

## On-page (`op-`, plus AI checks)

| id | check | ai | Pass condition |
|---|---|---|---|
| op-title | Title tag | | Primary keyword early, brand included if the SERP pattern has it, under about 580px |
| op-meta | Meta description | | 140–160 chars, keyword, a concrete reason to click |
| op-h1 | H1 | | Exactly one, primary keyword or close variant, not identical to the title |
| op-headings | Heading hierarchy | | No skipped levels, H2s describe real sections |
| op-url | URL | | Readable, hyphenated, no parameters, shallow |
| op-first100 | First 100 words | | Keyword appears naturally and the query is answered |
| op-kw | Primary + secondary keyword coverage | | Natural coverage across title, H1, opening, H2s; no forced exact-match strings |
| op-images | Images | | Descriptive alts, readable filenames, original images where competitors have them |
| op-internal | Internal links | | Contextual links to the related pages the copy mentions, descriptive anchors |
| op-external | External citations | | Claims and statistics link to authoritative sources |
| op-cta | CTA and conversion | | Primary action above the fold and repeated, matched to intent |
| op-fresh | Freshness | | Visible updated date; reviews, prices and dates on the page are current |
| op-markup | Markup hygiene | | No leftover template IDs, broken anchors, copied boilerplate or headings used as styling |
| ai-qheads | Question-shaped headings | yes | Headings match how people phrase the questions, where intent is informational |
| ai-entity | Entity consistency | yes | Brand, product and location names and OG/Twitter tags consistent with the rest of the site |

## Content (`ct-`, plus AI checks)

| id | check | ai | Pass condition |
|---|---|---|---|
| ct-intent | Page type vs SERP intent | | Page type matches what ranks; if not, this is the headline finding |
| ct-depth | Depth vs competitor median | | Within range of the competitor median (report the gap, never a target) |
| ct-dup | Duplicated and padded blocks | | No repeated sections, duplicate review blocks or filler |
| ct-eeat | Author / expert credentials (E-E-A-T) | | Named expert with credentials and a bio where the topic warrants it |
| ct-trust | Trust signals | | Reviews with a rating and count, certifications, guarantees, as competitors show them |
| ct-local | Local / market relevance | | Local scope: hours, areas served, landmarks. Global scope: Not applicable |
| ct-pricing | Cost and pricing transparency | | Prices, plans or how cost is decided, as far as the vertical allows |
| ct-buyerq | Key buyer questions answered | | Availability, turnaround, eligibility, guarantees: whatever competitors answer and the client already offers |
| ct-segments | Audience coverage | | Every audience segment competitors address is covered |
| ct-usp | Differentiators | | The client's real differentiators are stated early, not buried |
| ct-cannibal | Cannibalisation | | No other client page competes for the primary keyword |
| ct-paa | People Also Ask coverage | | PAA questions answered on the page; `Not checked` if PAA isn't visible to you |
| ai-answer | Answer first | yes | First 1–2 sentences answer the query before any preamble |
| ai-summary | Standalone 40–60 word opening summary | yes | Opening paragraph works when extracted on its own |
| ai-chunks | Self-contained chunks | yes | No "as mentioned above"; sections stand alone |
| ai-defs | Definition clarity | yes | Key terms defined near first use |
| ai-formats | Extractable formats (tables, lists) | yes | Comparisons, steps and specs as tables or lists |
| ai-stats | Statistics with named source | yes | Quotable figures with source and year |
