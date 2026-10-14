"""Static configuration: benchmarks, origins, news sources, data sources.

Everything the platform pulls from is declared here, so adding a feed or an
origin is a config change, not a code change.
"""

import os

# ----------------------------------------------------------------- runtime

QUOTE_TTL = int(os.getenv("QUOTE_TTL", "60"))
FX_TTL = int(os.getenv("FX_TTL", "120"))
WEATHER_TTL = int(os.getenv("WEATHER_TTL", "1800"))
LB_PER_KG = 2.20462

# ------------------------------------------------------------- benchmarks
# Live futures only for arabica. ICE London robusta has no free source (Yahoo
# delisted RC=F/RM=F; the alternatives need a paid key), so Robustas origins
# carry no implied price. IMF monthly Robustas prices come from FRED below.

BENCHMARKS = {
    "arabica": {
        "name": "Arabica 'C' (ICE NY)", "short": "KC", "unit": "¢/lb",
        "candidates": os.getenv("ARABICA_SYMBOLS", "KC=F").split(","),
    },
}

CONTEXT = {
    "dxy": {"name": "US Dollar Index", "symbol": "DX-Y.NYB"},
    "brl": {"name": "USD/BRL", "symbol": "BRL=X"},
}

# ---------------------------------------------------------------- origins
# lang/gl/ceid drive origin-language Google News queries.
# terms: words that tag an article to this origin (country names in local
# languages + key growing regions). census: name in US Census trade data.

