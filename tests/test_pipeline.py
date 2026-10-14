import asyncio
import os

os.environ.setdefault("MOCK", "1")  # market closes job uses synthetic Yahoo bars

from app import config  # noqa: E402
from app.demo import fixtures as fx  # noqa: E402
from app.ingest import common  # noqa: E402
from app.ingest.data import parse_census, parse_cot, parse_fred_csv, parse_oni, run_data  # noqa: E402
from app.ingest.news import parse_gdelt, parse_gnews, parse_rss, run_news  # noqa: E402
from app.store import SQLiteStore  # noqa: E402
from app.tagging import is_coffee, tag  # noqa: E402


def test_tagging_origins_topics_signal():
    t = tag("Geada atinge lavouras de café no Sul de Minas, preço dispara")
    assert "br" in t["origins"] and "weather" in t["topics"] and t["signal"] == "bullish"
    t = tag("Peru coffee farmers in Jaén report bumper crop, prices drop")
    assert t["origins"] == ["pe"] and t["signal"] == "bearish" and "crop" in t["topics"]
    t = tag("Giá cà phê hôm nay tăng mạnh tại Đắk Lắk")
    assert "vn" in t["origins"] and t["signal"] == "bullish"
    t = tag("EU confirms EUDR compliance timeline for coffee importers")
    assert "policy" in t["topics"]
    t = tag("Productores de Naranjo inician cosecha de café", hint_origins=["cr"])
    assert "cr.westvalley" in t["origins"] and "crop" in t["topics"]
    assert is_coffee("Kopi Gayo") and not is_coffee("Bitcoin rallies on ETF news")


def test_parsers():
    feed = {"id": "x", "name": "X", "kind": "trade"}
    items = parse_rss(fx.wordpress_rss("X", [("Arabica rallies", "https://x/1", "<b>hi</b>", fx.NOW)]).encode(), feed)
    assert items[0]["summary"] == "hi" and items[0]["channel"] == "rss"
    g = parse_gnews(fx.gnews_rss([("Coffee prices slump", "Reuters", fx.NOW),
                                  ("Bitcoin up", "CNBC", fx.NOW)]).encode(), {"id": "g", "name": "G"}, "en")
    assert len(g) == 1 and g[0]["source_name"] == "Reuters" and g[0]["title"] == "Coffee prices slump"
    d = parse_gdelt(fx.gdelt(), {"id": "gd", "name": "GD"})
    assert {a["lang"] for a in d} == {"en", "pt", "es", "vi"}
    cot = parse_cot(fx.cot_rows(5))
    assert len(cot["mm_net"]) == 5 and all(abs(v) < 500000 for v in cot["mm_long"].values())
    assert len(parse_fred_csv("observation_date,X\n2024-01-01,200.5\n2024-02-01,.\n")) == 1
    oni = parse_oni(fx.oni_txt())
    assert "2016-01-01" in oni
    cen = parse_census(fx.census_rows())
    assert "br" in cen and "total" in cen and cen["br"]["kg"]


def test_full_ingest(tmp_path, monkeypatch):
    common.TRANSPORT = fx.mock_transport()
    monkeypatch.setattr(config, "CENSUS_KEY", "test")
    store = SQLiteStore(str(tmp_path / "t.db"))
    r = asyncio.run(run_news(store, include_gdelt=True))
    assert r["new"] > 20
    again = asyncio.run(run_news(store, include_gdelt=False))
    assert again["new"] == 0  # dedupe
    runs = {x["source_id"]: x for x in store.runs()}
    assert all(runs[f"rss:{f['id']}"]["ok"] for f in config.RSS_FEEDS)
    assert store.query_articles(origin="br", limit=50)
    assert store.query_articles(q="rust", limit=5)
    d = asyncio.run(run_data(store))
    assert d["jobs"]["cot"] and d["jobs"]["census"] and d["jobs"]["weather"] == 18 + 8
    assert store.query_articles(origin="cr.brunca", limit=5)  # Pérez Zeledón / Coto Brus story
    assert len(store.get_series("wx:cr.tarrazu:rain")["points"]) > 300
    assert d["jobs"]["psd"] == 0  # no key -> skipped, recorded as not ok
    assert len(store.get_series("wx:br:rain")["points"]) > 300
    assert store.get_series("cot:mm_net")["points"]
