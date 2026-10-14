"""Offline fixtures shaped like the real upstream responses.

`mock_transport()` returns an httpx.MockTransport that answers every source the
ingestion jobs call, so the full pipeline runs with no network. Used by the
tests and by scripts/seed_demo.py to populate a demo archive.
"""

import math
import random
import time
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime

import httpx

NOW = time.time()


def _rfc822(ts):
    return format_datetime(datetime.fromtimestamp(ts, timezone.utc))


def wordpress_rss(name, items):
    body = "".join(f"""<item><title>{t}</title><link>{u}</link>
      <pubDate>{_rfc822(ts)}</pubDate><description><![CDATA[<p>{d}</p>]]></description></item>"""
                   for t, u, d, ts in items)
    return f"""<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>
      <title>{name}</title><link>https://example.com</link><language>en-US</language>
      <description>{name}</description>{body}</channel></rss>"""


def gnews_rss(items):
    body = "".join(f"""<item><title>{t} - {p}</title><link>https://news.google.com/rss/articles/{abs(hash(t))}</link>
      <pubDate>{_rfc822(ts)}</pubDate><source url="https://{p.lower().replace(' ', '')}.com">{p}</source></item>"""
                   for t, p, ts in items)
    return f"""<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>
      <title>Google News</title>{body}</channel></rss>"""


TRADE = [
    ("Arabica passes US$3/lb on stronger real as Brazil holds back supply",
     "Futures rallied as Brazilian farmers held back beans and the real strengthened against the dollar."),
    ("Conab trims Brazil arabica estimate after dry spell in Sul de Minas",
     "Brazil's crop agency lowered its forecast citing below average rain during flowering in Minas Gerais."),
    ("Vietnam robusta harvest begins in Dak Lak amid labor shortages",
     "Farmers in the Central Highlands started picking cherries as exporters report tight supply."),
    ("Colombia coffee exports rise 12% in September, FNC says",
     "The Federación Nacional de Cafeteros reported higher shipments and a recovery in output."),
    ("EU confirms EUDR compliance timeline for coffee importers",
     "Importers face traceability requirements under the deforestation regulation."),
    ("Red Sea disruption pushes freight for East African coffee higher",
     "Container shipping costs from Djibouti and Mombasa climbed as vessels reroute around the Cape."),
    ("Cup of Excellence Guatemala auction sets record for Huehuetenango geisha",
     "The specialty auction drew strong bids from roasters in Asia and the US."),
    ("ICE certified arabica stocks fall to 18-month low",
     "Certified stocks decline as fewer lots are graded in Antwerp and Houston."),
    ("Kenya Nairobi coffee auction prices climb on AA demand",
     "Nyeri and Kirinyaga lots led the weekly sale."),
    ("Ethiopia's coffee export earnings hit record as ECTA reforms take hold",
     "Shipments from Sidama and Guji increased in the first quarter of the fiscal year."),
    ("Honduras IHCAFE warns of rust outbreak in Santa Bárbara",
     "Coffee leaf rust spread after heavy rains, the institute said."),
    ("US tariff exemption for coffee imports under review",
     "Roasters lobbied to keep green coffee off the tariff list."),
    ("Peru coffee farmers in Jaén report bumper crop, prices drop",
     "Good rains produced a larger crop across Cajamarca."),
    ("Specialty roaster raises $12M to expand direct trade sourcing",
     "The funding will support traceable sourcing from Rwanda and Burundi."),
    ("La Niña watch: forecasters see 60% chance this winter",
     "A La Niña could mean drought risk for southern Brazil coffee areas."),
    ("Indonesia Gayo coffee exports slow as harvest delayed in Aceh",
     "Heavy rainfall delayed picking across Sumatra."),
]

LOCAL = {
    "cr": [("ICAFE estima cosecha 2026-2027 similar a la anterior pese a lluvias en Tarrazú", "La Nación"),
           ("Productores de Naranjo inician recolección temprana por maduración acelerada", "CRHoy"),
           ("Escasez de recolectores preocupa a cafetaleros de Pérez Zeledón", "Teletica"),
           ("Precio del café costarricense sube por alza en bolsa de Nueva York", "El Financiero"),
           ("Roya reaparece en fincas de Coto Brus tras lluvias intensas", "Diario Extra")],
    "br": [("Geada atinge lavouras de café no Sul de Minas, preço dispara", "Notícias Agrícolas"),
           ("Exportações de café do Brasil caem 8% em setembro, aponta Cecafé", "Revista Cultivar"),
           ("Safra de café 2027: florada é boa no Cerrado Mineiro após chuvas", "Globo Rural")],
    "co": [("Precio interno del café sube a nuevo récord por alza en Nueva York", "Valora Analitik"),
           ("Cosecha cafetera en Huila avanza con lluvias por encima de lo normal", "La Nación")],
    "vn": [("Giá cà phê hôm nay tăng mạnh tại Đắk Lắk", "VnExpress"),
           ("Xuất khẩu cà phê tháng 9 giảm do thiếu hàng", "Báo Đầu tư")],
    "gt": [("Anacafé proyecta cosecha estable para Huehuetenango", "Prensa Libre")],
    "mx": [("Productores de café en Chiapas reportan pérdidas por roya", "El Heraldo de Chiapas")],
    "pe": [("Exportaciones de café peruano caen por menor producción en Cajamarca", "Gestión")],
    "id": [("Harga kopi Gayo naik, petani Aceh tahan panen", "Kompas")],
    "bi": [("Burundi: la récolte de café en hausse à Kayanza", "Iwacu")],
    "ke": [("Kenya coffee auction volumes drop as farmers shift to direct sales", "Business Daily")],
    "et": [("Ethiopia coffee export revenue climbs as Yirgacheffe demand grows", "Addis Standard")],
    "ug": [("Uganda coffee exports rise on robusta demand, UCDA says", "Daily Monitor")],
    "rw": [("Rwanda NAEB targets higher coffee exports this season", "The New Times")],
}


