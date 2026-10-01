"""Build a location gazetteer: phrase -> (location label, location type)."""
import unicodedata, re
import geonamescache
from wordfreq import zipf_frequency as zf

gc = geonamescache.GeonamesCache()

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9 ]', ' ', s.lower()).strip()

US_STATES = {norm(v['name']): k for k, v in gc.get_us_states().items()}
US_STATES['washington dc'] = 'DC'
STATE_ABBR = {v.lower(): norm(gc.get_us_states()[v]['name']) if v in gc.get_us_states() else 'district of columbia'
              for v in US_STATES.values()}
# 2-letter abbreviations that collide with common words / seo jargon
AMBIG_ABBR = {'in', 'or', 'me', 'oh', 'hi', 'ok', 'al', 'la', 'co', 'de', 'pa', 'ma', 'id', 'mo', 'md', 'ar', 'ga', 'mt', 'ne', 'sc', 'ms', 'wa', 'va', 'ut', 'ct', 'nd', 'sd', 'ia', 'mi', 'dc'}
SAFE_ABBR_END = {k for k in STATE_ABBR} - {'in', 'or', 'me', 'hi', 'ok', 'id', 'ar', 'ne', 'ia', 'mt', 'ms', 'nd', 'sd', 'co', 'de'}

COUNTRIES = {norm(c['name']): c['name'] for c in gc.get_countries().values()}
COUNTRIES.update({'usa': 'United States', 'us': 'United States', 'america': 'United States', 'uk': 'United Kingdom',
                  'england': 'United Kingdom', 'scotland': 'United Kingdom', 'wales': 'United Kingdom',
                  'britain': 'United Kingdom', 'uae': 'United Arab Emirates', 'emirates': 'United Arab Emirates',
                  'europe': 'Europe', 'asia': 'Asia', 'africa': 'Africa', 'latin america': 'Latin America',
                  'middle east': 'Middle East', 'ireland': 'Ireland', 'nz': 'New Zealand'})
for amb in ['turkey', 'chad', 'jordan', 'georgia', 'guinea', 'niger', 'us']:
    COUNTRIES.pop(amb, None)
COUNTRIES['united states'] = 'United States'

CANADA_PROV = {norm(x): x for x in ['Ontario', 'Quebec', 'British Columbia', 'Alberta', 'Manitoba', 'Saskatchewan',
                                     'Nova Scotia', 'New Brunswick', 'Newfoundland']}
AUS_STATES = {norm(x): x for x in ['New South Wales', 'Victoria', 'Queensland', 'Tasmania', 'Western Australia',
                                    'South Australia', 'Gold Coast', 'Sunshine Coast']}
UK_REGIONS = {norm(x): x for x in ['London', 'Yorkshire', 'Kent', 'Essex', 'Surrey', 'Sussex', 'Cornwall', 'Devon',
                                    'Lancashire', 'Cheshire', 'Hampshire', 'Berkshire', 'Hertfordshire', 'Midlands',
                                    'West Midlands', 'East Midlands', 'Norfolk', 'Suffolk', 'Dorset', 'Somerset',
                                    'Wiltshire', 'Cumbria', 'Northumberland', 'Oxfordshire', 'Buckinghamshire']}
US_AREAS = {norm(x): x for x in ['Long Island', 'Bay Area', 'Silicon Valley', 'Inland Empire', 'Orange County',
                                  'South Florida', 'North Jersey', 'South Jersey', 'Central Florida', 'Hampton Roads',
                                  'Twin Cities', 'Tri Cities', 'Upstate New York', 'Westchester', 'Brooklyn',
                                  'Manhattan', 'Queens', 'Bronx', 'Staten Island', 'Hollywood', 'Lower Mainland',
                                  'Hilton Head', 'Lake Wylie', 'Rhode Island', 'North Carolina', 'South Carolina',
                                  'Dallas Fort Worth', 'Dfw', 'Nyc', 'La', 'Socal', 'Norcal', 'Long Beach',
                                  'Palm Beach', 'West Palm Beach', 'Boca Raton', 'Fort Lauderdale', 'Coral Springs',
                                  'Sutherland Shire', 'Main Line', 'Cape Cod', 'Outer Banks', 'Gulf Coast',
                                  'Space Coast', 'Treasure Coast', 'North Shore', 'South Shore', 'East Bay',
                                  'Peninsula', 'Delhi Ncr', 'Ncr', 'Kochi', 'Gurgaon', 'Noida']}
CC = {'GB': 'UK', 'AU': 'Australia', 'CA': 'Canada', 'IN': 'India', 'NZ': 'New Zealand', 'IE': 'Ireland',
      'AE': 'UAE', 'SG': 'Singapore', 'ZA': 'South Africa', 'PH': 'Philippines', 'PK': 'Pakistan', 'MY': 'Malaysia',
      'DE': 'Germany', 'FR': 'France', 'ES': 'Spain', 'IT': 'Italy', 'NL': 'Netherlands', 'BD': 'Bangladesh',
      'NG': 'Nigeria', 'KE': 'Kenya', 'MX': 'Mexico', 'BR': 'Brazil'}
