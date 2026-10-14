"""Upstream data fetchers with a small in-memory TTL cache.

Free sources only:
  * Yahoo Finance chart API   - delayed futures + FX (unofficial, no key)
  * open.er-api.com           - daily FX fallback (no key)
  * Open-Meteo                - weather for growing regions (no key)

Set MOCK=1 to generate synthetic data (useful offline or for UI work).
"""

import asyncio
import math
import os
import random
import time

import httpx

from . import config

MOCK = os.getenv("MOCK") == "1"
UA = {"User-Agent": "Mozilla/5.0 (coffee-monitor)"}
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

_cache: dict[str, tuple[float, object]] = {}
_locks: dict[str, asyncio.Lock] = {}
_client: httpx.AsyncClient | None = None


def client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=12, headers=UA, follow_redirects=True)
    return _client


async def cached(key: str, ttl: int, fn):
    """Return a cached value, refreshing at most once per TTL even under concurrent requests.
    If a refresh fails, the last good value is served (marked stale) rather than an error."""
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
        try:
            val = await fn()
            _cache[key] = (time.time(), val)
            return val
        except Exception as e:  # noqa: BLE001
            if hit:
                stale = dict(hit[1]) if isinstance(hit[1], dict) else hit[1]
                if isinstance(stale, dict):
                    stale["stale"] = True
                return stale
            return {"error": f"{type(e).__name__}: {e}"}


# ---------------------------------------------------------------- Yahoo charts

VALID = {  # interval -> max range Yahoo will serve
    "1m": "5d", "5m": "1mo", "15m": "1mo", "60m": "6mo", "1d": "5y", "1wk": "10y",
}


async def chart(symbol: str, interval: str = "5m", rng: str = "1d") -> dict:
    if MOCK:
        return _mock_chart(symbol, interval, rng)
    r = await client().get(
        YAHOO.format(symbol=symbol),
        params={"interval": interval, "range": rng, "includePrePost": "false"},
    )
    r.raise_for_status()
    res = r.json()["chart"]["result"]
    if not res:
        raise ValueError(f"no data for {symbol}")
    res = res[0]
    meta = res.get("meta", {})
    ts = res.get("timestamp") or []
    q = (res.get("indicators", {}).get("quote") or [{}])[0]
    bars = []
    for i, t in enumerate(ts):
        o, h, l, c = (q.get(k, [None])[i] for k in ("open", "high", "low", "close"))
        if None in (o, h, l, c):
            continue
        bars.append({"time": t, "open": o, "high": h, "low": l, "close": c,
                     "volume": (q.get("volume") or [0] * len(ts))[i] or 0})
    if not bars:
        raise ValueError(f"empty series for {symbol}")
    return {
        "symbol": symbol,
        "price": meta.get("regularMarketPrice", bars[-1]["close"]),
        "prev_close": meta.get("chartPreviousClose") or meta.get("previousClose"),
        "currency": meta.get("currency"),
        "exchange": meta.get("exchangeName"),
        "market_time": meta.get("regularMarketTime", bars[-1]["time"]),
        "bars": bars,
    }


async def quote(symbol: str) -> dict:
    """Latest price + today's change, from a 5-day daily chart (cheap, reliable)."""
    async def fetch():
        d = await chart(symbol, "1d", "5d")
        bars = d["bars"]
        prev = d.get("prev_close") or (bars[-2]["close"] if len(bars) > 1 else None)
        # chartPreviousClose on a 5d range is the close *before* the window; use the
        # second-to-last daily bar instead so "change" means change vs yesterday.
        if len(bars) > 1:
            prev = bars[-2]["close"]
        price = d["price"]
        return {
            "symbol": symbol, "price": price, "prev_close": prev,
            "change": (price - prev) if prev else None,
            "change_pct": ((price / prev - 1) * 100) if prev else None,
            "market_time": d["market_time"],
            "spark": [b["close"] for b in bars],
        }
    return await cached(f"q:{symbol}", config.QUOTE_TTL, fetch)


async def first_working(candidates: list[str]) -> dict:
    """Try each candidate symbol; return the first quote that has a price."""
    errors = []
    for s in candidates:
        q = await quote(s.strip())
        if isinstance(q, dict) and q.get("price") is not None:
            return q
        errors.append(f"{s}: {q.get('error') if isinstance(q, dict) else q}")
    return {"error": "no free source responded", "tried": errors}


# ------------------------------------------------------------------------- FX

async def fx_fallback() -> dict:
    async def fetch():
        if MOCK:
            return {o["currency"]: _MOCK_FX[o["currency"]] for o in config.ORIGINS}
        r = await client().get("https://open.er-api.com/v6/latest/USD")
        r.raise_for_status()
        return r.json()["rates"]
    return await cached("fx:fallback", 3600, fetch)


async def fx(origin: dict) -> dict:
    """USD -> local currency. Intraday from Yahoo; daily open.er-api as fallback."""
    if not origin.get("fx_symbol"):
        return {"price": 1.0, "change_pct": 0.0, "source": "USD economy"}
    q = await quote(origin["fx_symbol"])
    if isinstance(q, dict) and q.get("price"):
        return {**q, "source": "Yahoo (delayed)"}
    rates = await fx_fallback()
    rate = rates.get(origin["currency"]) if isinstance(rates, dict) else None
    if rate:
        return {"price": rate, "change_pct": None, "source": "open.er-api (daily)"}
    return {"error": "fx unavailable"}


# -------------------------------------------------------------------- Weather