ORIGINS = [
    # ---- Americas
    dict(id="br", country="Brazil", flag="🇧🇷", benchmark="arabica", group="Brazilian Naturals",
         currency="BRL", fx_symbol="BRL=X", region="Sul de Minas", lat=-21.55, lon=-45.43,
         harvest="May – Sep", census="BRAZIL",
         news=dict(q='café (safra OR colheita OR exportação OR arábica OR conilon)', hl="pt-BR", gl="BR", ceid="BR:pt-419"),
         terms=["brazil", "brasil", "brazilian", "minas gerais", "sul de minas", "cerrado mineiro",
                "espírito santo", "espirito santo", "mogiana", "conilon", "conab", "cecafé", "cecafe",
                "cooxupé", "cooxupe", "santos"]),
    dict(id="co", country="Colombia", flag="🇨🇴", benchmark="arabica", group="Colombian Milds",
         currency="COP", fx_symbol="COP=X", region="Huila", lat=2.03, lon=-75.75,
         harvest="Sep – Dec · Apr – Jun (mitaca)", census="COLOMBIA",
         news=dict(q='café (cosecha OR exportaciones OR "precio interno" OR caficultores)', hl="es-419", gl="CO", ceid="CO:es-419"),
         terms=["colombia", "colombian", "colombiano", "huila", "nariño", "narino", "cauca", "antioquia",
                "tolima", "federación nacional de cafeteros", "fnc", "cafeteros", "mitaca"]),
    dict(id="cr", country="Costa Rica", flag="🇨🇷", benchmark="arabica", group="Other Milds",
         currency="CRC", fx_symbol="CRC=X", region="Tarrazú", lat=9.65, lon=-84.02,
         harvest="Nov – Mar", census="COSTA RICA",
         news=dict(q='café (cosecha OR exportaciones OR ICAFE OR caficultores)', hl="es-419", gl="CR", ceid="CR:es-419"),
         terms=["costa rica", "costa rican", "costarricense", "tarrazú", "tarrazu", "west valley",
                "central valley", "brunca", "icafe", "naranjo"]),
    dict(id="gt", country="Guatemala", flag="🇬🇹", benchmark="arabica", group="Other Milds",
         currency="GTQ", fx_symbol="GTQ=X", region="Huehuetenango", lat=15.32, lon=-91.47,
         harvest="Nov – Apr", census="GUATEMALA",
         news=dict(q='café (cosecha OR exportaciones OR Anacafé OR caficultores)', hl="es-419", gl="GT", ceid="GT:es-419"),
         terms=["guatemala", "guatemalan", "guatemalteco", "huehuetenango", "antigua", "atitlán",
                "atitlan", "cobán", "coban", "acatenango", "anacafé", "anacafe"]),
    dict(id="hn", country="Honduras", flag="🇭🇳", benchmark="arabica", group="Other Milds",
         currency="HNL", fx_symbol="HNL=X", region="Marcala", lat=14.15, lon=-88.03,
         harvest="Nov – Apr", census="HONDURAS",
         news=dict(q='café (cosecha OR exportaciones OR IHCAFE OR productores)', hl="es-419", gl="HN", ceid="HN:es-419"),
         terms=["honduras", "honduran", "hondureño", "marcala", "santa bárbara", "santa barbara",
                "copán", "copan", "montecillos", "ihcafe"]),
    dict(id="mx", country="Mexico", flag="🇲🇽", benchmark="arabica", group="Other Milds",
         currency="MXN", fx_symbol="MXN=X", region="Chiapas", lat=16.75, lon=-92.63,
         harvest="Nov – Mar", census="MEXICO",
         news=dict(q='café (cosecha OR exportaciones OR cafeticultores) (Chiapas OR Veracruz OR Oaxaca)', hl="es-419", gl="MX", ceid="MX:es-419"),
         terms=["mexico", "méxico", "mexican", "chiapas", "veracruz", "oaxaca", "puebla", "cafeticultores"]),
    dict(id="ni", country="Nicaragua", flag="🇳🇮", benchmark="arabica", group="Other Milds",
         currency="NIO", fx_symbol="NIO=X", region="Jinotega", lat=13.09, lon=-85.99,
         harvest="Nov – Mar", census="NICARAGUA",
         news=dict(q='café (cosecha OR exportaciones OR productores) Nicaragua', hl="es-419", gl="NI", ceid="NI:es-419"),
         terms=["nicaragua", "nicaraguan", "nicaragüense", "jinotega", "matagalpa", "nueva segovia"]),
    dict(id="sv", country="El Salvador", flag="🇸🇻", benchmark="arabica", group="Other Milds",
         currency="USD", fx_symbol=None, region="Santa Ana", lat=13.99, lon=-89.56,
         harvest="Nov – Mar", census="EL SALVADOR",
         news=dict(q='café (cosecha OR exportaciones OR caficultores) "El Salvador"', hl="es-419", gl="SV", ceid="SV:es-419"),
         terms=["el salvador", "salvadoran", "salvadoreño", "santa ana", "apaneca", "ilamatepec", "chalatenango"]),
    dict(id="pa", country="Panama", flag="🇵🇦", benchmark="arabica", group="Other Milds",
         currency="USD", fx_symbol=None, region="Boquete", lat=8.78, lon=-82.44,
         harvest="Dec – Apr", census="PANAMA",
         news=dict(q='café (geisha OR "Best of Panama" OR cosecha) Panamá', hl="es-419", gl="PA", ceid="PA:es-419"),
         terms=["panama", "panamá", "panamanian", "boquete", "volcán", "volcan", "chiriquí", "chiriqui",
                "best of panama", "geisha", "gesha"]),
    dict(id="pe", country="Peru", flag="🇵🇪", benchmark="arabica", group="Other Milds",
         currency="PEN", fx_symbol="PEN=X", region="Jaén", lat=-5.71, lon=-78.81,
         harvest="Apr – Sep", census="PERU",
         news=dict(q='café (cosecha OR exportaciones OR cafetaleros) Perú', hl="es-419", gl="PE", ceid="PE:es-419"),
         terms=["peru", "perú", "peruvian", "peruano", "cajamarca", "jaén", "jaen", "san martín",
                "amazonas", "junín", "junin", "cusco", "puno"]),
    # ---- Africa & Middle East
    dict(id="et", country="Ethiopia", flag="🇪🇹", benchmark="arabica", group="Other Milds",
         currency="ETB", fx_symbol="ETB=X", region="Sidama", lat=6.16, lon=38.20,
         harvest="Oct – Jan", census="ETHIOPIA",
         news=dict(q='Ethiopia coffee (export OR harvest OR ECTA OR ECX OR price)', hl="en-US", gl="US", ceid="US:en"),
         terms=["ethiopia", "ethiopian", "sidama", "sidamo", "yirgacheffe", "yirgachefe", "guji", "harrar",
                "harar", "limu", "jimma", "ecta", "ecx", "addis ababa"]),
    dict(id="ke", country="Kenya", flag="🇰🇪", benchmark="arabica", group="Colombian Milds",
         currency="KES", fx_symbol="KES=X", region="Nyeri", lat=-0.42, lon=36.95,
         harvest="Oct – Dec · Apr – Jun", census="KENYA",
         news=dict(q='Kenya coffee (auction OR NCE OR exports OR farmers OR prices)', hl="en-KE", gl="KE", ceid="KE:en"),
         terms=["kenya", "kenyan", "nyeri", "kirinyaga", "murang'a", "muranga", "kiambu", "embu",
                "nairobi coffee exchange", "sl28", "sl34"]),
    dict(id="rw", country="Rwanda", flag="🇷🇼", benchmark="arabica", group="Other Milds",
         currency="RWF", fx_symbol="RWF=X", region="Lake Kivu", lat=-2.33, lon=29.13,
         harvest="Mar – Jul", census="RWANDA",
         news=dict(q='Rwanda coffee (exports OR NAEB OR harvest OR farmers)', hl="en-US", gl="US", ceid="US:en"),
         terms=["rwanda", "rwandan", "kivu", "nyamasheke", "huye", "naeb", "rubavu"]),
    dict(id="bi", country="Burundi", flag="🇧🇮", benchmark="arabica", group="Other Milds",
         currency="BIF", fx_symbol="BIF=X", region="Kayanza", lat=-2.92, lon=29.63,
         harvest="Mar – Jul", census="BURUNDI",
         news=dict(q='café Burundi (exportation OR récolte OR caféiculteurs)', hl="fr", gl="FR", ceid="FR:fr"),
         terms=["burundi", "burundian", "kayanza", "ngozi", "kirundo", "bujumbura"]),
    dict(id="ug", country="Uganda", flag="🇺🇬", benchmark="robusta", group="Robustas",
         currency="UGX", fx_symbol="UGX=X", region="Mt Elgon / Bugisu", lat=1.08, lon=34.18,
         harvest="Oct – Feb · Apr – Aug", census="UGANDA",
         news=dict(q='Uganda coffee (exports OR UCDA OR robusta OR farmers)', hl="en-US", gl="US", ceid="US:en"),
         terms=["uganda", "ugandan", "bugisu", "mt elgon", "mount elgon", "rwenzori", "ucda", "masaka", "kampala"]),
    dict(id="ye", country="Yemen", flag="🇾🇪", benchmark="arabica", group="Other Milds",
         currency="YER", fx_symbol="YER=X", region="Haraz", lat=15.10, lon=43.95,
         harvest="Oct – Dec", census="YEMEN",
         news=dict(q='Yemen coffee OR "Yemeni coffee" OR mocha coffee Yemen', hl="en-US", gl="US", ceid="US:en"),
         terms=["yemen", "yemeni", "haraz", "sanaa", "sana'a", "bani matar", "mokha", "mocha port"]),
    # ---- Asia
    dict(id="vn", country="Vietnam", flag="🇻🇳", benchmark="robusta", group="Robustas",
         currency="VND", fx_symbol="VND=X", region="Đắk Lắk", lat=12.67, lon=108.04,
         harvest="Oct – Jan", census="VIETNAM",
         news=dict(q='cà phê (giá OR xuất khẩu OR thu hoạch OR robusta)', hl="vi", gl="VN", ceid="VN:vi"),
         terms=["vietnam", "viet nam", "vietnamese", "đắk lắk", "dak lak", "daklak", "buôn ma thuột",
                "buon ma thuot", "lâm đồng", "lam dong", "gia lai", "đắk nông", "dak nong",
                "central highlands", "tây nguyên", "vicofa", "cà phê"]),
    dict(id="id", country="Indonesia", flag="🇮🇩", benchmark="arabica", group="Other Milds",
         currency="IDR", fx_symbol="IDR=X", region="Aceh Gayo", lat=4.60, lon=96.85,
         harvest="Oct – May (Sumatra)", census="INDONESIA",
         news=dict(q='kopi (ekspor OR harga OR panen OR petani)', hl="id", gl="ID", ceid="ID:id"),
         terms=["indonesia", "indonesian", "sumatra", "aceh", "gayo", "mandheling", "lampung", "java",
                "sulawesi", "toraja", "kopi", "bali kintamani"]),
]

