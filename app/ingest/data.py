"""Data ingestion: free structured datasets written to the series archive.

Series IDs:
  px:KC, px:DXY                   daily futures / index closes (Yahoo)
  fx:<CUR>                        daily USD→local closes (Yahoo)
  cot:mm_net|mm_long|mm_short|pm_net|swap_net|oi   CFTC disaggregated COT, Coffee C (weekly)
  imf:PCOFFOTMUSDM|PCOFFROBUSDM   IMF monthly prices via FRED (¢/lb)
  enso:oni                        NOAA Oceanic Niño Index (monthly)
  us_imports:<origin>:usd|kg      US green coffee imports by origin (monthly, Census)
  wx:<origin>:rain|tmin|tmax      daily weather history per growing region (Open-Meteo)
  psd:<origin>:<attribute>        USDA PSD supply & demand (annual, needs FAS_API_KEY)
"""

import csv
import io
import re
import time
from datetime import date, timedelta

from .. import config, sources
from .common import http, run_source

SEASON_MONTH = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
                "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}


# --------------------------------------------------------------------- COT

def parse_cot(rows: list[dict]) -> dict[str, dict[str, float]]:
    # Socrata field names are inconsistent (e.g. "swap__positions_short_all"), and
    # there are change_in_*/pct_of_* variants, so match on exact prefixes.
    def find(r, *prefixes):
        for p in prefixes:
            for k, v in r.items():
                if k.startswith(p):
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None
        return None

    out = {k: {} for k in ("mm_long", "mm_short", "mm_net", "pm_net", "swap_net", "oi")}
    for r in rows:
        d = (r.get("report_date_as_yyyy_mm_dd") or "")[:10]
        if not d:
            continue
        mml, mms = find(r, "m_money_positions_long"), find(r, "m_money_positions_short")
        pml, pms = find(r, "prod_merc_positions_long"), find(r, "prod_merc_positions_short")
        swl = find(r, "swap_positions_long", "swap__positions_long")
        sws = find(r, "swap_positions_short", "swap__positions_short")
        oi = find(r, "open_interest_all")
        if mml is not None and mms is not None:
            out["mm_long"][d], out["mm_short"][d], out["mm_net"][d] = mml, mms, mml - mms
        if pml is not None and pms is not None:
            out["pm_net"][d] = pml - pms
        if swl is not None and sws is not None:
            out["swap_net"][d] = swl - sws
        if oi is not None:
            out["oi"][d] = oi
    return out


async def job_cot(store, client):
    r = await client.get(config.CFTC_DATASET, params={
        "$where": f"cftc_contract_market_code='{config.CFTC_COFFEE_CODE}'",
        "$order": "report_date_as_yyyy_mm_dd DESC", "$limit": 780})
    r.raise_for_status()
    series = parse_cot(r.json())
    labels = {"mm_net": "Managed money net position", "mm_long": "Managed money long",
              "mm_short": "Managed money short", "pm_net": "Producer/merchant net position",
              "swap_net": "Swap dealer net position", "oi": "Open interest"}
    written = []
    for k, pts in series.items():
        if pts:
            store.put_series(f"cot:{k}", pts, {"name": labels[k], "unit": "contracts",
                                               "source": "CFTC COT (disaggregated)", "freq": "weekly"})
            written.append(k)
    if not written:
        raise ValueError("no COT rows parsed")
    return written


# -------------------------------------------------------------------- FRED

def parse_fred_csv(text: str) -> dict[str, float]:
    rdr = csv.reader(io.StringIO(text))
    next(rdr, None)
    out = {}
    for row in rdr:
        if len(row) >= 2 and row[1] not in ("", "."):
            try:
                out[row[0][:7] + "-01"] = float(row[1])
            except ValueError:
                pass
    return out


async def job_fred(store, client):
    written = []
    for sid, name in config.FRED_SERIES.items():
        r = await client.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": sid})
        r.raise_for_status()
        pts = parse_fred_csv(r.text)
        if pts:
            store.put_series(f"imf:{sid}", pts, {"name": name, "unit": "¢/lb", "source": "IMF via FRED",
                                                 "freq": "monthly"})
            written.append(sid)
    if not written:
        raise ValueError("FRED returned no data")
    return written


# --------------------------------------------------------------------- ONI

def parse_oni(text: str) -> dict[str, float]:
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] in SEASON_MONTH:
            try:
                out[f"{int(parts[1]):04d}-{SEASON_MONTH[parts[0]]:02d}-01"] = float(parts[3])
            except ValueError:
                pass
    return out