def strip(x):
    return unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode()
ABBREV_CITIES = {'nyc': 'New York City, NY', 'new york city': 'New York City, NY', 'new york': 'New York City, NY',
                 'la': 'Los Angeles, CA', 'dfw': 'Dallas, TX', 'dallas fort worth': 'Dallas, TX', 'sf': 'San Francisco, CA',
                 'okc': 'Oklahoma City, OK', 'slc': 'Salt Lake City, UT', 'atl': 'Atlanta, GA', 'philly': 'Philadelphia, PA',
                 'vegas': 'Las Vegas, NV', 'nola': 'New Orleans, LA', 'kc': 'Kansas City, MO', 'dc': 'Washington, DC',
                 'washington dc': 'Washington, DC', 'manhattan': 'New York City, NY', 'brooklyn': 'New York City, NY',
                 'queens': 'New York City, NY', 'bronx': 'New York City, NY', 'staten island': 'New York City, NY',
                 'socal': 'Southern California', 'norcal': 'Northern California', 'ncr': 'Delhi NCR'}

# single-word city names that are ordinary English / SEO words -> never treat as a place
CITY_STOP = set('''mobile orange commerce university page split best ranking marketing digital content search
google online local national global center central union independence liberty victory progress providence
concord harmony enterprise bristol chester reading bath sale bury march mission plano normal opportunity
temple gary troy irving tyler ontario surprise vista spring springs city town lake bay beach park hill valley
moore lawrence florence auburn columbia madison jackson lincoln franklin hamilton washington clinton marion
salem garland pearland frisco allen jordan aurora mesa paradise deltona brownsville homestead sunrise weston
cary layton orem bend eugene logan murray olympia richland kent santa rio san los del el la las de nice
mons como bar most aba sur ede best taxi gap cap pau lens guide link title meta rank site sites start tool
tools york new seo north south east west port fort mount saint st grand royal long little upper lower
industry builder pro plus prime trade gold silver media tech data network value one solutions win ads cork
dover reading wells mansfield newport kingston cambridge oxford stockton warren pasadena manchester''' .split())
BIG_CITIES_KEEP = {'manchester', 'cambridge', 'oxford', 'pasadena', 'columbia', 'madison', 'jacksonville', 'aurora',
                   'mesa', 'frisco', 'plano', 'eugene', 'salem', 'bristol', 'reading', 'kent', 'richland',
                   'orem', 'logan', 'tyler', 'irving', 'garland', 'pearland', 'cary', 'weston', 'brownsville',
                   'olympia', 'bend', 'stockton', 'newport', 'kingston', 'dover', 'warren', 'troy', 'temple'}


def build():
    loc = {}  # phrase -> (label, type)
    for c in gc.get_cities().values():
        names = {norm(c['name'])}
        if c['countrycode'] in ('US', 'GB', 'CA', 'AU', 'IN', 'NZ', 'IE', 'SG', 'AE', 'ZA', 'PH', 'MY', 'PK'):
            names = {n for n in names if n and len(n) > 3 and n.replace(' ', '').isalpha()}
        for n in names:
            if not n:
                continue
            if ' ' not in n:
                if n in CITY_STOP and n not in BIG_CITIES_KEEP:
                    continue
                # common English words are only kept for big cities
                if zf(n, 'en') >= 4.3 and c['population'] < 400000 and n not in BIG_CITIES_KEEP:
                    continue
                if len(n) < 4:
                    continue
            label = f"{strip(c['name'])}, {CC.get(c['countrycode'], c['countrycode'])}" if c['countrycode'] != 'US' else f"{c['name']}, {c['admin1code']}"
            prev = loc.get(n)
            if prev is None or prev[2] < c['population']:
                loc[n] = (label, 'City', c['population'], c['countrycode'])
    for county in gc.get_us_counties():
        n = norm(county['name'])
        loc.setdefault(n, (f"{county['name']}, {county['state']}", 'County', 0, 'US'))
    for n, ab in US_STATES.items():
        loc[n] = (n.title(), 'US State', 10**8, 'US')
    for d, t, cc in [(CANADA_PROV, 'Region', 'CA'), (AUS_STATES, 'Region', 'AU'), (UK_REGIONS, 'Region', 'GB'), (US_AREAS, 'Region', 'US')]:
        for n, lab in d.items():
            loc.setdefault(n, (lab, t, 10**7, cc))
    for n, lab in ABBREV_CITIES.items():
        loc[n] = (lab, 'City', 10**7, 'US')
    for n, lab in COUNTRIES.items():
        loc[n] = (lab, 'Country', 10**9, '')
    for bad in ['mobile', 'orange', 'commerce', 'page', 'best', 'google', 'online', 'marketing', 'york', 'national',
                'local', 'content', 'center', 'digital', 'chino', 'link', 'reading', 'guide', 'nice', 'split',
                'search', 'rank', 'value', 'tools', 'tool', 'one', 'pro', 'data', 'media']:
        if bad in loc and loc[bad][1] in ('City', 'County'):
            del loc[bad]
    loc['chino'] = ('Chino, CA', 'City', 90000, 'US')
    # smaller US towns from the USPS zip database
    import zipcodes
    for z in zipcodes.list_all():
        n = norm(z['city'])
        if not n or n in loc or len(n) < 4:
            continue
        words = n.split()
        if max(zf(w, l) for w in words for l in ('es', 'de', 'fr', 'pt', 'it', 'nl')) >= 3.5 and all(zf(w, 'en') < 3 for w in words):
            continue
        if len(words) == 1 and (n in CITY_STOP or zf(n, 'en') >= 3.3):
            continue
        if len(words) > 1 and all(zf(w, 'en') >= 4.0 for w in words) and words[0] not in ('fort', 'mount', 'saint', 'port', 'lake', 'west', 'east', 'north', 'south', 'new', 'palm', 'el', 'san', 'santa', 'los', 'las'):
            continue
        loc[n] = (f"{z['city'].title()}, {z['state']}", 'City', 1, 'US')
    for bad in ['white hat', 'black hat', 'page one', 'top rank', 'first page', 'web site', 'rank one', 'google',
                'friendly', 'mobile', 'content', 'local', 'national', 'organic', 'premium', 'ranking', 'search',
                'service', 'expert', 'success', 'progress', 'commerce', 'opportunity', 'enterprise', 'universal',
                'boost', 'hope', 'magnet', 'power', 'rush', 'stat', 'pinnacle', 'summit', 'vista', 'level', 'max',
                'mint', 'pro', 'plus', 'arrow', 'eagle', 'falcon', 'phoenix seo', 'fast', 'speed', 'scale', 'swift',
                'blue', 'green', 'orange', 'red', 'black', 'white', 'gold', 'silver', 'diamond', 'crystal',
                'wordpress', 'shopify', 'amazon', 'drupal', 'joomla', 'magento', 'hubspot']:
        if bad in loc and loc[bad][2] <= 1:
            del loc[bad]
    return loc


