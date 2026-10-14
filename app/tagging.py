"""Rule-based tagging: coffee relevance, origins, topics, and a price signal.

Keyword lists are multilingual (EN/ES/PT/VI/ID/FR) because origin-language
press is where supply news shows up first. Edit the dictionaries to tune.
"""

import re
from functools import cache

from .config import CR_REGION_TERMS, ORIGINS

COFFEE_TERMS = ["coffee", "café", "cafe", "cafés", "kaffee", "caffè", "kopi", "cà phê", "ca phe",
                "kahawa", "arabica", "arábica", "robusta", "conilon", "espresso", "barista",
                "roaster", "roastery", "torrefação", "tostadora", "green bean",
                "caficultor", "caficultores", "cafeicultor", "cafeicultores", "cafeticultor",
                "cafeticultores", "cafetalero", "cafetaleros", "cafetalera", "cafetero", "cafeteros",
                "cafeeiro", "cafezal", "roya", "ferrugem do cafeeiro", "micro mill",
                "micromill", "icafe", "anacafé", "anacafe", "ihcafe"]

TOPICS = {
    "prices": ["price", "prices", "futures", "rally", "slump", "ice futures", "arabica futures",
               "robusta futures", "precio", "precios", "preço", "preços", "cotação", "giá", "harga",
               "prix", "contract", "settled", "cents per pound", "per tonne"],
    "weather": ["frost", "drought", "rainfall", "rains", "dry weather", "heatwave", "heat wave",
                "el niño", "el nino", "la niña", "la nina", "weather", "climate", "geada", "seca",
                "chuva", "chuvas", "helada", "sequía", "sequia", "lluvia", "lluvias", "hạn hán",
                "mưa", "kekeringan", "hujan", "sécheresse", "cyclone", "hurricane", "storm"],
    "crop": ["harvest", "crop", "production", "yield", "flowering", "output", "million bags",
             "safra", "colheita", "produção", "florada", "cosecha", "producción",
             "rendimiento", "thu hoạch", "sản lượng", "vụ mùa", "panen", "produksi", "récolte",
             "conab", "estimate", "forecast"],
    "trade": ["export", "exports", "exported", "import", "imports", "shipments", "exportação",
              "exportações", "exportaciones", "exportación", "xuất khẩu", "ekspor", "exportation",
              "cecafé", "cecafe", "trade flows"],
    "policy": ["tariff", "tariffs", "eudr", "deforestation regulation", "regulation", "export ban",
               "quota", "sanction", "arancel", "aranceles", "tarifa", "tarifas", "tarifaço",
               "government", "ministry", "law", "decree", "subsidy", "minimum price"],
    "logistics": ["freight", "shipping", "container", "containers", "port", "vessel", "red sea",
                  "suez", "panama canal", "logistics", "frete", "flete", "cảng", "warehouse delays",
                  "congestion", "strike at port"],
    "stocks": ["certified stocks", "certified stock", "inventories", "inventory", "warehouse stocks",
               "ice stocks", "estoques", "existencias", "graded"],
    "disease": ["rust", "roya", "ferrugem", "borer", "broca", "pest", "pests", "disease",
                "coffee berry disease", "fungus", "plaga"],
    "specialty": ["specialty", "speciality", "cup of excellence", "auction", "geisha", "gesha",
                  "competition", "q grader", "cupping", "micro-lot", "microlot", "single origin",
                  "especialidad", "especiais", "best of panama", "processing method", "anaerobic"],
    "business": ["acquisition", "acquires", "merger", "funding", "raises", "ipo", "investment",
                 "earnings", "revenue", "starbucks", "nestlé", "nestle", "jde", "lavazza",
                 "keurig", "dutch bros", "blue bottle", "retail price", "price increase", "opens"],
    "sustainability": ["sustainab", "certification", "fairtrade", "fair trade", "rainforest alliance",
                       "traceab", "carbon", "regenerative", "living income", "deforestation"],
    "labor": ["workers", "labor", "labour", "wages", "child labor", "slave", "migrant", "pickers"],
    "demand": ["consumption", "demand", "consumers", "sales volume", "coffee drinkers", "consumo"],
}

# Price-direction heuristics for coffee futures. Positive = supply tightening /
# prices up (bullish), negative = supply loosening / prices down (bearish).
BULL = ["frost", "drought", "shortage", "deficit", "smaller crop", "lower crop", "crop loss",
        "crop losses", "rally", "rallies", "surge", "surges", "soar", "soars", "record high",
        "jumps", "climbs", "tight supply", "tighter", "stocks fall", "stocks decline",
        "dry weather", "heatwave", "export ban", "hoarding", "holding back", "geada", "seca",
        "alta", "sobe", "sube", "dispara", "sequía", "sequia", "helada", "heladas", "quebra de safra",
        "caída en la cosecha", "caida en la cosecha", "menor cosecha", "menor produção", "escasez", "tăng", "naik", "rust outbreak", "below average rain"]
BEAR = ["bumper", "record crop", "surplus", "beneficial rain", "good rains", "plunge", "plunges",
        "slump", "slumps", "falls", "drop", "drops", "decline", "declines", "tumble", "tumbles",
        "lower prices", "stocks rise", "stocks climb", "ample supply", "weak demand",
        "demand slows", "queda", "cai", "baja", "cae", "desploma", "cosecha récord", "safra recorde", "buena cosecha",
        "mayor cosecha", "maior safra", "giảm", "turun", "larger crop",
        "bigger crop", "recovery in output"]


@cache
def _rx(term: str) -> re.Pattern:
    # word-boundary-ish match that also works for multi-word and accented terms
    return re.compile(r"(?<![\w])" + re.escape(term) + r"(?![\w])", re.IGNORECASE)


def _any(text: str, terms) -> list[str]:
    return [t for t in terms if _rx(t).search(text)]


def is_coffee(text: str) -> bool:
    return bool(_any(text, COFFEE_TERMS))


def explain(title: str, summary: str = "") -> dict:
    """Which keywords fired, for the Dev panel's tagging playground."""
    text = f"{title} {summary}"
    low = text.lower()
    origins = {o["id"]: m for o in ORIGINS if (m := _any(text, o["terms"]))}
    regions = {f"cr.{rid}": m for rid, terms in CR_REGION_TERMS.items() if (m := _any(text, terms))}
    topics = {k: m for k, terms in TOPICS.items()
              if (m := [t for t in terms if ((t in low) if t.endswith("ab") else bool(_rx(t).search(text)))])}
    return {"coffee_terms": _any(text, COFFEE_TERMS), "origins": origins, "regions": regions,
            "topics": topics, "bullish": _any(text, BULL), "bearish": _any(text, BEAR)}


def tag(title: str, summary: str = "", hint_origins=()) -> dict:
    text = f"{title} {summary}"
    origins = list(dict.fromkeys(
        list(hint_origins) + [o["id"] for o in ORIGINS if _any(text, o["terms"])]))
    if "cr" in origins:  # featured origin: also tag Costa Rica growing regions as "cr.<region>"
        origins += [f"cr.{rid}" for rid, terms in CR_REGION_TERMS.items() if _any(text, terms)]
    low = text.lower()
    topics = [k for k, terms in TOPICS.items() if any(
        (t in low) if t.endswith("ab") else bool(_rx(t).search(text))  # "sustainab" = prefix
        for t in terms)]
    bull, bear = len(_any(text, BULL)), len(_any(text, BEAR))
    score = bull - bear
    signal = "bullish" if score > 0 else "bearish" if score < 0 else "neutral"
    return {"origins": origins, "topics": topics or ["general"], "signal": signal, "score": score}