ORIGIN_BY_ID = {o["id"]: o for o in ORIGINS}

# --------------------------------------------------------- featured: Costa Rica
# ICAFE's eight coffee regions. Coordinates point at each region's coffee towns;
# harvest windows are typical and shift with altitude and year (low-grown lots
# start earlier, strictly-hard-bean lots finish later).
FEATURED_ORIGIN = "cr"
CR_REGIONS = [
    dict(id="tarrazu", name="Tarrazú", town="San Marcos de Tarrazú", lat=9.66, lon=-84.02,
         alt="1,200–1,900 m", harvest=(11, 3), note="Los Santos zone; highest volume of SHB exports"),
    dict(id="westvalley", name="West Valley", town="Naranjo / Palmares", lat=10.10, lon=-84.40,
         alt="1,200–1,700 m", harvest=(11, 2), note="Many micro-mills; frequent Cup of Excellence winners"),
    dict(id="centralvalley", name="Central Valley", town="Heredia / Barva", lat=10.02, lon=-84.12,
         alt="900–1,600 m", harvest=(11, 2), note="Volcanic soils on Poás, Barva and Irazú slopes"),
    dict(id="tresrios", name="Tres Ríos", town="Tres Ríos", lat=9.90, lon=-83.98,
         alt="1,200–1,650 m", harvest=(11, 2), note="Small, increasingly urbanized region east of San José"),
    dict(id="orosi", name="Orosi", town="Orosi / Paraíso", lat=9.80, lon=-83.85,
         alt="1,000–1,400 m", harvest=(9, 2), note="Valley with long rainy season and early harvest"),
    dict(id="turrialba", name="Turrialba", town="Turrialba", lat=9.90, lon=-83.68,
         alt="600–1,400 m", harvest=(8, 2), note="Lower, wetter, Atlantic-influenced climate"),
    dict(id="brunca", name="Brunca", town="Pérez Zeledón / Coto Brus", lat=9.37, lon=-83.70,
         alt="600–1,700 m", harvest=(8, 1), note="Southern zone; earliest harvest in the country"),
    dict(id="guanacaste", name="Guanacaste", town="Hojancha / Tilarán", lat=10.06, lon=-85.42,
         alt="600–1,300 m", harvest=(10, 2), note="Pacific dry-season influence; naturals and honeys"),
]
CR_REGION_TERMS = {r["id"]: [r["name"].lower(), r["town"].split(" / ")[0].lower()] for r in CR_REGIONS}
CR_REGION_TERMS["tarrazu"] += ["tarrazu", "los santos", "dota", "león cortés", "leon cortes"]
CR_REGION_TERMS["westvalley"] += ["valle occidental", "naranjo", "palmares", "grecia", "sarchí", "sarchi"]
CR_REGION_TERMS["centralvalley"] += ["valle central", "heredia", "barva", "poás", "poas", "alajuela"]
CR_REGION_TERMS["brunca"] += ["pérez zeledón", "perez zeledon", "coto brus", "san isidro de el general"]
CR_REGION_TERMS["guanacaste"] += ["hojancha", "tilarán", "tilaran", "nicoya"]
CR_REGION_TERMS["orosi"] += ["paraíso", "cartago"]

