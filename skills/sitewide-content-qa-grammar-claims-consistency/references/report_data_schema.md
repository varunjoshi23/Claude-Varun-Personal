# report_data.json schema

`build_report.py` validates this and refuses to build on any violation. `verify_quotes.py` checks every `evidence.quote` against `pages.jsonl`.

```json
{
  "meta": {
    "client": "Acme Dental, PLLC",                       // legal/brand name as the client uses it
    "domain": "acmedental.com",                          // no scheme, no trailing slash
    "date": "12 November 2026",
    "kicker": "Content inconsistency audit · acmedental.com · 12 November 2026",
    "headline": "Acme Dental: where the site contradicts itself",
    "lede": "I read 15 core pages and compared every brand mention, business claim and service explanation across them. I also checked the copy for grammar and for how easily AI answer engines can quote it accurately. All {N} quoted snippets were checked word-for-word against the live pages.",
    "glance": "Findings by segment. \"High\" means a customer or an AI system could come away with a wrong fact about the business.",
    "decisions_heading": "Decisions the practice needs to make",
    "decisions_blurb": "These are facts only the practice can confirm. Once confirmed, use the same wording in page copy, meta descriptions and schema. Checkbox state isn't saved.",
    "review_label": "Clinical review",                   // tag text on kind:"review" cards (e.g. Attorney / ethics review, Clinical review, Compliance review)
    "not_reviewed": "About 40 more sitemap URLs, mostly blog posts and location pages. …",
    "method": "Pages were fetched with … then rendered in Chromium. …",
    "disclaimer_label": "Not clinical advice.",           // optional; omit both for non-regulated sites
    "disclaimer": "Points about treatments flag internal inconsistencies for the practice's clinicians to confirm.",
    "footer": "Prepared as a content QA review. Quotes are reproduced exactly from acmedental.com as rendered on 12 November 2026."
  },
  "pages": { "home": "/", "about": "/about-us/", "contact": "/contact-us/" },   // key -> path; keys match pages.jsonl "key"; order = heatmap order
  "top5": ["…", "…", "…", "…", "…"],                     // exactly 5, imperative, each names the concrete conflict
  "segments": [
    {
      "id": "brand", "name": "Brand name & identity", "short": "Brand",   // short = heatmap column label (optional)
      "layout": "cards",                                 // cards | grammar | ai
      "blurb": "One sentence on what this segment compares.",
      "verdict": "One-line summary shown on the overview card.",
      "items": [
        {
          "title": "The firm's legal name is written seven different ways",   // a finding, stated as the problem
          "impact": "High",                              // High | Medium | Low
          "kind": "finding",                             // finding | decision | review | grammar
          "evidence": [
            {"page": "home", "quote": "Underwood Law Firm, P.C.", "src": "text"}
          ],
          "why": "Why it matters, for customers and for AI/search systems.",   // required except kind:grammar
          "rec": "Concrete recommendation. For kind:grammar, the corrected text only.",
          "note": ""                                     // optional: verification note, counts, caveats
        }
      ]
    }
  ]
}
```

## Field rules

- `evidence.src`: `text` (visible body copy), `collapsed` (in the HTML but hidden behind Read more / accordion / tab), `title`, `meta` (meta description), `og` (Open Graph), `schema` (JSON-LD, quote the raw fragment e.g. `"@type":"Person"`), `boiler` (header/footer), `html` (other source-only text), `alt` (image alt).
- One finding groups every instance of the same problem. Seven spellings of a name is one finding with seven evidence rows, not seven findings.
- Quote the shortest exact span that proves the point (usually 4–15 words). Use `…` only to join two fragments from the same page.
- `kind: "decision"`: values conflict and only the client can say which is true. `rec` says what to standardise once decided; never pick the value.
- `kind: "review"`: needs a specialist (attorney, clinician, compliance) or ethics check: superlatives, guarantees, "specialist" claims in regulated industries, citations, unsourced statistics.
- `kind: "grammar"`: one row in the grammar table. `title` = the short snippet, `evidence[0]` = the exact current text, `rec` = the corrected text only. Add more evidence rows if the identical error repeats on other pages.
- Segment `layout`: segment 4 (Content & grammar) uses `grammar`; segment 5 (AI-quotability) uses `ai` (renders the readability table from metrics.json); the others use `cards`.

## metrics.json

Produced by `scripts/readability.py`. One object per page: `page, sentences, avg, max, over30, flesch, boiler, h1`. Page keys must equal the keys in `pages`.