def _gdelt(articles):
    return {"articles": [{"url": f"https://{d}/a/{i}", "title": t, "seendate":
                          datetime.fromtimestamp(NOW - i * 3600, timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                          "domain": d, "language": lang, "sourcecountry": c}
                         for i, (t, d, lang, c) in enumerate(articles)]}


def gdelt():
    return _gdelt([
    ("Coffee prices hit two-week high on Brazil frost fears", "reuters.com", "English", "United States"),
    ("Café: seca no Espírito Santo preocupa produtores de conilon", "noticiasagricolas.com.br", "Portuguese", "Brazil"),
    ("Exportaciones de café de Colombia crecen en septiembre", "portafolio.co", "Spanish", "Colombia"),
    ("Giá cà phê xuất khẩu giảm khi nguồn cung Brazil dồi dào", "vneconomy.vn", "Vietnamese", "Vietnam"),
    ])


def cot_rows(n=104):
    rows, d = [], date.today()
    d -= timedelta(days=(d.weekday() - 1) % 7)  # last Tuesday
    rnd = random.Random(7)
    mm = 40000
    for i in range(n):
        mm += rnd.randint(-3500, 3500)
        dt = d - timedelta(weeks=i)
        rows.append({"report_date_as_yyyy_mm_dd": dt.isoformat() + "T00:00:00.000",
                     "market_and_exchange_names": "COFFEE C - ICE FUTURES U.S.",
                     "cftc_contract_market_code": "083731",
                     "open_interest_all": str(190000 + rnd.randint(-20000, 20000)),
                     "m_money_positions_long_all": str(max(5000, 55000 + mm // 2)),
                     "m_money_positions_short_all": str(max(5000, 55000 - mm // 2)),
                     "change_in_m_money_long_all": "999999",  # decoy field
                     "prod_merc_positions_long": str(60000 + rnd.randint(-5000, 5000)),
                     "prod_merc_positions_short": str(110000 + rnd.randint(-8000, 8000)),
                     "swap_positions_long_all": str(40000 + rnd.randint(-3000, 3000)),
                     "swap__positions_short_all": str(15000 + rnd.randint(-2000, 2000))})
    return rows


def fred_csv(base):
    lines, rnd, v = ["observation_date,X"], random.Random(base), base * 0.4
    d = date(2000, 1, 1)
    while d < date.today().replace(day=1):
        v = max(40, v * (1 + rnd.gauss(0.006, 0.05)))
        lines.append(f"{d.isoformat()},{v:.2f}")
        d = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return "\n".join(lines)


def oni_txt():
    out, seasons = ["SEAS  YR   TOTAL   ANOM"], ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
    for y in range(2015, date.today().year + 1):
        for i, s in enumerate(seasons):
            if y == date.today().year and i >= date.today().month - 1:
                break
            a = 1.2 * math.sin((y * 12 + i) / 9.0)
            out.append(f"  {s} {y}   {26.5 + a:.2f}   {a:.2f}")
    return "\n".join(out)


def census_rows():
    from app import config
    rows = [["CTY_CODE", "CTY_NAME", "GEN_VAL_MO", "AIR_WGT_MO", "VES_WGT_MO", "I_COMMODITY", "time"]]
    rnd = random.Random(3)
    share = {"br": .30, "co": .22, "vn": .08, "gt": .05, "hn": .05, "pe": .04, "mx": .04, "ni": .04,
             "et": .03, "cr": .02, "id": .03, "ug": .03, "ke": .01, "sv": .01, "pa": .005, "rw": .005,
             "bi": .003, "ye": .001}
    m = date.today().replace(day=1) - timedelta(days=60)
    for i in range(30):
        month = (m - timedelta(days=30 * i)).strftime("%Y-%m")
        total_kg = 110e6 * (1 + rnd.gauss(0, 0.08))
        rows.append(["-", "TOTAL FOR ALL COUNTRIES", str(int(total_kg * 7.2)), "0", str(int(total_kg)), "090111", month])
        for o in config.ORIGINS:
            kg = total_kg * share[o["id"]] * (1 + rnd.gauss(0, 0.2))
            price = 6.8 + (3 if o["id"] in ("pa", "ke", "et", "ye") else 0) + rnd.gauss(0, .3)
            rows.append(["0", o["census"], str(int(kg * price)), "0", str(int(kg)), "090111", month])
    return rows


def meteo(lat, days=14, start=None):
    rnd = random.Random(int(lat * 100))
    if start:
        d0 = date.fromisoformat(start)
        n = days
    else:
        d0, n = date.today() - timedelta(days=days), days + 1
    t = [(d0 + timedelta(days=i)).isoformat() for i in range(n)]
    return {"daily": {"time": t,
                      "precipitation_sum": [round(max(0, rnd.gauss(4 + 4 * math.sin(i / 58), 6)), 1) for i in range(n)],
                      "temperature_2m_min": [round(13 + 3 * math.sin(i / 58) + rnd.gauss(0, 1), 1) for i in range(n)],
                      "temperature_2m_max": [round(26 + 3 * math.sin(i / 58) + rnd.gauss(0, 1.5), 1) for i in range(n)]},
            "current": {"temperature_2m": 22.0, "relative_humidity_2m": 75, "precipitation": 0}}


def mock_transport(fail: set[str] = frozenset()):
    global NOW
    NOW = time.time()  # timestamps are relative to when the demo is (re)seeded
    from app import config
    trade_by_feed = {}
    for i, (t, d) in enumerate(TRADE):
        f = config.RSS_FEEDS[i % 6]
        trade_by_feed.setdefault(f["url"], []).append((t, f"https://{f['id']}.example/{i}", d, NOW - i * 5400))

    def handler(req: httpx.Request) -> httpx.Response:
        url, host = str(req.url), req.url.host
        if any(f in url for f in fail):
            return httpx.Response(403, text="blocked")
        if host == "news.google.com":
            ceid = req.url.params.get("ceid", "")
            q = req.url.params.get("q", "")
            items = []
            for oid, heads in LOCAL.items():
                o = config.ORIGIN_BY_ID[oid]
                if o["news"]["ceid"] == ceid and ceid != "US:en" and o["news"]["q"].split(" when:")[0] in q:
                    items += [(h, p, NOW - (k + 1) * 7200) for k, (h, p) in enumerate(heads)]
                elif ceid in ("US:en", "KE:en") and o["country"] in q and oid in ("ke", "et", "ug", "rw"):
                    items += [(h, p, NOW - (k + 1) * 7200) for k, (h, p) in enumerate(heads)]
            if ceid == "CR:es-419" or "Costa Rica" in q:
                items += [(h, p, NOW - (k + 1) * 6000) for k, (h, p) in enumerate(LOCAL["cr"])]
                if "Cup of Excellence" in q:
                    items.append(("Costa Rica Cup of Excellence winner from West Valley micro mill fetches record",
                                  "Daily Coffee News", NOW - 20000))
            if "arabica OR robusta" in q:
                items += [("Coffee futures slump as Brazil rains ease supply worries", "Barchart", NOW - 1800),
                          ("Arabica coffee climbs to 2-week high on tight ICE stocks", "Nasdaq", NOW - 9000)]
            if "site:stonex.com" in q:
                items += [("ICE Coffee Warehouse Stocks Down 4,550 Bags", "StoneX", NOW - 4000)]
            return httpx.Response(200, text=gnews_rss(items))
        if host == "api.gdeltproject.org":
            return httpx.Response(200, json=gdelt())
        if host == "publicreporting.cftc.gov":
            return httpx.Response(200, json=cot_rows())
        if host == "fred.stlouisfed.org":
            return httpx.Response(200, text=fred_csv(240 if "OTM" in url else 110))
        if host == "www.cpc.ncep.noaa.gov":
            return httpx.Response(200, text=oni_txt())
        if host == "api.census.gov":
            return httpx.Response(200, json=census_rows())
        if host == "archive-api.open-meteo.com":
            p = req.url.params
            n = (date.fromisoformat(p["end_date"]) - date.fromisoformat(p["start_date"])).days + 1
            return httpx.Response(200, json=meteo(float(p["latitude"]), n, p["start_date"]))
        if host == "api.open-meteo.com":
            return httpx.Response(200, json=meteo(float(req.url.params["latitude"])))
        if url in trade_by_feed:
            f = next(f for f in config.RSS_FEEDS if f["url"] == url)
            return httpx.Response(200, text=wordpress_rss(f["name"], trade_by_feed[url]))
        for f in config.RSS_FEEDS:
            if f["url"] == url:
                return httpx.Response(200, text="<html>Access denied</html>")
        return httpx.Response(404, text="not mocked: " + url)

    return httpx.MockTransport(handler)
