"""News ingestion: trade-press RSS, Google News RSS, GDELT DOC 2.0."""

import asyncio
import calendar
import os
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

import feedparser

from .. import config
from ..tagging import is_coffee, tag
from .common import article_id, clean, gather_limited, http, run_source

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_DELAY = float(os.getenv("GDELT_DELAY", "5.5"))
GNEWS_URL = "https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"

LANG_CODES = {"english": "en", "spanish": "es", "portuguese": "pt", "vietnamese": "vi",
              "indonesian": "id", "french": "fr", "german": "de", "italian": "it",
              "japanese": "ja", "chinese": "zh", "korean": "ko", "arabic": "ar", "swahili": "sw",
              "amharic": "am", "dutch": "nl", "turkish": "tr", "russian": "ru"}


def _entry_time(e) -> float:
    for k in ("published_parsed", "updated_parsed"):
        if e.get(k):
            return float(calendar.timegm(e[k]))
    return time.time()


def _make(title, url, summary, source_id, source_name, channel, lang, published,
          hint_origins=(), require_coffee=True):
    title = clean(title, 300)
    summary = clean(summary)
    if not title or not url:
        return None
    if require_coffee and not is_coffee(f"{title} {summary}"):
        return None
    tags = tag(title, summary, hint_origins)
    return {"id": article_id(title), "url": url, "title": title, "summary": summary,
            "source_id": source_id, "source_name": source_name, "channel": channel,
            "lang": lang, "published": published, "fetched": time.time(), **tags}


def parse_rss(raw: bytes, feed: dict) -> list[dict]:
    parsed = feedparser.parse(raw)
    if not parsed.version:  # e.g. an HTML block page or a login wall
        raise ValueError("response is not an RSS/Atom feed (blocked or moved?)")
    lang = (parsed.feed.get("language") or "en")[:2].lower()
    out = []
    for e in parsed.entries[:60]:
        # general-news feeds (e.g. Tico Times) are filtered to coffee stories
        a = _make(e.get("title"), e.get("link"), e.get("summary", ""), feed["id"], feed["name"],
                  "rss", lang, _entry_time(e), hint_origins=feed.get("origins", ()),
                  require_coffee=feed.get("filter_coffee", False))
        if a:
            a["kind"] = feed.get("kind")
            out.append(a)
    return out


def parse_gnews(raw: bytes, src: dict, lang: str, hint_origins=()) -> list[dict]:
    parsed = feedparser.parse(raw)
    if not parsed.version:
        raise ValueError("response is not an RSS feed (rate limited?)")
    out = []
    for e in parsed.entries[:50]:
        title = e.get("title", "")
        publisher = (e.get("source") or {}).get("title")
        if " - " in title:  # Google appends " - Publisher"
            head, _, tail = title.rpartition(" - ")
            title, publisher = head, publisher or tail
        a = _make(title, e.get("link"), "", src["id"], publisher or "Google News", "gnews",
                  lang, _entry_time(e), hint_origins)
        if a:
            a["via"] = src["name"]
            out.append(a)
    return out


def parse_gdelt(payload: dict, src: dict) -> list[dict]:
    out = []
    for g in payload.get("articles", []) or []:
        try:
            pub = datetime.strptime(g["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).timestamp()
        except Exception:  # noqa: BLE001
            pub = time.time()
        lang = LANG_CODES.get((g.get("language") or "").lower(), (g.get("language") or "en")[:2].lower())
        # GDELT matches on its English translation, so a non-English title may not
        # contain a coffee word in its own language; trust the query instead.
        a = _make(g.get("title"), g.get("url"), "", src["id"], g.get("domain") or "GDELT", "gdelt",
                  lang, pub, require_coffee=(lang == "en"))
        if a:
            a["country"] = g.get("sourcecountry")
            a["via"] = src["name"]
            out.append(a)
    return out


# ------------------------------------------------------------------ fetchers

async def fetch_rss(client, feed):
    r = await client.get(feed["url"])
    r.raise_for_status()
    return parse_rss(r.content, feed)


async def fetch_gnews(client, src, hl="en-US", gl="US", ceid="US:en", hint_origins=()):
    url = GNEWS_URL.format(q=quote_plus(src["q"] + " when:7d"), hl=hl, gl=gl, ceid=ceid)
    r = await client.get(url)
    r.raise_for_status()
    return parse_gnews(r.content, src, hl[:2], hint_origins)


async def fetch_gdelt(client, src, timespan="1d"):
    r = await client.get(GDELT_URL, params={"query": src["q"], "mode": "artlist", "format": "json",
                                           "maxrecords": 100, "timespan": timespan, "sort": "datedesc"})
    r.raise_for_status()
    if not r.text.strip().startswith("{"):
        # GDELT returns plain-text errors (e.g. query too short, rate limited)
        raise ValueError(r.text.strip()[:200])
    return parse_gdelt(r.json(), src)


# ----------------------------------------------------------------------- job

async def run_news(store, include_gdelt: bool = True) -> dict:
    t0 = time.time()
    async with http() as client:
        jobs = []
        for f in config.RSS_FEEDS:
            jobs.append(run_source(store, f"rss:{f['id']}", f["name"], "rss", fetch_rss(client, f)))
        for s in config.GNEWS_GLOBAL:
            jobs.append(run_source(store, s["id"], f"Google News · {s['name']}", "gnews",
                                   fetch_gnews(client, s)))
        for s in config.GNEWS_CR:
            jobs.append(run_source(store, s["id"], f"Google News · CR · {s['name']}", "gnews",
                                   fetch_gnews(client, s, s["hl"], s["gl"], s["ceid"], ["cr"])))
        for o in config.ORIGINS:
            n = o["news"]
            local = {"id": f"gn-{o['id']}-local", "name": f"{o['country']} (local press)", "q": n["q"]}
            jobs.append(run_source(store, local["id"], f"Google News · {local['name']}", "gnews",
                                   fetch_gnews(client, local, n["hl"], n["gl"], n["ceid"], [o["id"]])))
            if not n["hl"].startswith("en"):
                en = {"id": f"gn-{o['id']}-en", "name": f"{o['country']} (English)",
                      "q": f'"{o["country"]}" coffee'}
                jobs.append(run_source(store, en["id"], f"Google News · {en['name']}", "gnews",
                                       fetch_gnews(client, en, hint_origins=[o["id"]])))
        results = await gather_limited(jobs, limit=6)

        gdelt_new = 0
        if include_gdelt:
            for i, s in enumerate(config.GDELT_QUERIES):
                if i:
                    await asyncio.sleep(GDELT_DELAY)  # GDELT courtesy rate limit
                gdelt_new += await run_source(store, s["id"], f"GDELT · {s['name']}", "gdelt",
                                              fetch_gdelt(client, s))
    return {"new": sum(results) + gdelt_new, "sources": len(results) + (len(config.GDELT_QUERIES) if include_gdelt else 0),
            "seconds": round(time.time() - t0, 1)}