# ------------------------------------------------------------------- news
# Trade-press RSS. Outlets whose feeds block bots (Perfect Daily Grind,
# Comunicaffe, European Coffee Trip, Tico Times) are reached through Google
# News `site:` queries below instead. Dropped Oct 2026, no working feed and
# not indexed by Google News: Royal Coffee, STiR, World Coffee Research,
# ICAFE, CRHoy, El Financiero CR.

RSS_FEEDS = [
    dict(id="dcn", name="Daily Coffee News", url="https://dailycoffeenews.com/feed/", kind="trade"),
    dict(id="sprudge", name="Sprudge", url="https://sprudge.com/feed", kind="specialty"),
    dict(id="barista", name="Barista Magazine", url="https://www.baristamagazine.com/feed/", kind="specialty"),
    dict(id="coffeereview", name="Coffee Review", url="https://www.coffeereview.com/feed/", kind="specialty"),
    dict(id="tcj", name="Tea & Coffee Trade Journal", url="https://www.teaandcoffee.net/feed/", kind="trade"),
    dict(id="freshcup", name="Fresh Cup", url="https://www.freshcup.com/feed/", kind="specialty"),
]

# Extra Costa Rica Google News queries (Spanish + English), on top of the
# per-origin queries every origin gets.
GNEWS_CR = [
    dict(id="gn-cr-icafe", name="ICAFE & cosecha", q='(ICAFE OR "Instituto del Café") Costa Rica', hl="es-419", gl="CR", ceid="CR:es-419"),
    dict(id="gn-cr-regions", name="Regiones cafetaleras",
         q='café (Tarrazú OR "Los Santos" OR Naranjo OR "Pérez Zeledón" OR "Coto Brus" OR Turrialba OR Orosi)',
         hl="es-419", gl="CR", ceid="CR:es-419"),
    dict(id="gn-cr-weather", name="Clima y café", q='café Costa Rica (lluvias OR sequía OR clima OR "El Niño" OR roya)',
         hl="es-419", gl="CR", ceid="CR:es-419"),
    dict(id="gn-cr-coe", name="Cup of Excellence CR", q='"Cup of Excellence" Costa Rica', hl="en-US", gl="US", ceid="US:en"),
    dict(id="gn-cr-ticotimes", name="The Tico Times", q='site:ticotimes.net coffee', hl="en-US", gl="US", ceid="US:en"),
    dict(id="gn-cr-trade", name="CR coffee trade (EN)", q='"Costa Rica" coffee (exports OR harvest OR farmers OR micro mill)',
         hl="en-US", gl="US", ceid="US:en"),
]

