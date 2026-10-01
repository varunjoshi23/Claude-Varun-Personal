import re, unicodedata
import pandas as pd
from functools import lru_cache
from wordfreq import zipf_frequency as zf
from geo import find_location, LOC

OTHER_LANGS = ['es', 'de', 'fr', 'nl', 'pt', 'it', 'sv', 'da', 'nb', 'pl', 'tr', 'ro', 'cs', 'fi', 'id', 'hu']

# ---------------------------------------------------------------- vocab
EN_OK = set('''seo sem ppc smm smo aeo geo llm llms aio gmb gbp serp serps ai api saas b2b b2c ecommerce woocommerce
shopify magento bigcommerce wix squarespace webflow wordpress wp yoast moz ahrefs semrush ubersuggest spyfu
serpstat mangools majestic screaming frog rankmath seoquake seoptimer woorank sitebulb botify conductor brightedge
seoclarity clearscope marketmuse frase surfer jasper copilot chatgpt gemini perplexity claude bing yahoo youtube
tiktok instagram linkedin pinterest reddit quora etsy amazon ebay gpt h1 h2 alt url urls html css js javascript
nextjs react vue angular amp cms crm roi kpi kpis ctr cpc onpage offpage backlink backlinks hreflang schema
sitemap sitemaps robots txt canonical noindex nofollow dofollow pagespeed lighthouse vitals cwv ga ga4 gsc gtm
ux ui cro dfw nyc la sf usa uk uae nz hvac cpa dds pr seos saas tx fl ny nj ca az nc pa va ga wa il oh mi ma md
co ct sc tn mo wi mn ky ok ut nv nm ia ks ne ar ms al la or id mt wy nd sd ri de dc nh vt me hi ak in
white label reseller agency agencies company companies services service near me consultant consulting
freelance freelancer expert experts specialist specialists com hat per pro stat plus nap guru han ha med min
finder io se analyser linkbuilding ad ab non er bo softwares remodeler gutter duda boca destin vet ember ben solo
lang biz mkt sov typo3 ham yuk roh ji au net org rapport lsa pwa pwas nft web3 iframes listicles accordions
cannibalization lcp cls inp fid ttfb gsa dmoz ryte keysearch disqus wechat amz audiology arborists hardscaping
optometrists gastroenterology acupuncture seohub serped ourlocalseoservices webshop multilingue'''.split())

KOREAN_SYL = set('''joon jun jung guk gook ji jin jeon jong hye hyun hyeon hyo yeon yoon yun ye min woo soo hee
kang kim park lee choi seung eun yeong young won ah ha hyuk yeol sung sang hoon seon seok seo-joon in-guk
ye-ji ji-hye kang-joon hyun-jin ha-joon yeji jihye seojoon inguk kangjoon taiji hyuna seohyun eunji jisoo
chul ho mi kyung hwan seol taeyeon jae'''.split())
KOREAN_SURNAMES = {'park','kim','lee','choi','kang','jeon','han','cha','bae','yoon','yuk','roh','hwang','jung','jang','cho','shin','oh','ahn','song','im','lim','yoo','moon'}
SEO_CONTEXT = re.compile(r'\b(agency|agencies|company|companies|service|services|tool|tools|marketing|optimi[sz]ation|optimi[sz]e|ranking|rank|google|website|web|site|keyword|keywords|content|backlink|link|links|audit|consult\w*|expert|specialist|strategy|search|engine|blog|page|meta|local|technical|traffic|ai|ecommerce|shopify|wordpress|plugin|checker|software|course|jobs?|salary|tips|guide|what|how|best|top|free|analysis|report|business|seos?|serp)\b')

SPAM = re.compile(r'(\.(com|net|org|io|in|co)\b|\b(com|net)\b|\bescort|\bporn|\bxxx|\bsex\b|\bcasino\b.*\bspam\b|\bviagra|\bcialis|\bhack(ed|ing)?\b|\bcrack(ed)?\b|\bnulled\b|\bwarez|\bspider pool\b|\bpbn for sale)')
ADULT = re.compile(r'\b(escort|escorts|porn|xxx|adult|onlyfans|sex|sexy|naked|nude|nudes|creampie|boobs|hentai|fuck|fucking|dick|pussy|viagra|cialis|swinger|swingers)\b')