async def weather(origin: dict) -> dict:
    async def fetch():
        if MOCK:
            return _mock_weather(origin)
        r = await client().get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": origin["lat"], "longitude": origin["lon"],
                "current": "temperature_2m,relative_humidity_2m,precipitation",
                "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "past_days": 7, "forecast_days": 7, "timezone": "auto",
            },
        )
        r.raise_for_status()
        j = r.json()
        daily = j["daily"]
        rain = daily["precipitation_sum"]
        return {
            "temp_c": j["current"]["temperature_2m"],
            "humidity": j["current"]["relative_humidity_2m"],
            "rain_past7_mm": round(sum(x or 0 for x in rain[:7]), 1),
            "rain_next7_mm": round(sum(x or 0 for x in rain[7:]), 1),
            "tmin_next7": min(x for x in daily["temperature_2m_min"][7:] if x is not None),
            "tmax_next7": max(x for x in daily["temperature_2m_max"][7:] if x is not None),
            "daily_rain": rain,
            "dates": daily["time"],
        }
    return await cached(f"wx:{origin['id']}", config.WEATHER_TTL, fetch)


async def forecast16(place: dict) -> dict:
    """16-day daily forecast (the Open-Meteo maximum), for trip planning."""
    async def fetch():
        if MOCK:
            rnd = random.Random(place["id"] + "f")
            from datetime import date, timedelta
            days = [(date.today() + timedelta(days=i)).isoformat() for i in range(16)]
            return {"dates": days,
                    "rain": [round(max(0, rnd.gauss(6, 7)), 1) for _ in days],
                    "rain_prob": [rnd.randint(20, 95) for _ in days],
                    "tmin": [round(rnd.uniform(12, 17), 1) for _ in days],
                    "tmax": [round(rnd.uniform(22, 28), 1) for _ in days]}
        r = await client().get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": place["lat"], "longitude": place["lon"], "forecast_days": 16, "timezone": "auto",
            "daily": "precipitation_sum,precipitation_probability_max,temperature_2m_min,temperature_2m_max"})
        r.raise_for_status()
        d = r.json()["daily"]
        return {"dates": d["time"], "rain": d["precipitation_sum"], "rain_prob": d["precipitation_probability_max"],
                "tmin": d["temperature_2m_min"], "tmax": d["temperature_2m_max"]}
    return await cached(f"f16:{place['id']}", 3 * 3600, fetch)


# ----------------------------------------------------------------------- Mock

_MOCK_FX = {"CRC": 503.0, "BRL": 5.41, "COP": 4020.0, "VND": 26250.0, "ETB": 142.0,
            "GTQ": 7.7, "HNL": 26.1, "MXN": 18.4, "NIO": 36.7, "PEN": 3.55, "KES": 129.0,
            "RWF": 1440.0, "BIF": 2960.0, "UGX": 3650.0, "YER": 250.0, "IDR": 16300.0, "USD": 1.0}
_MOCK_BASE = {"KC=F": 312.4, "DX-Y.NYB": 99.2,
              **{f"{k}=X": v for k, v in _MOCK_FX.items()}}
_STEP = {"1m": 60, "5m": 300, "15m": 900, "60m": 3600, "1d": 86400, "1wk": 604800}
_SPAN = {"1d": 86400, "5d": 5 * 86400, "1mo": 30 * 86400, "6mo": 182 * 86400,
         "1y": 365 * 86400, "2y": 730 * 86400, "5y": 5 * 365 * 86400, "10y": 3650 * 86400}


def _mock_price(symbol: str, t: float) -> float:
    """Synthetic price as a smooth function of absolute time, so every chart
    range agrees with every other and the 'live' price moves minute to minute."""
    base = _MOCK_BASE.get(symbol, 100.0)
    ph = (sum(map(ord, symbol)) % 97) / 7.0
    fx = symbol.endswith("=X") or symbol.startswith("DX")
    amp = 0.25 if fx else 1.0  # currencies move less than coffee
    w = (0.07 * math.sin(t / 2.6e6 + ph) + 0.035 * math.sin(t / 6.1e5 + 2 * ph)
         + 0.014 * math.sin(t / 7.3e4 + 3 * ph) + 0.005 * math.sin(t / 5.1e3 + ph)
         + 0.0025 * math.sin(t / 830 + 5 * ph))
    return base * (1 + amp * w)


def _mock_chart(symbol, interval, rng):
    step, span = _STEP.get(interval, 300), _SPAN.get(rng, 86400)
    n = max(10, min(1500, span // step))
    now = time.time()
    end = int(now) // step * step
    bars = []
    for i in range(n):
        t = end - (n - 1 - i) * step
        o = _mock_price(symbol, t)
        c = _mock_price(symbol, min(t + step, now))
        rnd = random.Random(f"{symbol}{t}{step}")
        wick = 0.0015 * math.sqrt(step / 300)
        bars.append({"time": t, "open": o, "close": c,
                     "high": max(o, c) * (1 + abs(rnd.gauss(0, wick))),
                     "low": min(o, c) * (1 - abs(rnd.gauss(0, wick))),
                     "volume": int(rnd.uniform(200, 2000))})
    return {"symbol": symbol, "price": bars[-1]["close"], "prev_close": bars[0]["open"],
            "currency": "USX" if symbol == "KC=F" else "USD", "exchange": "MOCK",
            "market_time": int(now), "bars": bars}


def _mock_weather(origin):
    rnd = random.Random(origin["id"])
    rain = [round(max(0, rnd.gauss(5, 6)), 1) for _ in range(14)]
    return {"temp_c": round(rnd.uniform(16, 28), 1), "humidity": rnd.randint(55, 90),
            "rain_past7_mm": round(sum(rain[:7]), 1), "rain_next7_mm": round(sum(rain[7:]), 1),
            "tmin_next7": round(rnd.uniform(10, 16), 1), "tmax_next7": round(rnd.uniform(24, 31), 1),
            "daily_rain": rain, "dates": [f"d{i}" for i in range(14)]}
