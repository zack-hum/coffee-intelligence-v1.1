"""Run modes and .env loading.

APP_MODE decides how the whole app behaves:

  demo   Offline. Synthetic prices that tick, a fixture news archive seeded on
         first start, and a new demo headline every DEMO_DRIP_SECONDS.
         Nothing leaves your machine. Default when running locally.
  live   Real data from every free source, archived to a local SQLite file,
         with ingestion running inside the server (news every 15 min,
         datasets every 6 h). Use this to test feeds before deploying.
  cloud  Production on Cloud Run: Firestore archive, ingestion triggered by
         Cloud Scheduler, Dev tools off. Chosen automatically on Cloud Run.

Values come from the real environment first, then a `.env` file in the
project root (copy .env.example). No extra dependency needed.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:  # real env always wins
            os.environ[key] = val


_load_dotenv(ROOT / ".env")

ON_CLOUD_RUN = bool(os.getenv("K_SERVICE"))
APP_MODE = (os.getenv("APP_MODE") or ("cloud" if ON_CLOUD_RUN else "demo")).lower()
if APP_MODE not in ("demo", "live", "cloud"):
    raise SystemExit(f"APP_MODE must be demo, live or cloud (got {APP_MODE!r})")

DATA_DIR = ROOT / "data"

if APP_MODE == "demo":
    os.environ.setdefault("MOCK", "1")
    os.environ.setdefault("STORE", "sqlite")
    os.environ.setdefault("SQLITE_PATH", str(DATA_DIR / "demo.db"))
    os.environ.setdefault("GDELT_DELAY", "0")
elif APP_MODE == "live":
    os.environ.setdefault("STORE", "sqlite")
    os.environ.setdefault("SQLITE_PATH", str(DATA_DIR / "live.db"))
else:
    os.environ.setdefault("STORE", "firestore")

if os.getenv("STORE") == "sqlite":
    Path(os.environ["SQLITE_PATH"]).parent.mkdir(parents=True, exist_ok=True)

# In-process ingestion (cloud uses Cloud Scheduler instead).
BG_INGEST = os.getenv("BG_INGEST", "0" if APP_MODE == "cloud" else "1") == "1"
NEWS_EVERY = int(os.getenv("NEWS_EVERY", "900"))
DATA_EVERY = int(os.getenv("DATA_EVERY", str(6 * 3600)))
DEMO_DRIP_SECONDS = int(os.getenv("DEMO_DRIP_SECONDS", "45"))

# Dev panel (#/dev): on locally, off in the cloud unless explicitly enabled.
DEV_TOOLS = os.getenv("DEV_TOOLS", "0" if APP_MODE == "cloud" else "1") == "1"
