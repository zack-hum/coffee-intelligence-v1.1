"""Exercise FirestoreStore against the `mock-firestore` fake (pip install mock-firestore).

The fake predates FieldFilter/batch/select, so a thin shim adapts it. Skipped
when the fake isn't installed."""

import asyncio
import types

import pytest

mf = pytest.importorskip("mockfirestore")

from app.demo import fixtures as fx  # noqa: E402
from app.ingest import common  # noqa: E402
from app.ingest.news import run_news  # noqa: E402
from app.store import FirestoreStore  # noqa: E402


def _shim():
    from mockfirestore.collection import CollectionReference
    from mockfirestore.query import Query

    for cls in (CollectionReference, Query):
        orig = cls.where

        def where(self, *args, filter=None, _orig=orig):  # noqa: A002
            return _orig(self, *(filter if filter else args))
        cls.where = where
        cls.select = lambda self, fields: self

    class Batch:
        def __init__(self):
            self.ops = []

        def set(self, ref, data):
            self.ops.append((ref, data))

        def commit(self):
            for ref, data in self.ops:
                ref.set(data)
    client = mf.MockFirestore()
    client.batch = Batch
    fs = types.SimpleNamespace(FieldFilter=lambda f, op, v: (f, op, v),
                               Query=types.SimpleNamespace(DESCENDING="DESCENDING"))
    st = FirestoreStore.__new__(FirestoreStore)
    st.db, st.fs = client, fs
    return st


def test_firestore_roundtrip(monkeypatch):
    monkeypatch.setenv("GDELT_DELAY", "0")
    common.TRANSPORT = fx.mock_transport()
    st = _shim()
    first = asyncio.run(run_news(st, include_gdelt=False))
    assert first["new"] > 20
    assert asyncio.run(run_news(st, include_gdelt=False))["new"] == 0
    assert len(st.db.collection("meta").document("seen_ids").get().to_dict()["ids"]) == first["new"]
    br = st.query_articles(origin="br", limit=10)
    assert br and all("br" in a["origins"] for a in br)
    assert [a["published"] for a in br] == sorted([a["published"] for a in br], reverse=True)
    assert st.query_articles(q="roya", limit=5)
    assert all(a["signal"] == "bullish" for a in st.query_articles(origin="br", signal="bullish", limit=5))
    assert st.query_articles(origin="cr.brunca", limit=5)
    st.put_series("cot:mm_net", {"2026-01-06": 1.0}, {"name": "x"})
    st.put_series("cot:mm_net", {"2026-01-13": 2.0})
    assert st.get_series("cot:mm_net")["points"] == [["2026-01-06", 1.0], ["2026-01-13", 2.0]]
    assert st.list_series("cot:")[0]["sid"] == "cot:mm_net"
    assert any(r["ok"] for r in st.runs())