# ---------------------------------------------------------------- dictionaries
INDUSTRIES = [
    ('Dental', r'dent(al|ist|ists|istry)|orthodont\w*|endodont\w*|oral surg\w*'),
    ('Law Firms & Attorneys', r'law ?firms?|lawyers?|attorneys?|legal|personal injury|criminal defen[cs]e|dui|immigration law|family law|divorce|estate planning|bankruptcy|paralegal|litigation|mesothelioma'),
    ('Plastic Surgery & Med Spa', r'plastic surg\w*|cosmetic surg\w*|med ?spas?|medspa|aesthetic\w*|botox|dermatolog\w*|cosmetic'),
    ('Healthcare & Medical', r'medical|healthcare|health care|doctors?|physicians?|clinics?|hospitals?|chiropract\w*|physical therap\w*|physiotherap\w*|orthoped\w*|pharma\w*|pharmac\w*|surgeons?|urgent care|veterinar\w*|vets?|optometr\w*|therapists?|therapy|counsel(l)?ing|psycholog\w*|psychiatr\w*|mental health|behavioral health|rehabs?|addiction|recovery center|treatment cent\w*|home care|senior living|assisted living|nursing|hearing|podiatr\w*|obgyn|ob gyn|fertility|ivf|medicare|cardiolog\w*|wellness|health'),
    ('Home Services & Contractors', r'hvac|plumb\w*|roof\w*|electricians?|electrical contractor\w*|pest control|exterminat\w*|landscap\w*|lawn care|tree service|pool\w*|garage doors?|remodel\w*|renovation\w*|contractors?|construction|(?<!website )(?<!site )(?<!page )builders?|home builder\w*|restoration|water damage|flooring|carpet clean\w*|cleaning|cleaners?|maid|janitorial|pressure washing|power washing|painters?|painting|movers|moving compan\w*|locksmith\w*|solar|window\w*|siding|gutters?|concrete|paving|fencing|fence|handyman|home services?|home improvement|kitchen|bathroom|cabinet\w*|countertop\w*|junk removal|septic|foundation repair|insulation|appliance repair|interior design\w*|architects?|excavat\w*|demolition|deck\w*|masonry|drywall|mold|waterproofing'),
    ('Real Estate & Property', r'real estate|realtors?|realty|property management|properties|property|mortgage\w*|home sellers?|brokerages?|apartments?|rental\w*|vacation rental\w*|commercial real estate|homebuild\w*'),
    ('Restaurants, Hospitality & Travel', r'restaurants?|cafes?|coffee shops?|bars?|breweries|brewery|winer(y|ies)|catering|food truck|bakery|hotels?|motels?|resorts?|hospitality|travel|tour\w*|tourism|airbnb|wedding venue\w*|event venue\w*|food|bakeries'),
    ('Automotive', r'auto\b|automotive|car dealer\w*|dealerships?|car wash|auto repair|mechanics?|auto body|collision|tires?|towing|car rental|motorcycle|rv dealer\w*|car detailing|detailing|used cars?|cars?\b'),
    ('Finance, Insurance & Accounting', r'financial|finance|fintech|insurance|accountants?|accounting|cpas?|bookkeep\w*|tax prep\w*|tax|banks?|banking|credit union\w*|wealth management|financial advisors?|investment|crypto\w*|blockchain|forex|loans?|lending|wealth|payroll'),
    ('SaaS, Tech & Startups', r'saas|software compan\w*|tech compan\w*|tech startups?|startups?|technology compan\w*|it compan\w*|it services|msp|managed service\w*|cyber ?security|apps? developers?|b2b saas|ai startups?|tech|cloud'),
    ('B2B & Manufacturing', r'b2b|manufactur\w*|industrial|engineering|logistics|wholesale|distributors?|suppliers?|machinery|chemical|aerospace|oil and gas|energy compan\w*|trucking|freight|packaging'),
    ('Education & Schools', r'schools?|universit(y|ies)|colleges?|education\w*|edtech|e ?learning|tutor\w*|online courses? (business|creators?)|academies'),
    ('Nonprofits & Churches', r'non ?profits?|nonprofit|charit\w*|churches|church|ministr\w*|ngo'),
    ('Beauty, Fitness & Wellness', r'salons?|beauty|spas?|barbers?|hair|nail\w*|gyms?|fitness|personal trainers?|yoga|pilates|tattoo|massage|crossfit'),
    ('Recruitment & Staffing', r'recruit\w*|staffing|hr compan\w*|employment agenc\w*|headhunt\w*'),
    ('Cannabis & CBD', r'cannabis|cbd|dispensar\w*|marijuana|hemp|vape\w*|smoke shops?'),
    ('Casino & iGaming', r'casinos?|igaming|gambling|betting|sportsbook|poker|slots?'),
    ('Ecommerce & Retail Brands', r'retail\w*|online stores?|fashion|jewelry|jewellery|furniture|clothing|apparel|cosmetics brand|dtc|d2c|boutique\w*|florists?|pet\w*|toys?'),
    ('Creative, Media & Professional Services', r'photograph\w*|videograph\w*|wedding\w*|events?|event planners?|musicians?|artists?|authors?|publishers?|news sites?|media compan\w*|podcast\w*|consultants? (firms?)?|coaches|coaching|marketing agenc\w* (clients)|architecture firms?|engineering firms?|funeral\w*|translation|printing|security compan\w*|storage|self storage|government'),
]
INDUSTRIES = [(n, re.compile(r'\b(' + p + r')\b')) for n, p in INDUSTRIES]

SERVICE_TYPES = [
    # (name, regex, url slug)
    ('White Label SEO', r'white ?label\w*|reseller|resell|private label|wholesale seo|outsourc\w*|outsource', 'white-label-seo'),
    ('AI SEO / GEO / AEO', r'\bai\b|artificial intelligence|\bgeo\b|generative engine|\baeo\b|answer engine|\bllms?\b|chatgpt|chat gpt|\bgpt\w*|perplexity|gemini|\bclaude\b|copilot|ai overviews?|ai mode|sge|\baio\b|ai search|ai visibility|llmo|\bgso\b|search everywhere|machine learning', 'ai-seo'),
    ('Local SEO', r'local|google (my )?business( profile)?|\bgmb\b|\bgbp\b|google maps|maps seo|map pack|\bnap\b|citations?|map rank\w*|near me seo|multi ?location|franchise seo', 'local-seo'),
    ('Technical SEO', r'technical|tech seo|site speed|page ?speed|core web vitals|crawl\w*|index\w*|sitemaps?|robots ?txt|canonical\w*|redirects?|javascript|\bjs\b|react|next ?js|nextjs|angular|vue|render\w*|hreflang|schema|structured data|log file|site architecture|site structure|migration|migrat\w*|\bamp\b|https|ssl|404|duplicate content|subdomains?|subfolders?|pagination|headless', 'technical-seo'),
    ('Ecommerce SEO', r'e ?commerce|ecom\b|ecomemrce|shopify|woocommerce|magento|bigcommerce|online stores?|product pages?|category pages?|\bstores?\b|product seo|dtc|d2c|etsy|amazon|ebay|walmart|marketplace', 'ecommerce-seo'),
    ('Enterprise SEO', r'enterprise|fortune 500|large compan\w*|large websites?|large sites?|corporate', 'enterprise-seo'),
    ('International & Multilingual SEO', r'international|multilingual|multi lingual|multi language|global seo|multiregional|cross border|translation seo|localization', 'international-seo'),
    ('Link Building & Off-Page SEO', r'link ?building|backlinks?|back links?|link\b|links\b|off ?page|offpage|guest post\w*|guest blog\w*|outreach|digital pr|\bpr\b|press release\w*|citation building|pbn|directory submission\w*|directories|social bookmark\w*|link ?earning|niche edits?|link insertion', 'link-building'),
    ('On-Page SEO', r'on ?page|onpage|on site|onsite|meta tags?|meta titles?|meta descriptions?|title tags?|titles?|headings?|\bh1\b|\bh2\b|alt text|alt tags?|image alt|internal link\w*|keyword density|url structure|slugs?|meta\b|metadata', 'on-page-seo'),
    ('Content SEO & SEO Writing', r'content|copywrit\w*|writ(ing|ers?|e)|articles?|blog(s|ging|ger|gers)?\b|editorial|topic clusters?|pillar pages?|semantic|topical authority|landing pages?', 'seo-content-writing'),
    ('SEO Audit', r'audits?|auditing|site analysis|website analysis|seo analysis|health check|seo review|seo assessment|site check|website review|seo evaluation', 'seo-audit'),
    ('YouTube & Video SEO', r'youtube|video|vimeo|tiktok|instagram|social media seo|pinterest|linkedin|facebook|twitter|social seo|podcast', 'youtube-video-seo'),
    ('App Store Optimization (ASO)', r'app store|play store|\baso\b|mobile apps?|apps? seo|app ranking', 'app-store-optimization'),
    ('WordPress SEO', r'wordpress|\bwp\b|elementor|divi', 'wordpress-seo'),
    ('Website Builder SEO (Wix, Squarespace, Webflow)', r'\bwix\b|squarespace|webflow|godaddy|weebly|framer|hubspot cms|duda|ghost', 'website-builder-seo'),
    ('Mobile & Voice SEO', r'mobile|voice search|voice seo|voice assistants?', 'mobile-voice-seo'),
    ('Programmatic SEO', r'programmatic|pseo|seo at scale|automated seo pages', 'programmatic-seo'),
    ('National SEO', r'national|nationwide', 'national-seo'),
    ('B2B & SaaS SEO', r'\bb2b\b|saas', 'b2b-saas-seo'),
    ('Small Business SEO', r'small business(es)?|smb|startups?|small compan\w*|small sites?', 'small-business-seo'),
    ('SEO + PPC / Digital Marketing', r'\bppc\b|\bsem\b|paid search|google ads|adwords|digital marketing|internet marketing|online marketing|smm|social media marketing|inbound|growth marketing|performance marketing|search marketing|sea\b', 'seo-and-ppc'),
    ('SEO & Web Design', r'web ?design\w*|website design\w*|web develop\w*|website develop\w*|web dev|website builders?|website build\w*|redesign|website creation', 'seo-web-design'),
    ('Reputation & Brand SEO', r'reputation|\borm\b|brand seo|branded search|reviews management|negative seo|penalty recovery|penalt\w*|algorithm recovery|recovery', 'reputation-management-seo'),
]
SERVICE_TYPES = [(n, re.compile(r'\b(?:' + p + r')\b'), s) for n, p, s in SERVICE_TYPES]

