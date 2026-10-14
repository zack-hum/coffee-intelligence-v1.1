"""Demo mode: seed the archive from fixtures and keep it moving.

The seed runs the *real* ingestion pipeline (parsers, tagging, dedupe, store)
against offline fixtures, so what you see in demo mode exercises the same code
that runs against live sources.
"""

import random
import time

from .. import config
from ..ingest import common
from ..ingest.data import run_data
from ..ingest.news import run_news
from ..tagging import tag
from .fixtures import mock_transport


async def seed(store) -> dict:
    prev, prev_key = common.TRANSPORT, config.CENSUS_KEY
    common.TRANSPORT = mock_transport()
    config.CENSUS_KEY = prev_key or "demo"  # the mocked Census API needs no real key
    try:
        news = await run_news(store)
        data = await run_data(store)
    finally:
        common.TRANSPORT, config.CENSUS_KEY = prev, prev_key
    return {"news": news, "data": data}


# Templates for drip-fed headlines. {o}=country, {r}=growing region.
TEMPLATES = [
    ("{o} coffee exports rise {n}% in latest monthly data", "trade"),
    ("{o} coffee exports fall {n}% as harvest delays shipments", "trade"),
    ("Dry weather in {r} raises concerns for next {o} coffee crop", "weather"),
    ("Heavy rains in {r} slow coffee harvest, producers say", "weather"),
    ("{o} coffee farmers in {r} report bumper crop", "crop"),
    ("Coffee leaf rust spreads in {r}, {o} growers warn", "disease"),
    ("Specialty buyers chase {r} micro-lots as {o} auction prices climb", "specialty"),
    ("Arabica futures rally as traders watch {o} supply", "prices"),
    ("Arabica futures slump on improved {o} crop outlook", "prices"),
    ("{o} government reviews coffee export rules", "policy"),
    ("Freight delays hit {o} green coffee shipments", "logistics"),
    ("Roaster opens sourcing office in {r} to buy direct from {o} farms", "business"),
]
CR_TEMPLATES = [
    "ICAFE reporta avance de cosecha en {r}",
    "Lluvias en {r} retrasan la recolección de café",
    "Productores de {r} piden apoyo por escasez de recolectores",
    "Microbeneficios de {r} reciben compradores internacionales",
    "Precio del café en {r} sube por alza en Nueva York",
]


def drip_article() -> dict:
    """One fresh, believable headline. ~1 in 3 is about Costa Rica."""
    rnd = random.Random()
    now = time.time()
    if rnd.random() < 0.33:
        r = rnd.choice(config.CR_REGIONS)
        title = rnd.choice(CR_TEMPLATES).format(r=r["name"])
        lang, source, hint = "es", rnd.choice(["La Nación", "CRHoy", "El Financiero", "Teletica"]), ["cr"]
    else:
        o = rnd.choice(config.ORIGINS)
        t, _ = rnd.choice(TEMPLATES)
        title = t.format(o=o["country"], r=o["region"], n=rnd.randint(3, 24))
        lang, source, hint = "en", rnd.choice(["Reuters", "Bloomberg", "Daily Coffee News", "Perfect Daily Grind", "Barchart"]), []
    return {"id": common.article_id(title + str(now)), "url": "https://example.com/demo/" + str(int(now)),
            "title": title, "summary": "Demo headline generated locally to show live updates.",
            "source_id": "demo:drip", "source_name": f"{source} (demo)", "channel": "rss", "lang": lang,
            "published": now, "fetched": now, **tag(title, "", hint)}
