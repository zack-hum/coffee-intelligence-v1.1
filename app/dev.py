"""Dev panel API (#/dev). Mounted only when DEV_TOOLS=1 (default locally, off on Cloud Run)."""

import os
import platform
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import config, settings
from .demo import live as demo
from .demo.fixtures import mock_transport
from .ingest import common
from .ingest.data import JOBS as DATA_JOBS
from .ingest.data import run_data
from .ingest.news import parse_rss, run_news
from .store import get_store
from .tagging import explain, is_coffee, tag

router = APIRouter(prefix="/api/dev")


def _bg():
    from .main import BG  # avoid import cycle
    return BG


@router.get("/info")
def info():
    st = get_store()
    stats = st.stats() if hasattr(st, "stats") else {"backend": type(st).__name__}
    bg = _bg()
    return {
        "mode": settings.APP_MODE, "mock_prices": os.getenv("MOCK") == "1",
        "store": stats, "python": platform.python_version(),
        "background": {"on": settings.BG_INGEST, "busy": bg["busy"], "last_news": bg["last_news"],
                       "last_data": bg["last_data"], "last_error": bg["last_error"],
                       "news_every": settings.NEWS_EVERY, "data_every": settings.DATA_EVERY,
                       "drip_every": settings.DEMO_DRIP_SECONDS},
        "keys": {k: bool(os.getenv(k)) for k in ("FAS_API_KEY", "CENSUS_API_KEY", "DASH_PASSWORD")},
        "catalog": {"origins": len(config.ORIGINS), "cr_regions": len(config.CR_REGIONS),
                    "rss": len(config.RSS_FEEDS), "gnews": len(config.GNEWS_GLOBAL) + len(config.GNEWS_CR)
                    + sum(1 + (not o["news"]["hl"].startswith("en")) for o in config.ORIGINS),
                    "gdelt": len(config.GDELT_QUERIES), "data_jobs": len(DATA_JOBS)},
        "data_jobs": {k: v[0] for k, v in DATA_JOBS.items()},
    }


async def _with_source(coro_fn):
    """Demo mode runs ingestion against fixtures; live mode hits the real sources."""
    if settings.APP_MODE != "demo":
        return await coro_fn()
    prev = common.TRANSPORT
    common.TRANSPORT = mock_transport()
    try:
        return await coro_fn()
    finally:
        common.TRANSPORT = prev


@router.post("/ingest/news")
async def ingest_news(gdelt: bool = True):
    t0 = time.time()
    res = await _with_source(lambda: run_news(get_store(), include_gdelt=gdelt))
    _bg()["last_news"] = time.time()
    return {**res, "mode": settings.APP_MODE, "took": round(time.time() - t0, 1)}


@router.post("/ingest/data")
async def ingest_data(only: str | None = None):
    res = await _with_source(lambda: run_data(get_store(), only.split(",") if only else None))
    _bg()["last_data"] = time.time()
    return {**res, "mode": settings.APP_MODE}


@router.post("/drip")
def drip(n: int = 1):
    items = [demo.drip_article() for _ in range(max(1, min(n, 20)))]
    get_store().upsert_articles(items)
    return {"added": len(items), "titles": [a["title"] for a in items]}


@router.post("/reset")
async def reset(confirm: str = ""):
    st = get_store()
    if not hasattr(st, "reset"):
        raise HTTPException(400, "reset is only available for the local SQLite archive")
    if settings.APP_MODE != "demo" and confirm != "yes":
        raise HTTPException(400, "live archive: pass confirm=yes to wipe it")
    st.reset()
    seeded = await demo.seed(st) if settings.APP_MODE == "demo" else None
    return {"reset": True, "seeded": bool(seeded)}


class TagIn(BaseModel):
    title: str
    summary: str = ""


@router.post("/tag")
def tag_text(body: TagIn):
    return {"is_coffee": is_coffee(f"{body.title} {body.summary}"),
            "result": tag(body.title, body.summary), "matched": explain(body.title, body.summary)}


class FeedIn(BaseModel):
    url: str
    filter_coffee: bool = False


@router.post("/test-feed")
async def test_feed(body: FeedIn):
    """Fetch any RSS/Atom URL and show how it would be parsed and tagged, without storing."""
    if settings.APP_MODE == "demo":
        raise HTTPException(400, "Switch to live mode (./dev.sh live) to test real feeds")
    async with common.http() as client:
        try:
            r = await client.get(body.url)
            r.raise_for_status()
            items = parse_rss(r.content, {"id": "test", "name": "Test feed", "filter_coffee": body.filter_coffee})
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return {"ok": True, "count": len(items), "items": items[:25]}