TOOL_BRANDS = [
    ('Ahrefs', r'ahrefs?|ahref'), ('Semrush', r'sem ?rush|semrush'), ('Moz', r'\bmoz\b|mozbar|mozcast|moz pro'),
    ('Yoast SEO', r'yoast'), ('Rank Math', r'rank ?math|rankmath'), ('All in One SEO (AIOSEO)', r'all in one seo|aioseo|all-in-one seo'),
    ('Surfer SEO', r'surfer'), ('Screaming Frog', r'screaming ?frog|seo spider'), ('SE Ranking', r'se ?ranking'),
    ('SEO PowerSuite', r'powersuite|power suite|rank tracker by seo powersuite|website auditor'), ('Ubersuggest', r'ubersuggest|neil patel'),
    ('SpyFu', r'spyfu'), ('Serpstat', r'serpstat'), ('Mangools / KWFinder', r'mangools|kwfinder|kw finder'), ('Majestic', r'majestic'),
    ('Google Search Console', r'search console|webmaster tools?|\bgsc\b'), ('Google Analytics', r'google analytics|ga4'),
    ('Google Lighthouse & PageSpeed', r'lighthouse|pagespeed insights'), ('Conductor', r'conductor'), ('BrightEdge', r'brightedge|bright edge'),
    ('Botify', r'botify'), ('seoClarity', r'seoclarity|seo clarity'), ('Clearscope', r'clearscope'), ('MarketMuse', r'marketmuse|market muse'),
    ('Frase', r'\bfrase\b'), ('Sitebulb', r'sitebulb'), ('SEOquake', r'seoquake|seo quake'), ('Siteimprove', r'siteimprove'),
    ('Wincher', r'wincher'), ('AccuRanker', r'accuranker'), ('AgencyAnalytics', r'agency ?analytics'), ('Similarweb', r'similarweb|similar web'),
    ('Seobility', r'seobility'), ('SEOptimer', r'seoptimer'), ('WooRank', r'woorank'), ('Nightwatch', r'nightwatch'),
    ('Squirrly', r'squirrly'), ('Jasper', r'jasper'), ('Semji / NeuronWriter', r'neuronwriter|neuron writer|semji'),
    ('BrightLocal', r'brightlocal|bright local'), ('Whitespark', r'whitespark'), ('Yext', r'\byext\b'), ('HubSpot', r'hubspot'),
    ('Profound', r'\bprofound\b'), ('SEOwind / Writesonic', r'writesonic|seowind'), ('Copilot (Microsoft)', r'\bcopilot\b'),
    ('ChatGPT', r'chatgpt|chat gpt'), ('Workhorse', r'workhorse'), ('Search Atlas / OTTO', r'search ?atlas|\botto\b'),
    ('Alli AI', r'alli ai'), ('Morningscore', r'morningscore'), ('SEMScoop / Others', r'semscoop'),
]
TOOL_BRANDS = [(n, re.compile(r'\b(' + p + r')\b')) for n, p in TOOL_BRANDS]