# Google News RSS: global English topic queries. Also used as a fallback to
# reach outlets whose own feeds block bots (the `site:` queries).
GNEWS_GLOBAL = [
    dict(id="gn-market", name="Coffee market", q='coffee (arabica OR robusta) (prices OR futures OR market)'),
    dict(id="gn-crop", name="Coffee crops", q='coffee (harvest OR crop OR frost OR drought) (Brazil OR Vietnam OR Colombia)'),
    dict(id="gn-trade", name="Coffee trade policy", q='coffee (tariff OR EUDR OR "deforestation regulation" OR export ban)'),
    dict(id="gn-logistics", name="Coffee logistics", q='coffee (shipping OR freight OR port OR containers) green coffee'),
    dict(id="gn-specialty", name="Specialty coffee", q='"specialty coffee" (auction OR "Cup of Excellence" OR importer OR roaster)'),
    dict(id="gn-industry", name="Coffee industry deals", q='coffee (acquisition OR raises OR funding OR merger) roaster'),
    dict(id="gn-barchart", name="Barchart coffee", q='site:barchart.com coffee'),
    dict(id="gn-stonex", name="StoneX coffee", q='site:stonex.com coffee'),
    dict(id="gn-gcr", name="Global Coffee Report", q='site:gcrmag.com'),
    dict(id="gn-wcp", name="World Coffee Portal", q='site:worldcoffeeportal.com'),
    dict(id="gn-ci", name="Coffee Intelligence", q='site:intelligence.coffee'),
    dict(id="gn-pdg", name="Perfect Daily Grind", q='site:perfectdailygrind.com'),
    dict(id="gn-comunicaffe", name="Comunicaffe", q='site:comunicaffe.com'),
    dict(id="gn-ect", name="European Coffee Trip", q='site:europeancoffeetrip.com'),
    dict(id="gn-ico", name="ICO", q='"International Coffee Organization" OR site:ico.org'),
]

# GDELT DOC 2.0: multilingual (65 languages, searched via English translation).
# Keep the list short; GDELT asks for ~1 request every 5 seconds.
GDELT_QUERIES = [
    dict(id="gd-market", name="Global coffee market", q='(arabica OR robusta) coffee (price OR futures OR exports)'),
    dict(id="gd-weather", name="Coffee weather risk", q='coffee (frost OR drought OR rainfall OR "El Nino" OR "La Nina")'),
    dict(id="gd-policy", name="Coffee trade policy", q='coffee (tariff OR EUDR OR "export ban" OR quota)'),
    dict(id="gd-pt", name="Portuguese-language press", q='coffee (harvest OR exports OR farmers OR price) sourcelang:portuguese'),
    dict(id="gd-es", name="Spanish-language press", q='coffee (harvest OR exports OR farmers OR price) sourcelang:spanish'),
    dict(id="gd-vi", name="Vietnamese-language press", q='coffee (harvest OR exports OR farmers OR price) sourcelang:vietnamese'),
    dict(id="gd-id", name="Indonesian-language press", q='coffee (harvest OR exports OR farmers OR price) sourcelang:indonesian'),
    dict(id="gd-africa", name="East Africa coffee", q='coffee (Ethiopia OR Kenya OR Uganda OR Rwanda OR Burundi) (exports OR harvest OR auction)'),
]

# ------------------------------------------------------------------- data

# CFTC Commitments of Traders, Socrata dataset (disaggregated, futures only).
CFTC_DATASET = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"
CFTC_COFFEE_CODE = "083731"  # ICE Coffee C

# FRED public CSV (no key). IMF Primary Commodity Prices, monthly, US cents/lb.
FRED_SERIES = {
    "PCOFFOTMUSDM": "Other Milds Arabica (IMF, monthly)",
    "PCOFFROBUSDM": "Robustas (IMF, monthly)",
}

CENSUS_IMPORTS = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
CENSUS_HS = "090111"  # coffee, not roasted, not decaffeinated
CENSUS_KEY = os.getenv("CENSUS_API_KEY")  # required by the Census API (free)

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

# USDA FAS Production, Supply & Distribution. Needs a free api.data.gov key.
PSD_KEY = os.getenv("FAS_API_KEY")
PSD_COFFEE = "0711100"  # Coffee, Green
