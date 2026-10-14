"""Coffee Origin Monitor - specialty coffee market & news intelligence (FastAPI, Cloud Run)."""

import asyncio
import base64
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from datetime import time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import config, settings, sources
from .demo import live as demo
from .ingest.data import JOBS as DATA_JOBS
from .ingest.data import run_data
from .ingest.news import run_news
from .store import get_store

log = logging.getLogger("coffee")
app = FastAPI(title="Coffee Origin Monitor", docs_url=None, redoc_url=None)
STATIC = Path(__file__).parent / "static"
PASSWORD = os.getenv("DASH_PASSWORD")      # basic-auth gate for the UI/API (any username)
INGEST_TOKEN = os.getenv("INGEST_TOKEN")   # shared secret for Cloud Scheduler → /tasks/*
OPEN_PATHS = ("/healthz", "/tasks/")


@app.middleware("http")
async def basic_auth(request: Request, call_next):
    if not PASSWORD or request.url.path.startswith(OPEN_PATHS):
        return await call_next(request)
    header = request.headers.get("authorization", "")
    if header.startswith("Basic "):
        try:
            _, _, pw = base64.b64decode(header[6:]).decode().partition(":")
            if secrets.compare_digest(pw, PASSWORD):
                return await call_next(request)
        except Exception:  # noqa: BLE001
            pass
    return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="coffee"'})


# --------------------------------------------------------------- market hours

SESSIONS = {
    "arabica": ("America/New_York", dtime(4, 15), dtime(13, 30)),
}


def market_status(key: str) -> dict:
    tz, start, end = SESSIONS[key]
    now = datetime.now(ZoneInfo(tz))
    open_ = now.weekday() < 5 and start <= now.time() < end
    return {"open": open_, "hours": f"{start:%H:%M}–{end:%H:%M} {now.tzname()}"}


def origin_public(o: dict) -> dict:
    return {k: v for k, v in o.items() if k not in ("terms", "news")}


# ----------------------------------------------------------------- live data

@app.get("/healthz")
async def healthz():
    return {"ok": True, "mock": sources.MOCK}


@app.get("/api/snapshot")
async def snapshot():
    bench_keys, ctx_keys = list(config.BENCHMARKS), list(config.CONTEXT)
    tasks = ([sources.first_working(config.BENCHMARKS[k]["candidates"]) for k in bench_keys]
             + [sources.quote(config.CONTEXT[k]["symbol"]) for k in ctx_keys]
             + [sources.fx(o) for o in config.ORIGINS]
             + [sources.weather(o) for o in config.ORIGINS])
    res = await asyncio.gather(*tasks)
    nb, nc, no = len(bench_keys), len(ctx_keys), len(config.ORIGINS)
    bench_q, ctx_q = res[:nb], res[nb:nb + nc]
    fx_q, wx_q = res[nb + nc:nb + nc + no], res[nb + nc + no:]
    return JSONResponse({
        "server_time": datetime.now(timezone.utc).isoformat(),
        "mock": sources.MOCK,
        "lb_per_kg": config.LB_PER_KG,
        "benchmarks": {k: {**{kk: v for kk, v in config.BENCHMARKS[k].items() if kk != "candidates"},
                           "quote": q, "session": market_status(k)} for k, q in zip(bench_keys, bench_q)},
        "context": {k: {**config.CONTEXT[k], "quote": q} for k, q in zip(ctx_keys, ctx_q)},
        "origins": [{**origin_public(o), "fx": f, "weather": w}
                    for o, f, w in zip(config.ORIGINS, fx_q, wx_q)],
    })


@app.get("/api/chart")
async def chart(market: str = "arabica", interval: str = "5m", range: str = "1d"):  # noqa: A002
    if interval not in sources.VALID:
        raise HTTPException(400, f"interval must be one of {list(sources.VALID)}")
    if market in config.BENCHMARKS:
        symbols = config.BENCHMARKS[market]["candidates"]
    elif market in config.CONTEXT:
        symbols = [config.CONTEXT[market]["symbol"]]
    else:
        o = config.ORIGIN_BY_ID.get(market)
        if not o or not o["fx_symbol"]:
            raise HTTPException(404, "unknown market")
        symbols = [o["fx_symbol"]]
    last_err = None
    for s in symbols:
        data = await sources.cached(f"c:{s}:{interval}:{range}", config.QUOTE_TTL,
                                    lambda s=s: sources.chart(s.strip(), interval, range))
        if isinstance(data, dict) and data.get("bars"):
            return data
        last_err = data.get("error") if isinstance(data, dict) else data
    raise HTTPException(502, f"no data: {last_err}")