TOOL_TYPES = [
    ('Rank Tracker', r'rank(ing|ings)? (track|check|monitor|notif|alert|report)\w*|track\w* (seo )?(keyword )?rank\w*|keyword (rank|position)\w*|rank ?tracker|serp (track|check|monitor)\w*|position (track|check)\w*|ranking (tool|software|checker|alerts?|notifications?)|check (my )?(seo )?rank\w*|get keyword ranking|seo notifications?|seo alerts?|rank(ing)? notification', 'rank-tracker'),
    ('Keyword Research Tool', r'keyword (research|finder|tool|generator|planner|suggestion|explorer|difficulty|analy\w*|density checker|checker)|keywords? tools?|long tail keyword', 'keyword-research-tool'),
    ('Backlink Checker', r'backlinks? (checker|tool|analy\w*|checking|generator|finder|monitor)|link (checker|analy\w*)|broken link', 'backlink-checker'),
    ('Meta Tag & Title Generator', r'meta (tag|title|description)s? (generator|checker|analy\w*|tool)|title (generator|checker)|(tag|title|description) generator|schema (generator|markup generator)|serp (preview|simulator|snippet)', 'meta-tag-generator'),
    ('Website SEO Checker / Analyzer', r'checker|check(ing)?|analy[sz]er|analysis tool|grader|score|scorer|test(er|ing)?|audit (tool|software)|site audit|crawler|scanner|seo report (tool|generator)|website (seo )?(analy|check|test|grader)\w*', 'seo-checker'),
    ('SEO Reporting & Dashboard Software', r'report(ing)? (tool|software|platform|dashboard)|dashboard|automated (seo )?report\w*|white label report\w*|seo reporting', 'seo-reporting-software'),
    ('Content Optimization Tool', r'content (optimi[sz]\w*|tool|editor|grader|writer|generator)|ai (writer|writing|content)|article (generator|writer|rewriter)|paraphras\w*|rewriter|plagiarism', 'content-optimization-tool'),
    ('Competitor Analysis Tool', r'competitor|competition|competitive', 'competitor-analysis-tool'),
    ('Local SEO Tools', r'local seo (tool|software|grid|checker|scan\w*|rank)|citation (tool|finder|builder)|gmb (tool|software)|map rank', 'local-seo-tools'),
    ('SEO Chrome Extensions', r'extensions?|chrome|firefox|toolbar|add ?on|bookmarklet|browser', 'seo-chrome-extensions'),
    ('SEO Plugins', r'plugins?|plug ins?|modules?|apps? (for|on) shopify|shopify apps?', 'seo-plugins'),
    ('AI SEO Tools', r'\bai\b|artificial intelligence|chatgpt|\bgpt\b|llm|geo|aeo|ai visibility|generative', 'ai-seo-tools'),
    ('SEO APIs & Data', r'\bapi\b|apis\b|data ?for ?seo|serp api|dataforseo', 'seo-api'),
]
TOOL_TYPES = [(n, re.compile(r'\b(?:' + p + r')\b'), s) for n, p, s in TOOL_TYPES]
TOOL_WORD = re.compile(r'\b(tools?|software|softwares|checker|checkers|analy[sz]er|tracker|trackers|plugins?|extensions?|generator|platforms?|seo apps?|grader|crawler|toolbar|toolkit|suite|api|saas tool|score|scanner|test|tester|calculator|dashboard|check|checkup|lookup|monitor|monitoring|scan|optimizer|optimiser|audit tool|site checker)\b')