async def job_oni(store, client):
    r = await client.get(config.ONI_URL)
    r.raise_for_status()
    pts = parse_oni(r.text)
    if not pts:
        raise ValueError("ONI file not parsed")
    store.put_series("enso:oni", pts, {"name": "Oceanic Niño Index (ENSO)", "unit": "°C anomaly",
                                       "source": "NOAA CPC", "freq": "monthly",
                                       "note": "≥ +0.5 El Niño, ≤ −0.5 La Niña"})
    return ["oni"]


# ------------------------------------------------------------- US imports

def parse_census(rows: list[list]) -> dict[str, dict[str, dict[str, float]]]:
    """Returns {origin_id|'total': {'usd': {...}, 'kg': {...}}}."""
    if not rows:
        return {}
    head = rows[0]
    ix = {h: i for i, h in enumerate(head)}
    by_name = {o["census"]: o["id"] for o in config.ORIGINS}
    out: dict = {}
    for r in rows[1:]:
        name = (r[ix["CTY_NAME"]] or "").upper()
        oid = "total" if name.startswith("TOTAL FOR ALL") else next(
            (v for k, v in by_name.items() if name == k or name.startswith(k + " ")), None)
        if not oid:
            continue
        month = r[ix["time"]][:7] + "-01"
        rec = out.setdefault(oid, {"usd": {}, "kg": {}})
        try:
            rec["usd"][month] = float(r[ix["GEN_VAL_MO"]])
            # HS6 rows carry no quantity; shipping weight is within ~1% of the HS10 kg totals
            rec["kg"][month] = float(r[ix["AIR_WGT_MO"]]) + float(r[ix["VES_WGT_MO"]])
        except (KeyError, TypeError, ValueError):
            pass
    return out


async def job_census(store, client):
    if not config.CENSUS_KEY:
        raise ValueError("skipped: set CENSUS_API_KEY (free at api.census.gov/data/key_signup.html) to enable")
    start = (date.today().replace(day=1) - timedelta(days=365 * 3)).strftime("%Y-%m")
    # CTY_CODE must be requested, or the API returns only the all-countries total
    params = {"get": "CTY_CODE,CTY_NAME,GEN_VAL_MO,AIR_WGT_MO,VES_WGT_MO", "I_COMMODITY": config.CENSUS_HS,
              "time": f"from {start}"}
    params["key"] = config.CENSUS_KEY
    r = await client.get(config.CENSUS_IMPORTS, params=params)
    r.raise_for_status()
    data = parse_census(r.json())
    if not data:
        raise ValueError("no Census rows matched configured origins")
    for oid, rec in data.items():
        label = "All countries" if oid == "total" else config.ORIGIN_BY_ID[oid]["country"]
        store.put_series(f"us_imports:{oid}:usd", rec["usd"], {"name": f"US green coffee imports · {label}",
                         "unit": "USD", "source": "US Census (HS 090111)", "freq": "monthly"})
        store.put_series(f"us_imports:{oid}:kg", rec["kg"], {"name": f"US green coffee imports · {label}",
                         "unit": "kg", "source": "US Census (HS 090111)", "freq": "monthly"})
    return list(data)


# ------------------------------------------------------------ weather hist

async def job_weather(store, client):
    written = []
    cr_regions = [dict(id=f"cr.{r['id']}", region=r["name"], lat=r["lat"], lon=r["lon"])
                  for r in config.CR_REGIONS]
    for o in config.ORIGINS + cr_regions:
        have = store.get_series(f"wx:{o['id']}:rain")["points"]
        if len(have) < 300:  # first run: backfill a year from the archive API
            start = (date.today() - timedelta(days=372)).isoformat()
            end = (date.today() - timedelta(days=6)).isoformat()
            r = await client.get("https://archive-api.open-meteo.com/v1/archive", params={
                "latitude": o["lat"], "longitude": o["lon"], "start_date": start, "end_date": end,
                "daily": "precipitation_sum,temperature_2m_min,temperature_2m_max", "timezone": "auto"})
            if r.status_code == 200:
                _store_wx(store, o, r.json())
        r = await client.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": o["lat"], "longitude": o["lon"], "past_days": 14, "forecast_days": 1,
            "daily": "precipitation_sum,temperature_2m_min,temperature_2m_max", "timezone": "auto"})
        r.raise_for_status()
        _store_wx(store, o, r.json())
        written.append(o["id"])
    return written