# ---------------------------------------------------------------- archive API

@app.get("/api/news")
def news(q: str | None = None, origin: str | None = None, topic: str | None = None,
         signal: str | None = None, channel: str | None = None, lang: str | None = None,
         before: float | None = None, days: int | None = None, limit: int = 50):
    since = time.time() - days * 86400 if days else None
    items = get_store().query_articles(q=q, origin=origin, topic=topic, signal=signal,
                                       channel=channel, lang=lang, before=before, since=since,
                                       limit=min(limit, 200))
    return {"items": items, "next_before": items[-1]["published"] if len(items) == limit else None}


_stats_cache: dict[int, tuple[float, dict]] = {}


def cached_counts(days: int) -> dict:
    """Counting reads every article in the window, so cache it for 10 minutes."""
    hit = _stats_cache.get(days)
    if hit and time.time() - hit[0] < 600:
        return hit[1]
    val = get_store().article_counts(time.time() - days * 86400)
    _stats_cache[days] = (time.time(), val)
    return val


@app.get("/api/news/stats")
def news_stats(days: int = 7):
    return cached_counts(min(days, 90))


@app.get("/api/series")
def series_list(prefix: str = ""):
    return get_store().list_series(prefix)


@app.get("/api/series/{sid:path}")
def series(sid: str, start: str | None = None):
    s = get_store().get_series(sid)
    if start:
        s["points"] = [p for p in s["points"] if p[0] >= start]
    return s


@app.get("/api/origin/{oid}")
def origin_detail(oid: str):
    o = config.ORIGIN_BY_ID.get(oid)
    if not o:
        raise HTTPException(404, "unknown origin")
    st = get_store()
    year_ago = datetime.fromtimestamp(time.time() - 400 * 86400).date().isoformat()
    sids = [f"wx:{oid}:rain", f"wx:{oid}:tmin", f"wx:{oid}:tmax",
            f"us_imports:{oid}:usd", f"us_imports:{oid}:kg"]
    if o["fx_symbol"]:
        sids.append(f"fx:{o['currency']}")
    out = {"origin": origin_public(o), "series": {}}
    for sid in sids:
        s = st.get_series(sid)
        if sid.startswith(("wx:", "fx:")):
            s["points"] = [p for p in s["points"] if p[0] >= year_ago]
        out["series"][sid] = s
    out["psd"] = {s["sid"]: st.get_series(s["sid"]) for s in st.list_series(f"psd:{oid}:")}
    out["news"] = st.query_articles(origin=oid, limit=40)
    return out


@app.get("/api/costa-rica")
async def costa_rica():
    """Featured-origin page: everything about Costa Rica in one payload."""
    o = config.ORIGIN_BY_ID[config.FEATURED_ORIGIN]
    st = get_store()
    places = [dict(id=f"cr.{r['id']}", lat=r["lat"], lon=r["lon"]) for r in config.CR_REGIONS]
    live = await asyncio.gather(sources.fx(o), sources.first_working(config.BENCHMARKS["arabica"]["candidates"]),
                                *[sources.weather(p) for p in places], *[sources.forecast16(p) for p in places])
    fx, kc = live[0], live[1]
    wx, f16 = live[2:2 + len(places)], live[2 + len(places):]
    since90 = datetime.fromtimestamp(time.time() - 90 * 86400).date().isoformat()
    since400 = datetime.fromtimestamp(time.time() - 400 * 86400).date().isoformat()
    regions = []
    for r, w, f in zip(config.CR_REGIONS, wx, f16):
        rain = st.get_series(f"wx:cr.{r['id']}:rain")["points"]
        regions.append({**r, "weather": w, "forecast": f,
                        "rain90": [p for p in rain if p[0] >= since90],
                        "rain_ytd_mm": round(sum(p[1] for p in rain if p[0] >= f"{date_today().year}-01-01"), 0),
                        "news": st.query_articles(origin=f"cr.{r['id']}", limit=5)})
    imports = {k: st.get_series(f"us_imports:cr:{k}") for k in ("usd", "kg")}
    fxs = st.get_series("fx:CRC")
    fxs["points"] = [p for p in fxs["points"] if p[0] >= since400]
    return {
        "origin": origin_public(o), "fx": fx, "kc": kc, "lb_per_kg": config.LB_PER_KG,
        "regions": regions, "imports": imports, "fx_series": fxs,
        "psd": {s["sid"]: st.get_series(s["sid"]) for s in st.list_series("psd:cr:")},
        "news": st.query_articles(origin="cr", limit=60),
        "counts": cached_counts(30),
    }