BLOG_TOPICS = [
    # (cluster, regex, slug) evaluated in order for informational keywords
    ('SEO Glossary & Definitions', r'^(what is|what are|whats|what does|what s|define|definition|meaning)\b.*\b(in|of|for) seo\b|\bseo (term|terms|terminology|glossary|acronyms?|jargon)\b|\b(meaning|definition|stands? for|abbreviation|acronym)\b', 'seo-glossary'),
    ('SEO Careers, Jobs & Salary', r'\bjobs?\b|careers?|salar(y|ies)|hiring\b|internships?|interns?|resumes?|cv\b|interview|become (an? )?seo|how to be an? seo|seo roles?|job description|remote seo|work from home|freelanc\w* (jobs|work|career)|pay\b|earn|income|make money|side hustle|vacanc\w*|recruit\w*|hire me|portfolio|linkedin profile|job title', 'seo-careers'),
    ('SEO Courses, Training & Certification', r'courses?|training|trainings|classes|class\b|certif\w*|academy|bootcamp|workshop|tutorials?|learn\w*|lessons?|study|teach\w*|school|degree|diploma|mentor\w*|books?|ebooks?|pdf|notes|udemy|coursera|hubspot academy|youtube channel|beginners?|for dummies|from scratch|step by step|masterclass|webinar|institute|syllabus|exam|quiz|questions and answers', 'learn-seo'),
    ('Google Algorithm Updates & SEO News', r'\bnews\b|updates?|algorithm|core update|helpful content|e ?e ?a ?t|eeat|panda|penguin|hummingbird|rankbrain|bert|mum\b|spam update|today|latest|this week|trends?|future|predictions?|conference|conferences|events?|summit|brighton|smx|pubcon|podcast|newsletter|blogs? to follow|influencers?|statistics|stats|study|studies|survey|report 20|research data|speakers?|thought leaders?|to follow|famous|is seo dead|seo dead|dying|still relevant|worth it in', 'seo-news-updates'),
    ('AI Search, GEO & AEO', r'\bai\b|artificial intelligence|\bgeo\b|generative|\baeo\b|answer engine|\bllms?\b|chatgpt|chat gpt|\bgpt\w*|perplexity|gemini|\bclaude\b|copilot|ai overview\w*|ai mode|\bsge\b|\baio\b|llms ?txt|machine learning|automation|automate\w*|agentic|agents?\b|prompts?', 'ai-search-geo'),
    ('Keyword Research', r'keywords?|long ?tail|search volume|search intent|keyword difficulty|kd\b|topic research|search terms?|queries|query', 'keyword-research'),
    ('Local SEO Guide', r'local|google (my )?business|\bgmb\b|\bgbp\b|google maps|map pack|\bnap\b|citations?|reviews?\b|near me|service area', 'local-seo-guide'),
    ('Technical SEO Guide', r'technical|site speed|page ?speed|core web vitals|\bcwv\b|crawl\w*|index\w*|sitemaps?|robots|canonical\w*|redirect\w*|301|302|404|javascript|\bjs\b|react|next ?js|angular\w*|vue\w*|nuxt\w*|svelte|gatsby|spa\b|single page|render\w*|hreflang|schema|structured data|rich (snippets?|results?)|markup|log file|site architecture|site structure|migrat\w*|\bamp\b|https|ssl|duplicate|subdomains?|subfolders?|pagination|headless|server|hosting|cdn|domain|domains|url|urls|http|lazy load\w*|cache|caching|page experience|mobile ?first|responsive', 'technical-seo-guide'),
    ('Link Building & Off-Page SEO', r'link ?building|backlinks?|back links?|\blinks?\b|off ?page|offpage|guest post\w*|guest blog\w*|outreach|digital pr|press releases?|\bpbn\b|directory|directories|bookmark\w*|anchor text|domain authority|\bda\b|\bdr\b|domain rating|authority|nofollow|dofollow|disavow|toxic', 'link-building-guide'),
    ('On-Page SEO Guide', r'on ?page|onpage|on site|meta|title|titles|headings?|\bh1\b|\bh2\b|header tags?|alt (text|tags?|attributes?)|image\w*|internal link\w*|keyword density|url structure|slugs?|snippets?|featured snippet\w*|tags?\b|descriptions?|word count|readability|faq', 'on-page-seo-guide'),
    ('Content SEO & Blogging', r'content|copywrit\w*|writ(ing|ers?|e)|articles?|blog\w*|editorial|topic clusters?|pillar|semantic|topical|landing pages?|word count|evergreen|repurpos\w*', 'content-seo-guide'),
    ('Ecommerce SEO Guide', r'e ?commerce|ecom\b|shopify|woocommerce|magento|bigcommerce|online stores?|product (pages?|descriptions?|listings?)|category pages?|etsy|amazon|ebay|walmart|marketplace|dropship\w*', 'ecommerce-seo-guide'),
    ('Platform SEO (WordPress, Wix, Squarespace & more)', r'wordpress|\bwp\b|\bwix\b|squarespace|webflow|godaddy|weebly|framer|hubspot|duda|ghost|joomla|drupal|blogger|blogspot|website builders?|cms|elementor|divi|shopify', 'platform-seo-guide'),
    ('YouTube, Video & Social SEO', r'youtube|video\w*|vimeo|tiktok|instagram|pinterest|linkedin|facebook|twitter|social|podcast|reddit|quora|google images|image search|app store|play store|\baso\b|apps?\b', 'social-video-seo-guide'),
    ('SEO vs PPC, SEM & Digital Marketing', r'\bppc\b|\bsem\b|paid|google ads|adwords|digital marketing|internet marketing|online marketing|social media|smm|smo|email marketing|inbound|marketing', 'seo-vs-ppc-sem'),
    ('SEO Reporting, Analytics & ROI', r'report\w*|analytics|kpis?|metrics?|measure\w*|roi\b|return on|track\w*|results?|attribution|conversion\w*|ctr|click through|impressions|traffic|dashboard|benchmark\w*|forecast\w*|organic (traffic|search)|visibility|search console|data', 'seo-reporting-analytics'),
    ('Black Hat, White Hat & Penalties', r'black ?hat|white ?hat|grey ?hat|gray ?hat|penalt\w*|negative seo|spam\w*|cloak\w*|keyword stuffing|manual action|deindex\w*|banned|sandbox|unethical|ethical|scam\w*|cheat\w*|tricks?|hacks?', 'black-hat-white-hat-seo'),
    ('Running an SEO Agency / Freelance Business', r'clients?|proposals?|contracts?|start (an? )?(seo )?(agency|business|company)|starting (an? )?seo|seo business|agency (owner|growth|model|business)|sell(ing)? seo|lead gen\w*|leads\b|cold (email|call\w*)|pitch\w*|retainer|onboarding|sops?|scale|scaling|niche|seo reseller program|pricing model|how to charge|charge for', 'seo-agency-business'),
    ('SEO Checklists & Templates', r'checklists?|templates?|examples?|samples?|cheat ?sheets?|worksheets?|spreadsheets?|excel|google sheets?|frameworks?|swipe', 'seo-checklists-templates'),
    ('SEO Strategy, Tips & Best Practices', r'strateg\w*|tips|tip\b|best practices?|techniques?|tactics?|ideas?|hacks?|ways|steps|plan\w*|roadmap|improve\w*|boost\w*|increase\w*|rank (higher|better|faster|#?1)|first page|page one|top of google|how to rank|ranking factors?|factors|mistakes?|common|rules|guidelines?|principles|fundamentals|basics?|essentials|101|how long|timeline|take to|competitive|competitors?|competition|optimi[sz]\w*', 'seo-strategy-tips'),
    ('What Is SEO & How It Works', r'^(what|why|how|is|does|do|can|are|should|will|when|where|who|which)\b|\bseo (mean|means|meaning|stand|definition)\b|how (does )?seo work|benefits?|importance|important|advantages?|disadvantages?|pros and cons|why seo|purpose|value of|types of seo|kinds of seo|explained', 'what-is-seo'),
]
BLOG_TOPICS = [(n, re.compile(r'\b(?:' + p + r')\b'), s) for n, p, s in BLOG_TOPICS]

QUESTION = re.compile(r'^(what|why|how|is|does|do|can|are|should|will|when|where|who|which|whats|define|explain|difference|did|would|could|has|have)\b|\b(how to|what is|guide|tips|tutorial|meaning|definition|examples?|checklist|vs|versus|difference|best practices|strateg(y|ies)|ideas|techniques|tactics|basics|beginners?|learn|course|courses|training|certification|jobs?|salary|news|updates?|trends|statistics|mistakes|factors|benefits|importance|explained|template|templates|case stud(y|ies))\b|\?')
COMMERCIAL = re.compile(r'\b(agency|agencies|agence|company|companies|compan|firm|firms|services?|consultants?|consulting|consultancy|consultation|experts?|specialists?|freelancers?|freelance|professionals?|pros|providers?|partners?|hire|hiring an?|outsourc\w*|near me|packages?|pricing|prices?|cost|costs|rates?|quote|cheap|affordable|budget|buy|management|solutions?|marketer|marketers|strategist|strategists|advisors?|coach|coaches|inc|llc|ltd|group|guys|team|teams|bureau|outfit|vendors?|contractors?|managed|done for you|retainer|plans?)\b')
PRICING = re.compile(r'\b(pric\w*|cost\w*|cheap\w*|affordable|budget|packages?|plans?|rates?|fees?|how much|quote|quotes|per month|monthly|retainer|low cost|inexpensive|price list|charges?|invoice|roi calculator|calculator)\b')
NEAR_ME = re.compile(r'\bnear (me|by)\b|\bnearby\b|\bin my area\b|\baround me\b|\blocal to me\b')
HEAD_TYPES = [
    ('SEO Consultant', re.compile(r'\b(consultants?|consulting|consultancy|consultation|advisors?|advisory|strategists?|coach(es|ing)?)\b'), 'seo-consultant'),
    ('SEO Expert / Specialist', re.compile(r'\b(experts?|specialists?|professionals?|pros|gurus?|ninjas?|wizards?|marketers?|managers?|hire an? seo|seo person|seo guy|seo girl|seo man)\b'), 'seo-expert'),
    ('SEO Freelancer', re.compile(r'\b(freelanc\w*|independent|solo)\b'), 'seo-freelancer'),
    ('SEO Agency / SEO Company', re.compile(r'\b(agency|agencies|agence|company|companies|compan|firm|firms|bureau|studio|partners?|providers?|vendors?|team|teams|outfit|business(es)? that|organi[sz]ations?)\b'), 'seo-agency'),
    ('SEO Services', re.compile(r'\b(services?|solutions?|management|managed|help|support|done for you|packages?|optimization services|seo work)\b'), 'seo-services'),
]