def _store_wx(store, o, j):
    d = j.get("daily", {})
    days = d.get("time", [])
    today = date.today().isoformat()
    for key, field, unit in (("rain", "precipitation_sum", "mm"), ("tmin", "temperature_2m_min", "°C"),
                             ("tmax", "temperature_2m_max", "°C")):
        pts = {t: v for t, v in zip(days, d.get(field, [])) if v is not None and t <= today}
        store.put_series(f"wx:{o['id']}:{key}", pts, {"name": f"{o['region']} {key}", "unit": unit,
                                                      "source": "Open-Meteo", "freq": "daily"})


# ---------------------------------------------------------- market closes

async def job_closes(store, client):
    targets = [("px:KC", config.BENCHMARKS["arabica"]["candidates"], "Arabica 'C' front month", "¢/lb"),
               ("px:DXY", [config.CONTEXT["dxy"]["symbol"]], "US Dollar Index", "index")]
    seen = set()
    for o in config.ORIGINS:
        if o["fx_symbol"] and o["currency"] not in seen:
            seen.add(o["currency"])
            targets.append((f"fx:{o['currency']}", [o["fx_symbol"]], f"USD/{o['currency']}", o["currency"]))
    written, errors = [], []
    for sid, syms, name, unit in targets:
        for s in syms:
            try:
                d = await sources.chart(s.strip(), "1d", "2y")
                pts = {date.fromtimestamp(b["time"]).isoformat(): b["close"] for b in d["bars"]}
                store.put_series(sid, pts, {"name": name, "unit": unit, "source": f"Yahoo ({s})", "freq": "daily"})
                written.append(sid)
                break
            except Exception as e:  # noqa: BLE001
                errors.append(f"{s}: {e}")
    if not written:
        raise ValueError("; ".join(errors)[:300])
    return written


# --------------------------------------------------------------- USDA PSD

def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


PSD_KEEP = ("production", "exports", "ending stocks", "domestic consumption", "imports",
            "arabica production", "robusta production", "bean exports")


async def job_psd(store, client):
    if not config.PSD_KEY:
        raise ValueError("skipped: set FAS_API_KEY (free at api.data.gov) to enable")
    base = "https://apps.fas.usda.gov/OpenData/api/psd"
    h = {"API_KEY": config.PSD_KEY}
    attrs = {a["attributeId"]: a["attributeName"].strip() for a in
             (await client.get(f"{base}/commodityAttributes", headers=h)).raise_for_status().json()}
    countries = {c["countryCode"]: c["countryName"].strip().upper() for c in
                 (await client.get(f"{base}/countries", headers=h)).raise_for_status().json()}
    by_name = {o["census"]: o["id"] for o in config.ORIGINS}
    by_name["VIETNAM"] = "vn"
    yr = date.today().year
    out: dict = {}
    for y in range(yr - 5, yr + 1):
        r = await client.get(f"{base}/commodity/{config.PSD_COFFEE}/country/all/year/{y}", headers=h)
        if r.status_code != 200:
            continue
        for row in r.json():
            oid = by_name.get(countries.get(row.get("countryCode"), ""))
            name = attrs.get(row.get("attributeId"), "")
            if oid and name.lower() in PSD_KEEP:
                out.setdefault((oid, name), {})[str(row.get("marketYear", y))] = row.get("value")
    for (oid, name), pts in out.items():
        store.put_series(f"psd:{oid}:{_slug(name)}", pts, {"name": name, "unit": "1000 60-kg bags",
                         "source": "USDA FAS PSD", "freq": "annual (marketing year)"})
    if not out:
        raise ValueError("PSD returned no coffee rows")
    return [f"{k[0]}:{k[1]}" for k in out]


# --------------------------------------------------------------------- run

JOBS = {
    "closes": ("Futures & FX daily closes (Yahoo)", job_closes),
    "cot": ("CFTC Commitments of Traders", job_cot),
    "fred": ("IMF monthly coffee prices (FRED)", job_fred),
    "oni": ("NOAA ENSO index", job_oni),
    "census": ("US Census green coffee imports", job_census),
    "weather": ("Open-Meteo weather history (18 regions)", job_weather),
    "psd": ("USDA FAS PSD supply & demand", job_psd),
}


async def run_data(store, only: list[str] | None = None) -> dict:
    t0 = time.time()
    done = {}
    async with http() as client:
        for key, (name, fn) in JOBS.items():
            if only and key not in only:
                continue
            done[key] = await run_source(store, f"data:{key}", name, "data", fn(store, client))
    return {"jobs": done, "seconds": round(time.time() - t0, 1)}