def date_today():
    return datetime.now(ZoneInfo("America/Costa_Rica")).date()


@app.get("/api/sources")
def sources_health():
    runs = {r["source_id"]: r for r in get_store().runs()}
    catalog = (
        [dict(source_id=f"rss:{f['id']}", name=f["name"], channel="rss", url=f["url"],
              verified=f.get("verified", False)) for f in config.RSS_FEEDS]
        + [dict(source_id=s["id"], name=f"Google News · {s['name']}", channel="gnews") for s in config.GNEWS_GLOBAL]
        + [dict(source_id=s["id"], name=f"Google News · CR · {s['name']}", channel="gnews") for s in config.GNEWS_CR]
        + [dict(source_id=f"gn-{o['id']}-local", name=f"Google News · {o['country']} (local press)",
                channel="gnews") for o in config.ORIGINS]
        + [dict(source_id=f"gn-{o['id']}-en", name=f"Google News · {o['country']} (English)", channel="gnews")
           for o in config.ORIGINS if not o["news"]["hl"].startswith("en")]
        + [dict(source_id=s["id"], name=f"GDELT · {s['name']}", channel="gdelt") for s in config.GDELT_QUERIES]
        + [dict(source_id=f"data:{k}", name=v[0], channel="data") for k, v in DATA_JOBS.items()]
    )
    return [{**c, **runs.get(c["source_id"], {})} for c in catalog]


@app.get("/api/meta")
def meta():
    from .tagging import TOPICS
    return {"origins": [origin_public(o) for o in config.ORIGINS], "topics": list(TOPICS) + ["general"],
            "featured": config.FEATURED_ORIGIN, "cr_regions": config.CR_REGIONS,
            "mode": settings.APP_MODE, "dev_tools": settings.DEV_TOOLS}


# ------------------------------------------------------------------ ingestion

def _check_token(token: str | None):
    if not INGEST_TOKEN:
        raise HTTPException(503, "INGEST_TOKEN not configured")
    if not token or not secrets.compare_digest(token, INGEST_TOKEN):
        raise HTTPException(403, "bad token")


@app.post("/tasks/ingest/news")
async def task_news(x_ingest_token: str | None = Header(None), gdelt: bool = True):
    _check_token(x_ingest_token)
    return await run_news(get_store(), include_gdelt=gdelt)


@app.post("/tasks/ingest/data")
async def task_data(x_ingest_token: str | None = Header(None), only: str | None = None):
    _check_token(x_ingest_token)
    return await run_data(get_store(), only.split(",") if only else None)


# ------------------------------------------------- in-process ingestion
# demo: seed fixtures on first start, then drip a fresh headline every
#       DEMO_DRIP_SECONDS. live: run real ingestion on a timer. cloud: off
#       (Cloud Scheduler calls /tasks/*).

BG = {"task": None, "last_news": None, "last_data": None, "last_error": None, "busy": False}


async def _demo_loop():
    st = get_store()
    if not st.query_articles(limit=1):
        log.info("demo: seeding archive from fixtures")
        await demo.seed(st)
    while True:
        await asyncio.sleep(settings.DEMO_DRIP_SECONDS)
        try:
            st.upsert_articles([demo.drip_article()])
            BG["last_news"] = time.time()
        except Exception as e:  # noqa: BLE001
            BG["last_error"] = str(e)


async def _live_loop():
    st = get_store()
    last_data = 0.0
    while True:
        try:
            BG["busy"] = True
            await run_news(st)
            BG["last_news"] = time.time()
            if time.time() - last_data > settings.DATA_EVERY:
                await run_data(st)
                last_data = BG["last_data"] = time.time()
        except Exception as e:  # noqa: BLE001
            BG["last_error"] = str(e)
            log.exception("background ingest failed")
        finally:
            BG["busy"] = False
        await asyncio.sleep(settings.NEWS_EVERY)


@app.on_event("startup")
async def _start_bg():
    if not settings.BG_INGEST:
        return
    loop = _demo_loop if settings.APP_MODE == "demo" else _live_loop
    BG["task"] = asyncio.create_task(loop())
    log.info("mode=%s, background ingestion on", settings.APP_MODE)


# ------------------------------------------------------------------- frontend

if settings.DEV_TOOLS:
    from .dev import router as dev_router
    app.include_router(dev_router)

app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})
