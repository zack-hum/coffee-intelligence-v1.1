"""Archive storage.

Two backends with the same interface:
  * SQLiteStore   - local dev / tests / a single small VM (full-text search via FTS5)
  * FirestoreStore - production on Cloud Run (free tier covers personal use)

Choose with STORE=sqlite|firestore (default: sqlite locally, firestore when
K_SERVICE is set, i.e. on Cloud Run).
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
from collections.abc import Iterable

WORD = re.compile(r"[\w'-]{3,}", re.UNICODE)
STOP = set("""the and for with from that this are was were has have its into over after
about will more than their they which been also but not new said says could would
de la el los las del en por con para que una uno des les sur dans pour une est
do da dos das em com uma não que""".split())


def tokens(text: str) -> list[str]:
    seen, out = set(), []
    for w in WORD.findall((text or "").lower()):
        if w not in STOP and w not in seen:
            seen.add(w)
            out.append(w)
    return out[:80]


class Store:
    # articles
    def upsert_articles(self, items: Iterable[dict]) -> int: ...
    def query_articles(self, *, q=None, origin=None, topic=None, signal=None, channel=None,
                       lang=None, before=None, since=None, limit=50) -> list[dict]: ...
    def article_counts(self, since: float) -> dict: ...
    # series
    def put_series(self, sid: str, points: dict[str, float], meta: dict | None = None) -> int: ...
    def get_series(self, sid: str) -> dict: ...
    def list_series(self, prefix: str = "") -> list[dict]: ...
    # source health
    def record_run(self, source_id: str, **info) -> None: ...
    def runs(self) -> list[dict]: ...


def _match(a: dict, *, q, origin, topic, signal, channel, lang, before, since) -> bool:
    if origin and origin not in a.get("origins", []):
        return False
    if topic and topic not in a.get("topics", []):
        return False
    if signal and a.get("signal") != signal:
        return False
    if channel and a.get("channel") != channel:
        return False
    if lang and a.get("lang") != lang:
        return False
    if before and a.get("published", 0) >= before:
        return False
    if since and a.get("published", 0) < since:
        return False
    if q:
        hay = f"{a.get('title', '')} {a.get('summary', '')} {a.get('source_name', '')}".lower()
        if not all(t in hay for t in q.lower().split()):
            return False
    return True


# ===================================================================== SQLite

class SQLiteStore(Store):
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS articles(
          id TEXT PRIMARY KEY, url TEXT, title TEXT, summary TEXT, source_id TEXT,
          source_name TEXT, channel TEXT, lang TEXT, published REAL, fetched REAL,
          origins TEXT, topics TEXT, signal TEXT, score INTEGER);
        CREATE INDEX IF NOT EXISTS ix_pub ON articles(published DESC);
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(id UNINDEXED, title, summary);
        CREATE TABLE IF NOT EXISTS series(sid TEXT PRIMARY KEY, meta TEXT, points TEXT, updated REAL);
        CREATE TABLE IF NOT EXISTS runs(source_id TEXT PRIMARY KEY, info TEXT);
        """)

    def upsert_articles(self, items):
        new = 0
        with self._lock:
            for a in items:
                cur = self.db.execute("SELECT 1 FROM articles WHERE id=?", (a["id"],))
                if cur.fetchone():
                    continue
                self.db.execute(
                    "INSERT INTO articles VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (a["id"], a["url"], a["title"], a.get("summary", ""), a["source_id"],
                     a["source_name"], a["channel"], a.get("lang", "en"), a["published"],
                     a["fetched"], "," + ",".join(a.get("origins", [])) + ",",
                     "," + ",".join(a.get("topics", [])) + ",", a.get("signal", "neutral"),
                     a.get("score", 0)))
                self.db.execute("INSERT INTO articles_fts VALUES(?,?,?)",
                                (a["id"], a["title"], a.get("summary", "")))
                new += 1
            self.db.commit()
        return new

    def _row(self, r) -> dict:
        d = dict(r)
        d["origins"] = [x for x in d["origins"].split(",") if x]
        d["topics"] = [x for x in d["topics"].split(",") if x]
        return d

    def query_articles(self, *, q=None, origin=None, topic=None, signal=None, channel=None,
                       lang=None, before=None, since=None, limit=50):
        where, args = [], []
        if q:
            fts = " ".join(f'"{t}"' for t in re.findall(r"\w+", q))
            if fts:
                where.append("id IN (SELECT id FROM articles_fts WHERE articles_fts MATCH ?)")
                args.append(fts)
        for col, val in (("origins", origin), ("topics", topic)):
            if val:
                where.append(f"{col} LIKE ?")
                args.append(f"%,{val},%")
        for col, val in (("signal", signal), ("channel", channel), ("lang", lang)):
            if val:
                where.append(f"{col}=?")
                args.append(val)
        if before:
            where.append("published < ?")
            args.append(before)
        if since:
            where.append("published >= ?")
            args.append(since)
        sql = "SELECT * FROM articles" + (" WHERE " + " AND ".join(where) if where else "")
        sql += " ORDER BY published DESC LIMIT ?"
        args.append(int(limit))
        with self._lock:
            return [self._row(r) for r in self.db.execute(sql, args).fetchall()]

    def article_counts(self, since):
        with self._lock:
            rows = self.db.execute(
                "SELECT origins, topics, signal FROM articles WHERE published >= ?", (since,)).fetchall()
        return _count([self._row({"origins": r[0], "topics": r[1], "signal": r[2]}) for r in rows])

    def put_series(self, sid, points, meta=None):
        with self._lock:
            row = self.db.execute("SELECT meta, points FROM series WHERE sid=?", (sid,)).fetchone()
            cur_pts = json.loads(row["points"]) if row else {}
            cur_meta = json.loads(row["meta"]) if row else {}
            cur_pts.update({k: v for k, v in points.items() if v is not None})
            cur_meta.update(meta or {})
            self.db.execute("INSERT OR REPLACE INTO series VALUES(?,?,?,?)",
                            (sid, json.dumps(cur_meta), json.dumps(cur_pts), time.time()))
            self.db.commit()
        return len(points)

    def get_series(self, sid):
        with self._lock:
            row = self.db.execute("SELECT meta, points, updated FROM series WHERE sid=?", (sid,)).fetchone()
        if not row:
            return {"sid": sid, "meta": {}, "points": []}
        pts = json.loads(row["points"])
        return {"sid": sid, "meta": json.loads(row["meta"]), "updated": row["updated"],
                "points": [[k, pts[k]] for k in sorted(pts)]}

    def list_series(self, prefix=""):
        with self._lock:
            rows = self.db.execute("SELECT sid, meta, updated FROM series WHERE sid LIKE ?",
                                   (prefix + "%",)).fetchall()
        return [{"sid": r["sid"], "meta": json.loads(r["meta"]), "updated": r["updated"]} for r in rows]

    def record_run(self, source_id, **info):
        with self._lock:
            self.db.execute("INSERT OR REPLACE INTO runs VALUES(?,?)",
                            (source_id, json.dumps({**info, "source_id": source_id})))
            self.db.commit()

    def runs(self):
        with self._lock:
            return [json.loads(r[0]) for r in self.db.execute("SELECT info FROM runs").fetchall()]

    # local-only helpers (Dev panel)
    def reset(self):
        with self._lock:
            self.db.executescript("DELETE FROM articles; DELETE FROM articles_fts; DELETE FROM series; DELETE FROM runs;")
            self.db.commit()

    def stats(self) -> dict:
        with self._lock:
            n = self.db.execute("SELECT COUNT(*), MIN(published), MAX(published) FROM articles").fetchone()
            s = self.db.execute("SELECT COUNT(*) FROM series").fetchone()[0]
        size = os.path.getsize(self.path) if os.path.exists(self.path) else 0
        return {"backend": "sqlite", "path": self.path, "articles": n[0], "oldest": n[1], "newest": n[2],
                "series": s, "bytes": size}