def strip_accents(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()


@lru_cache(maxsize=None)
def is_foreign_token(t):
    if t in EN_OK or len(t) < 2 or t.isdigit():
        return False
    en = zf(t, 'en')
    other = max(zf(t, l) for l in OTHER_LANGS)
    if en < 1.5 and other >= 2.5:
        return True
    return other >= 3.0 and other - en >= 1.6


FOREIGN_PHRASE = re.compile(r'\b(posicionamiento|posicionamento|optimizacion|optimizacao|optimierung|suchmaschine\w*|referencement|referenciamento|agencia|agenzia|empresa\w*|servicios|servicos|herramienta\w*|zoekmachine\w*|optimalisatie|optimering|sokmotor\w*|pozycjonowanie|ottimizzazione|wat is|que es|o que e|cos e|was ist|qu est ce|para que|como hacer|como fazer)\b')


CORE_VOCAB = '''agency agencies company companies services service consultant consulting consultants expert experts
specialist specialists marketing optimization optimize optimizer website websites analytics analysis analyzer check
checker course courses training practices strategy strategies keyword keywords ranking rankings google search engine
content backlinks backlink audit tools tool software report reporting tracking tracker business businesses local
technical ecommerce shopify wordpress plugin professional affordable company's packages pricing results optimized
optimizing traffic organic management consultancy freelancer services techniques friendly checklist beginners
tutorial certification copywriting writing writer generator description descriptions title titles meta image images
internal external structure schema sitemap crawl indexing performance competitor competitors analyse analysing
marketing digital online small enterprise international national strategy restaurants contractors dentists lawyers
attorneys plumbers roofers realtors doctors'''.split()
import difflib
@lru_cache(maxsize=None)
def fix_token(t):
    if len(t) < 5 or t in EN_OK or t in CORE_VOCAB or zf(t, 'en') >= 2.5 or t in LOC:
        return t
    m = difflib.get_close_matches(t, CORE_VOCAB, n=1, cutoff=0.84)
    return m[0] if m else t


def classify(raw):
    kw = str(raw)
    low = kw.lower().strip()
    for a, b in (('\u2019', "'"), ('\u2018', "'"), ('\u201c', '"'), ('\u201d', '"'), ('\u2013', '-'), ('\u2014', '-'), ('\u00a0', ' '), ('\u2026', '...')):
        low = low.replace(a, b)
    # data clean-up: strip numeric prefixes such as "11505: " or "0:13 "
    clean = re.sub(r'^\s*\d+(:\d+)?\s*:?\s+', '', low)
    out = dict(Keyword=kw, Clean=clean)

    def irr(reason):
        out.update(Relevance='Irrelevant', Pillar='Irrelevant', Cluster='Irrelevant – ' + reason,
                   PageType='Do not target', URL='', Intent='', Reason=reason)
        return out

    # 1. non-Latin scripts
    if re.search(r'[^\x00-\x7f]', clean):
        non_latin = [ch for ch in clean if ord(ch) > 0x24f and not unicodedata.category(ch).startswith(('P', 'Z', 'S'))]
        if non_latin:
            return irr('Non-English (non-Latin script)')
    ascii_kw = strip_accents(clean)
    tokens = re.findall(r'[a-z0-9]+', ascii_kw.replace("'", ''))
    if not tokens:
        return irr('Empty / junk')
    fixed = [fix_token(t) for t in tokens]
    out['TypoFixed'] = 'Yes' if fixed != tokens else ''
    text = ' '.join(tokens)

    loc = find_location(tokens)
    loc_tokens = set(loc[2].split()) if loc else set()

    # 2. foreign-language (Latin script)
    if FOREIGN_PHRASE.search(text):
        return irr('Non-English language')
    foreign = [t for t in tokens if t not in loc_tokens and is_foreign_token(t)]
    accented = clean != ascii_kw
    if foreign and (len(foreign) >= 2 or accented or len(tokens) <= 4 or foreign[0] in
                    {'de', 'la', 'el', 'los', 'para', 'und', 'fur', 'voor', 'van', 'het', 'les', 'des', 'du', 'que',
                     'por', 'con', 'una', 'och', 'og', 'per', 'il', 'della', 'di', 'na', 'em', 'w', 'z', 'dla',
                     'jak', 'ist', 'der', 'die', 'das', 'mit', 'op', 'en', 'et', 'y', 'e', 'o', 'com', 'je', 'ce',
                     'est', 'como', 'qual', 'cual', 'zu', 'bei', 'auf', 'nel', 'sur', 'pour', 'avec', 'mejor',
                     'mejores', 'melhor', 'beste', 'besten', 'meilleur', 'migliore', 'gratis', 'gratuit'}):
        return irr('Non-English language')
    if accented and not loc:
        return irr('Non-English language')

    # 3. Korean personalities named "Seo" (actors / idols) – not the marketing term
    hy = [h for h in re.findall(r'\bseo-([a-z]+)|([a-z]+)-seo\b', clean) if (h[0] or h[1]) in KOREAN_SYL]
    kor = [t for t in tokens if t in KOREAN_SYL and t not in KOREAN_SURNAMES]
    ctx = SEO_CONTEXT.search(re.sub(r'\bseo\b', '', text))
    if (hy or kor) and not ctx and not loc:
        return irr('Korean name / celebrity (not SEO)')
    if re.search(r'\b(actor|actress|drama|dramas|kdrama|k drama|movies?|wife|husband|girlfriend|boyfriend|height|married|kpop|idol|singer|olympics?|olympic|archer|archery|badminton|golfer|footballer|net worth|biography|bio wiki|dodgers|tennis|makeup artist|miss korea|nudes)\b', text) and not SEO_CONTEXT.search(re.sub(r'\b(seo)\b', '', text)):
        return irr('Person / celebrity named Seo (not SEO)')

    # 4. adult / spam / other-site navigational
    if ADULT.search(text):
        return irr('Adult / brand-unsafe')
    dom = re.findall(r'([a-z0-9-]+)\s?\.\s?(?:com|net|org|io|xyz|info|in|co|us)\b|([a-z0-9-]+) (?:com|net|org)\b', low)
    dom = [a or b for a, b in dom]
    if dom and any(d not in ('schema', 'wordpress', 'clutch', 'moz', 'google', 'seo', 'e', 'ecom', 'asp', 'dot') and zf(d, 'en') < 3.0 for d in dom):
        return irr('Navigational – other website / spam domain')
    if re.search(r'\b(spider pool|crack(ed)?|nulled|warez|keygen|torrent|apk|mod apk|hack(ed)? (seo|tool)|serial key|license key|free download full)\b', text):
        return irr('Spam / piracy')
    if 'seo' not in tokens and not re.search(r'seo|search engine|optimi[sz]', text):
        return irr('Not SEO related')

    tokens = fixed
    text = ' '.join(tokens)
    out['Relevance'] = 'Relevant'
    out['Location'] = loc[0] if loc else ''
    out['LocationHub'] = loc[3] if loc else ''
    out['LocationType'] = loc[1] if loc else ''
    out['NearMe'] = 'Yes' if NEAR_ME.search(text) else ''
    ind = next((n for n, rx in INDUSTRIES if rx.search(text)), '')
    out['Industry'] = ind
    svc = next(((n, s) for n, rx, s in SERVICE_TYPES if rx.search(text)), None)
    out['ServiceType'] = svc[0] if svc else ''
    brand = next((n for n, rx in TOOL_BRANDS if rx.search(text)), '')
    out['ToolBrand'] = brand

    is_q = bool(QUESTION.search(text))
    is_comm = bool(COMMERCIAL.search(text)) or bool(re.search(r'\b(best|top|leading|rated|top rated|reviews?)\b', text) and re.search(r'\b(agency|agencies|company|companies|firm|firms|consultants?|experts?|services?|specialists?)\b', text))
    is_tool = bool(TOOL_WORD.search(text)) or bool(brand)
    if re.search(r'\b(vs|versus|pros and cons|difference|differences|compared?)\b', text) and not re.search(r'\b(agency|agencies|company|companies|firm|consultants?|services)\b', text):
        is_comm = False
        is_q = True

    def set_(pillar, cluster, ptype, url, intent):
        out.update(Pillar=pillar, Cluster=cluster, PageType=ptype, URL=url, Intent=intent)
        return out

    def slug(s):
        return re.sub(r'[^a-z0-9]+', '-', strip_accents(s.lower())).strip('-')

    # --- careers / learning are always informational and override commercial words like "specialist"
    for name, rx, s in BLOG_TOPICS[1:3]:
        if rx.search(text) and not (name.startswith('SEO Courses') and re.search(r'\b(agency|company|services|consultant)\b', text) and not re.search(r'course|training|certif|class|academy', text)):
            if name.startswith('SEO Careers') and re.search(r'\b(hire|hiring) (an? |the )?(seo|best)|\bpay for seo|\bpay per\b', text):
                continue
            if name.startswith('SEO Careers'):
                return set_('Blog: SEO Careers', name, 'Blog post / Career guide', f'/blog/{s}/', 'Informational')
            return set_('Learn SEO (Courses & Training)', name, 'Course / Learning hub page', f'/learn-seo/', 'Informational / Commercial')

    # --- tool brand reviews & comparisons (a place name wins when the query is clearly local-commercial)
    if brand and loc and is_comm and not is_tool:
        brand = ''
        out['ToolBrand'] = ''
    if brand and not (is_comm and not is_tool and re.search(r'\b(agency|company|services|consultant)\b', text) and brand in ('HubSpot', 'Conductor', 'Copilot (Microsoft)', 'ChatGPT', 'Profound')):
        if re.search(r'\b(vs|versus|alternatives?|alternative|compare|comparison|or|better than|competitors?)\b', text):
            return set_('Blog: SEO Tool Reviews & Comparisons', f'{brand} – Comparisons & Alternatives',
                        'Comparison blog post', f'/blog/{slug(brand)}-alternatives/', 'Commercial investigation')
        if brand in ('ChatGPT', 'Copilot (Microsoft)') and not is_tool:
            pass
        else:
            return set_('Blog: SEO Tool Reviews & Comparisons', f'{brand} – Review & How-to',
                        'Tool review / Tutorial post', f'/blog/{slug(brand)}-review/', 'Commercial investigation')

    # --- location pages (commercial intent + a place)
    if loc and not (is_q and not is_comm):
        city = loc[0]
        return set_('Location Pages', f'SEO Services – {city}', 'Location landing page',
                    f'/locations/{slug(city)}/', 'Commercial / Local')

    # --- pricing
    if PRICING.search(text) and not is_tool and not re.search(r'\b(how to|guide|tips)\b', text):
        if is_q and not is_comm:
            return set_('Blog: SEO Pricing', 'How Much Does SEO Cost?', 'Blog post', '/blog/seo-cost/', 'Informational / Commercial')
        return set_('Service Pages', 'SEO Pricing & Packages', 'Pricing page', '/seo-pricing/', 'Transactional')

    # --- tools (software / free tools)
    if is_tool and not (is_comm and re.search(r'\b(agency|agencies|company|companies|consultant|services)\b', text) and not re.search(r'\b(tools?|software)\b', text)):
        if re.search(r'\b(best|top|vs|alternatives?|compare|comparison|list|review|reviews|recommended|which)\b', text) and re.search(r'\b(tools?|software|plugins?|extensions?|apps?|platforms?|trackers?|checkers?)\b', text):
            ttype = next((n for n, rx, s in TOOL_TYPES if rx.search(text)), 'SEO Tools (General)')
            return set_('Blog: SEO Tool Reviews & Comparisons', f'Best {ttype} (Listicle)', 'Listicle / Roundup post',
                        f'/blog/best-{slug(ttype)}/', 'Commercial investigation')
        tt = next(((n, s) for n, rx, s in TOOL_TYPES if rx.search(text)), ('SEO Tools Hub (General)', ''))
        url = f'/tools/{tt[1]}/' if tt[1] else '/tools/'
        return set_('Free SEO Tools', tt[0], 'Tool page', url, 'Transactional / Tool')

    # --- industry pages
    if ind and not (is_q and not is_comm):
        return set_('Industry Pages', f'{ind} SEO', 'Industry landing page', f'/industries/{slug(ind)}-seo/',
                    'Commercial')

    # --- service pages
    if is_comm or (svc and not is_q and len(tokens) <= 3):
        if svc and svc[0] == 'SEO + PPC / Digital Marketing' and not is_comm and not re.search(r'\b(seo and|and seo|seo &)\b', text):
            pass
        elif svc:
            return set_('Service Pages', svc[0] + (' Services' if not svc[0].endswith(('Services', 'Marketing', 'Design', 'SEO')) else ''),
                        'Service landing page', f'/seo-services/{svc[1]}/', 'Commercial')
        if is_comm:
            head = next(((n, s) for n, rx, s in HEAD_TYPES if rx.search(text)), ('SEO Services', 'seo-services'))
            if out['NearMe']:
                return set_('Core Money Pages', f'{head[0]} (Near Me)', 'Core landing page', f'/{head[1]}/', 'Commercial / Local')
            return set_('Core Money Pages', head[0], 'Core landing page', f'/{head[1]}/', 'Commercial')

    # --- generic head terms (seo, seo marketing, seo optimization, website seo ...)
    if re.fullmatch(r'(the )?(best |top |good |professional |expert |pro )?(seo|search engine optimi[sz]ation)( (marketing|optimi[sz]ation|optimi[sz]ing|website|websites|web|site|online|google|digital marketing|search|ranking|rankings|for websites?|for my website|for business(es)?|for my business|internet))*', text) or re.fullmatch(r'(google|website|web|site|online|websites|internet|organic|search) (seo|search engine optimi[sz]ation)( (marketing|optimi[sz]ation|services?))?', text):
        return set_('Core Money Pages', 'SEO (Head Term / Homepage)', 'Homepage / Pillar page', '/', 'Mixed')
    # --- informational blog topics
    if ind:
        return set_('Blog: Industry SEO Guides', f'SEO for {ind} (Guide)', 'Blog post', f'/blog/seo-for-{slug(ind)}/',
                    'Informational')
    if loc:
        return set_('Blog: Local Market Guides', f'SEO in {loc[0]} (Guide)', 'Blog post', f'/blog/seo-{slug(loc[0])}/',
                    'Informational')
    for name, rx, s in BLOG_TOPICS[3:] + BLOG_TOPICS[:1]:
        if rx.search(text):
            if name == 'SEO Glossary & Definitions':
                term = re.sub(r'\b(what|is|are|does|do|a|an|the|in|of|for|seo|mean|meaning|definition|define|stand|stands|whats|s|by|term|terms)\b', ' ', text)
                term = ' '.join(term.split()) or 'seo'
                return set_('SEO Glossary', name, 'Glossary entry', '/glossary/', 'Informational')
            pillar = 'Blog: ' + name
            return set_(pillar, name, 'Blog post / Guide', f'/blog/{s}/', 'Informational')

    # --- generic head terms
    if svc and not is_q:
        return set_('Service Pages', svc[0], 'Service landing page', f'/seo-services/{svc[1]}/', 'Commercial')
    if re.search(r'\b(rank|ranks|ranker|ranking|rankings|position|placement|guarantee\w*|first page|top 10|page 1|1st page|number one|#1)\b', text) and not is_q:
        return set_('Core Money Pages', 'SEO Services', 'Core landing page', '/seo-services/', 'Commercial')
    leftover = [t for t in tokens if t not in ('seo', 'for', 'and', 'the', 'a', 'in', 'of', 'to', 'my', 'best', 'top')]
    m = re.fullmatch(r'(?:best |top )?seo (?:for|services for|marketing for) (?:an? |the )?([a-z ]+)|([a-z]+(?: [a-z]+)?) (?:seo|seo marketing|seo services)', text)
    if m:
        niche = (m.group(1) or m.group(2)).strip()
        generic = re.search(r'\b(beginners?|new|website|websites|site|sites|yahoo|bing|dummies|free|spanish|english|speakers|keyphrases|freelancing|blogs?|pages?|it|me|you|us|them|this|that|everyone|all)\b', niche)
        if not generic and ((m.group(1) and len(niche.split()) <= 4) or re.search(r'(ers|ists|ians|shops|stores|companies|businesses|centers|centres|clinics|practices|firms|studios|agencies|brands|salons|services|contractors|providers|trucks)$', niche)):
            return set_('Industry Pages', 'Other Niches SEO (Industries hub)', 'Industries hub page', '/industries/', 'Commercial')
    if leftover and all(zf(t, 'en') < 3.0 for t in leftover):
        out.update(Relevance='Review', Pillar='Needs manual review', Cluster='Unclassified – competitor brand / person / place / typo',
                   PageType='Review', URL='', Intent='Navigational?')
        return out
    return set_('Blog: SEO Strategy, Tips & Best Practices', 'General SEO – long tail (review)', 'Blog post / Guide',
                '/blog/seo-strategy-tips/', 'Informational')


if __name__ == '__main__':
    import sys
    df = pd.read_csv('kw.csv')
    df = df[df.Keyword.notna()]
    rows = [classify(k) for k in df.Keyword]
    res = pd.DataFrame(rows)
    res.to_pickle('res.pkl')
    print(res.Relevance.value_counts())
    print(res.Pillar.value_counts().head(40))
