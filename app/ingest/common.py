"""Shared helpers for ingestion jobs."""

import asyncio
import hashlib
import html
import re
import time
import traceback

import httpx

UA = {"User-Agent": "Mozilla/5.0 (compatible; CoffeeOriginMonitor/1.0; personal research)"}
TAG_RE = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


TRANSPORT = None  # tests swap in an httpx.MockTransport


def http() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=20, headers=UA, follow_redirects=True, transport=TRANSPORT)


def clean(text: str, limit: int = 280) -> str:
    """Strip HTML and cap length. Keeping only a short excerpt keeps the
    archive on the safe side of reproducing publishers' articles."""
    t = WS.sub(" ", html.unescape(TAG_RE.sub(" ", text or ""))).strip()
    return (t[: limit - 1].rsplit(" ", 1)[0] + "…") if len(t) > limit else t


def article_id(title: str) -> str:
    norm = re.sub(r"[^\w]+", "", (title or "").lower())[:140]
    return hashlib.sha1(norm.encode()).hexdigest()[:20]


async def run_source(store, source_id: str, name: str, channel: str, coro):
    """Run one source's fetch coroutine, store results, and record health."""
    t0 = time.time()
    try:
        items = await coro
        new = store.upsert_articles(items) if channel != "data" else len(items or [])
        store.record_run(source_id, name=name, channel=channel, ok=True, fetched=len(items or []),
                         new=new, error=None, last_run=t0, duration=round(time.time() - t0, 2))
        return new
    except Exception as e:  # noqa: BLE001
        skipped = str(e).startswith("skipped")  # optional source without credentials
        store.record_run(source_id, name=name, channel=channel, ok=None if skipped else False, fetched=0, new=0,
                         error=f"{type(e).__name__}: {str(e)[:300]}", last_run=t0,
                         duration=round(time.time() - t0, 2),
                         trace=traceback.format_exc(limit=2)[-600:])
        return 0


async def gather_limited(coros, limit: int = 6):
    sem = asyncio.Semaphore(limit)

    async def run(c):
        async with sem:
            return await c
    return await asyncio.gather(*(run(c) for c in coros))