LOC = build()

# (place, state abbr) -> label, for disambiguating e.g. "lancaster pa" vs "lancaster ca"
CITY_STATE = {}
for _c in gc.get_cities().values():
    if _c['countrycode'] == 'US':
        CITY_STATE.setdefault((norm(_c['name']), _c['admin1code'].lower()), f"{_c['name']}, {_c['admin1code']}")
import zipcodes as _zc
for _z in _zc.list_all():
    CITY_STATE.setdefault((norm(_z['city']), _z['state'].lower()), f"{_z['city'].title()}, {_z['state']}")
MAXLEN = 4


def find_location(tokens):
    """Return (label, type, matched_phrase) for the longest location phrase in tokens."""
    best = None
    n = len(tokens)
    # explicit state given? (abbr or full name)
    st = None
    for t in tokens[-2:]:
        if t in STATE_ABBR and t not in ('in', 'or', 'me', 'oh', 'hi', 'ok', 'co', 'de', 'la', 'al', 'id'):
            st = t
    if st is None:
        for name, ab in US_STATES.items():
            if re.search(r'\b' + name + r'\b', ' '.join(tokens)):
                st = ab.lower()
    if st is None and tokens and tokens[-1] in ('co', 'de', 'la', 'al', 'id', 'oh', 'ok', 'hi', 'me', 'or', 'in') and n >= 3:
        st = tokens[-1]
    if st:
        for L in range(MAXLEN, 0, -1):
            for i in range(n - L + 1):
                ph = ' '.join(tokens[i:i + L])
                if (ph, st) in CITY_STATE and ph not in US_STATES:
                    lab = CITY_STATE[(ph, st)]
                    lab = {'New York, NY': 'New York City, NY'}.get(lab, lab)
                    return lab, 'City', ph, hub(lab, 'City', 'US')
    for L in range(MAXLEN, 0, -1):
        for i in range(n - L + 1):
            ph = ' '.join(tokens[i:i + L])
            if ph in LOC:
                lab, typ, _, cc = LOC[ph]
                return lab, typ, ph, hub(lab, typ, cc)
    # trailing state abbreviation, e.g. "seo company tx"
    if n >= 2 and tokens[-1] in SAFE_ABBR_END:
        st = STATE_ABBR[tokens[-1]]
        return st.title(), 'US State', tokens[-1], 'United States'
    return best


ABBR_TO_STATE = {v: k.title() for k, v in US_STATES.items()}


def hub(lab, typ, cc):
    """Parent hub for the location page (US state, or country)."""
    if typ == 'Country':
        return lab
    if typ == 'US State':
        return 'United States'
    if cc == 'US' and ', ' in lab:
        ab = lab.rsplit(', ', 1)[1]
        return 'United States > ' + ABBR_TO_STATE.get(ab, 'District Of Columbia' if ab == 'DC' else ab)
    if cc == 'US':
        return 'United States'
    if ', ' in lab:
        return lab.rsplit(', ', 1)[1]
    return CC.get(cc, 'Other regions')
