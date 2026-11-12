# Segment catalog

Every audit has the same five segments in this order. Run every check in each segment on every page in scope. A check with nothing to report produces no item; do not pad.

## Impact rubric

| Impact | Use when |
|---|---|
| **High** | A customer, a regulator or an AI system could come away with a wrong fact about the business, its offer, its legal/clinical/financial content, or a contact route; or the issue is a compliance exposure (inconsistent testimonial attributions, unverifiable awards, guarantees, placeholder text live). |
| **Medium** | Weakens trust or entity consistency without stating a wrong fact: name/format drift, title-suffix patterns, errors in H1/H2/title/CTA/boilerplate, grammar that changes or blurs meaning, structural problems that block clean extraction. |
| **Low** | Body-copy mechanics and style drift that a careful reader notices but that do not change meaning. |

## 1. Brand name & identity (`id: brand`, layout `cards`)

Blurb: "How the business, its people and its positioning are named across visible copy, titles, meta tags and schema."

- Every spelling, spacing, casing and legal-suffix variant of the business name (e.g. "P.C" vs "P.C.", "Digital Liner" vs "Digitaliner", ALL CAPS in running text). Count and list them with pages.
- Page-title brand suffix patterns (how many patterns, which pages break them).
- Founder / key people: name variants between visible copy, bios, titles and `Person` schema; missing H1 or Person schema on profile pages.
- Leftover branding from another location, client, template or sister business (another city, another brand name, "Your Company").
- Positioning statement drift: the one-line "who we are" changes between pages (e.g. "SEO agency in California" vs "in the USA"; "only partition" vs full-service).
- Footer, header and CTA boilerplate: typos here repeat on every page; report once with the page count.
- Schema `name` / `alternateName` / `logo` vs visible name.

## 2. Business claims & firm facts (`id: claims`, layout `cards`)

Blurb: "Numbers, dates, offices, fees and scope claims compared across pages. Where values conflict the client decides the true figure; this report doesn't pick one."

Build a claim ledger first (grouped by subject, normalised: "50+ years" = "five decades"). Then one item per subject with conflicts:

- Years in business / experience vs founding year (show the arithmetic against today's date).
- Client, case, project, review counts; currently-open matters; team size; office count; locations; service area.
- Fees and pricing: free vs paid consultation, starting prices, contract terms, setup fees, guarantees, refund terms, payment model.
- Process claims: number of steps, timelines ("results in 3 months" vs "6–12 months").
- Scope: "we only do X" vs pages offering Y.
- Results and case-study figures: hub vs detail page, title vs body (#1 vs top 3), tiles that match no case study.
- Testimonials and reviews: the same quote attributed to different people/titles/companies; ratings in schema but not on the page; review counts that differ. Mark `review` (endorsement compliance); never edit the quote.
- Awards, certifications, memberships, partner badges: named, dated and verifiable? Otherwise `review`.
- Unsourced statistics and conflicting versions of the same statistic (95% vs 75%). Conflicts are `decision`; unsourced ones are `review`.
- Contact details: phone numbers, emails, addresses, hours: value conflicts are High `decision`; format-only drift is Low `finding`.
- Credentials and titles of people worded differently per page.

## 3. Industry-content consistency (`id` and name chosen per industry, layout `cards`)

The segment where two pages give different answers to the same subject-matter question. AI tools quote these as facts, so they are usually the highest-risk items for regulated industries. Name it for the industry:

| Industry | Segment name | Typical checks | `review_label` |
|---|---|---|---|
| Law firm | Legal-content consistency | statute/section numbers, act names, case names, procedure steps, timelines, how proceeds/damages are divided | Attorney / ethics review |
| Healthcare / dental / med spa | Clinical-content consistency | treatment descriptions, recovery times, candidacy, risks, pricing per treatment, credentials | Clinical review |
| Finance / insurance | Product & compliance consistency | rates, fees, eligibility, disclosures, regulated terms | Compliance review |
| Agency / SaaS / B2B services | Service & offer consistency | what each service includes, deliverables, process steps, reporting cadence, how a tool/AI is used, platform lists, copy pasted onto the wrong service page | Specialist review |
| Ecommerce / retail | Product & policy consistency | shipping, returns, warranty, sizing, materials, stock claims | Specialist review |
| Local trades / home services | Service & policy consistency | service area, call-out fees, guarantees, licensing, emergency availability | Specialist review |

Also check: FAQ answers on one page contradicting body copy on another; the same explainer duplicated with a location swapped in; definitions that change.

## 4. Content & grammar (`id: grammar`, layout `grammar`)

Blurb: "Errors in the business's own copy. Client testimonials and quoted third-party text are excluded and left as written."

- One `kind: "grammar"` item per error: exact current text → corrected text. Impact Medium when it is in a title, H1/H2, CTA, form, boilerplate, or changes meaning; otherwise Low.
- Covers: typos, agreement, tense, articles, prepositions, fragments, run-ons, comma splices, dangling modifiers, wrong word (then/than, its/it's), apostrophes, capitalisation, hyphenation of compound modifiers, unclosed brackets, missing end punctuation, truncated headings, headings that don't match their section, copy that belongs to another page.
- Confirm every `qa_scan.py` candidate by reading; drop false positives silently.
- Finish with one `kind: "finding"` item, "Style conventions to standardize", summarising the majority conventions and the minority usages (spelling system, Oxford comma, heading case, dash style, quote style, number/date/price/phone formats, term spelling such as ecommerce variants), with counts.

## 5. AI-quotability & answer readiness (`id: ai`, layout `ai`)

Blurb: "What makes it hard for ChatGPT, Perplexity, Google AI Overviews and similar tools to lift a clean, accurate answer from these pages."

The readability table renders from metrics.json. Items:

- FAQ answers that don't answer the question in the first sentence.
- Raw markdown, shortcodes, template tokens or placeholder text visible on the page.
- Boilerplate share: pages where most paragraph text repeats sitewide (from metrics.json `boiler`).
- Important copy hidden behind Read more / accordions (`collapsed`).
- Duplicate passages across pages with a location or service swapped in.
- Long sentences and dense blocks (metrics: avg > 20, > 10% over 30 words, Flesch < 50).
- Idioms, slogans and quotes that carry no facts; misattributed quotes.
- Undated "new", "latest", "this year" claims; years in titles that will go stale.
- Weak structure: missing or multiple H1s, pages with no H2s, non-descriptive link text ("click here").
- Schema that doesn't carry the facts that conflict on the page (no telephone, address, foundingDate, founder, areaServed, sameAs), so AI systems fall back on inconsistent copy.

## Top 5

Pick the five items with the highest impact × reach (number of pages). Each line is imperative and names the concrete conflict, e.g. "Decide whether consultations are free or paid. Every page says \"Book a Free Consultation\", but /civil-litigation/ says they are paid in advance."