def _count(rows: list[dict]) -> dict:
    out = {"total": len(rows), "origins": {}, "topics": {}, "signal": {}}
    for a in rows:
        for o in a["origins"]:
            out["origins"][o] = out["origins"].get(o, 0) + 1
        for t in a["topics"]:
            out["topics"][t] = out["topics"].get(t, 0) + 1
        s = a.get("signal") or "neutral"
        out["signal"][s] = out["signal"].get(s, 0) + 1
    return out


# ================================================================== Firestore

class FirestoreStore(Store):
    """Collections: articles/{id}, series/{sid}, runs/{source_id}.

    Firestore can only use one array-contains filter per query, so the most
    selective filter goes to Firestore and the rest are applied in Python.
    deploy.sh creates the composite indexes these queries need."""

    SEEN_MAX = 8000  # ~160 KB of IDs, well under the 1 MiB document limit

    def __init__(self, project: str | None = None, database: str = "(default)"):
        from google.cloud import firestore  # imported lazily so dev doesn't need it
        self.fs = firestore
        self.db = firestore.Client(project=project, database=database)

    def upsert_articles(self, items):
        items = list(items)
        if not items:
            return 0
        col = self.db.collection("articles")
        # Dedupe against a rolling list of recent IDs kept in one document:
        # 1 read per ingest run instead of one read per fetched item, which
        # keeps a 15-minute news cycle inside Firestore's free tier.
        seen_ref = self.db.collection("meta").document("seen_ids")
        snap = seen_ref.get()
        seen = snap.to_dict().get("ids", []) if snap.exists else []
        seen_set = set(seen)
        fresh = [a for a in items if a["id"] not in seen_set]
        fresh = list({a["id"]: a for a in fresh}.values())
        if not fresh:
            return 0
        # Older articles that fell off the rolling list: confirm with a direct read.
        existing = {s.id for s in self.db.get_all([col.document(a["id"]) for a in fresh]
                                                  if len(seen) >= self.SEEN_MAX else []) if s.exists}
        batch, n, new = self.db.batch(), 0, 0
        for a in fresh:
            if a["id"] in existing:
                continue
            doc = {**a, "tokens": tokens(a["title"] + " " + a.get("summary", ""))}
            batch.set(col.document(a["id"]), doc)
            n += 1
            new += 1
            if n == 400:
                batch.commit()
                batch, n = self.db.batch(), 0
        if n:
            batch.commit()
        seen_ref.set({"ids": (seen + [a["id"] for a in fresh])[-self.SEEN_MAX:]})
        return new

    def query_articles(self, *, q=None, origin=None, topic=None, signal=None, channel=None,
                       lang=None, before=None, since=None, limit=50):
        F = self.fs.FieldFilter
        query = self.db.collection("articles")
        q_tokens = tokens(q) if q else []
        used = None
        if q_tokens:
            query, used = query.where(filter=F("tokens", "array_contains", q_tokens[0])), "q"
        elif origin:
            query, used = query.where(filter=F("origins", "array_contains", origin)), "origin"
        elif topic:
            query, used = query.where(filter=F("topics", "array_contains", topic)), "topic"
        if before:
            query = query.where(filter=F("published", "<", before))
        query = query.order_by("published", direction=self.fs.Query.DESCENDING)
        # Over-fetch only when some criteria still have to be applied in Python
        # (each document read counts against the free tier).
        leftover = any([q and (used != "q" or len(q_tokens) > 1), origin and used != "origin",
                        topic and used != "topic", signal, channel, lang, since])
        fetch = min(limit * 4, 200) if leftover else limit
        out = []
        for snap in query.limit(fetch).stream():
            a = snap.to_dict()
            a.pop("tokens", None)
            if _match(a, q=q, origin=origin, topic=topic, signal=signal, channel=channel,
                      lang=lang, before=before, since=since):
                out.append(a)
                if len(out) >= limit:
                    break
        return out

    def article_counts(self, since):
        F = self.fs.FieldFilter
        snaps = (self.db.collection("articles").where(filter=F("published", ">=", since))
                 .select(["origins", "topics", "signal"]).stream())
        return _count([s.to_dict() for s in snaps])

    def put_series(self, sid, points, meta=None):
        ref = self.db.collection("series").document(sid.replace("/", "_"))
        snap = ref.get()
        cur = snap.to_dict() if snap.exists else {"sid": sid, "meta": {}, "points": {}}
        cur["points"].update({k: v for k, v in points.items() if v is not None})
        cur["meta"].update(meta or {})
        cur["updated"] = time.time()
        ref.set(cur)
        return len(points)

    def get_series(self, sid):
        snap = self.db.collection("series").document(sid.replace("/", "_")).get()
        if not snap.exists:
            return {"sid": sid, "meta": {}, "points": []}
        d = snap.to_dict()
        pts = d.get("points", {})
        return {"sid": sid, "meta": d.get("meta", {}), "updated": d.get("updated"),
                "points": [[k, pts[k]] for k in sorted(pts)]}

    def list_series(self, prefix=""):
        out = []
        for s in self.db.collection("series").select(["sid", "meta", "updated"]).stream():
            d = s.to_dict()
            if d.get("sid", "").startswith(prefix):
                out.append({"sid": d["sid"], "meta": d.get("meta", {}), "updated": d.get("updated")})
        return out

    def record_run(self, source_id, **info):
        self.db.collection("runs").document(source_id).set({**info, "source_id": source_id})

    def runs(self):
        return [s.to_dict() for s in self.db.collection("runs").stream()]


# ==================================================================== factory

_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        kind = os.getenv("STORE") or ("firestore" if os.getenv("K_SERVICE") else "sqlite")
        if kind == "firestore":
            _store = FirestoreStore(project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                                    database=os.getenv("FIRESTORE_DB", "(default)"))
        else:
            _store = SQLiteStore(os.getenv("SQLITE_PATH", "coffee.db"))
    return _store
