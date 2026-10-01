# SEO Industry Keywords: Clusters & Site Architecture

Sorts the ~130k SEO industry keywords into website sections, target pages and suggested URLs.
Irrelevant keywords (non-English, Korean celebrities named "Seo", adult, spam domains) are flagged.

- `SEO_Keyword_Clusters_Site_Architecture.xlsx`: the deliverable (Read Me, Summary, Site Architecture, Keyword Clusters, Irrelevant & Review)
- `scripts/geo.py`: place-name gazetteer (GeoNames cities, US states/counties, USPS towns)
- `scripts/classify.py`: rule-based classifier (relevance, section, cluster, intent, location, industry, service, tool brand)
- `scripts/build.py`: blog post-topic splitting and Excel export

Rebuild: `pip install openpyxl pandas wordfreq geonamescache zipcodes`, export the source keywords to `kw.csv`, then run `python classify.py && python build.py`.
