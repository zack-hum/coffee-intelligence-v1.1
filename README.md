# Coffee Origin Monitor

[![CI](https://github.com/<owner>/coffee-intelligence-v1.1/actions/workflows/ci.yml/badge.svg)](https://github.com/<owner>/coffee-intelligence-v1.1/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

Open-source market and origin intelligence for specialty coffee. It brings together live arabica futures and origin currencies, a multilingual archive of coffee news, supply and trade datasets, and growing-region weather for 18 producing countries, all from free sources. **Costa Rica** has a featured page for sourcing-trip planning.

It's built for people who buy and sell green coffee: roasters, importers, green buyers and cafés. It runs on a laptop in a minute, with no API keys needed to try it.

## Features

- **Market:** delayed ICE arabica "C" futures, US dollar index, USD/BRL and 16 origin currencies, with intraday to 5-year charts.
- **News archive:** about 65 sources (publisher RSS, Google News and GDELT) in English, Spanish, Portuguese, Vietnamese, Indonesian and French. De-duplicated and tagged by origin, topic and likely price direction, with full-text search and filters.
- **Origins:** 18 origin pages with the implied local price from your own differential, exchange rate, current and forecast weather, a year of rainfall, US import volumes and prices, and origin news.
- **Costa Rica:** all 8 ICAFE regions with harvest calendars, weather, 16-day rain forecasts, regional news, a trip planner and a price calculator (USD/lb, ₡/kg, ₡ per quintal).
- **Data:** CFTC speculator positioning, IMF monthly arabica and robusta prices, ENSO (El Niño/La Niña), US Census imports by origin, and USDA supply and demand (optional key).
- **Source health:** a Sources page showing the last run, item count and error for every feed and dataset.

## Quick start

You need **Python 3.10 or newer** (`python --version`). On Windows, install it from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH**.

```bash
git clone https://github.com/<owner>/coffee-intelligence-v1.1.git
cd coffee-intelligence-v1.1
```

| | Windows | macOS / Linux |
|---|---|---|
| Demo mode: offline, synthetic data | `dev.bat` | `./dev.sh` |
| Live mode: real sources | `dev.bat live` | `./dev.sh live` |
| Run tests | `dev.bat test` | `./dev.sh test` |
| Delete local archives | `dev.bat reset` | `./dev.sh reset` |
| Production container (needs Docker) | | `./dev.sh docker` |

Then open http://localhost:8080. In PowerShell, type `.\dev.bat`. If `./dev.sh` reports "permission denied", run `bash dev.sh` or `chmod +x dev.sh`.

The first run creates a `.venv`, installs dependencies (about a minute) and copies `.env.example` to `.env`. Stop the server with **Ctrl+C**. To use another port: `PORT=9000 ./dev.sh` or `set PORT=9000 && dev.bat`.

### Modes

| | demo | live | cloud |
|---|---|---|---|
| Prices | Synthetic, moving minute to minute | Yahoo (delayed) | Yahoo (delayed) |
| News | Fixture archive, plus a new demo headline every 45 s | All real sources, every 15 min | Same, triggered by Cloud Scheduler |
| Datasets | Fixtures | Real, every 6 h | Real, daily; prices and weather every 3 h |
| Archive | `data/demo.db` (SQLite) | `data/live.db` (SQLite) | Firestore |
| Internet needed | No | Yes | Yes |
| Dev page | Yes | Yes | Off |

Each mode keeps its own archive, so demo and real data never mix.

## Configuration

Settings come from environment variables, falling back to `.env`. Command-line and real environment variables always win.

| Variable | Default | Purpose |
|---|---|---|
| `APP_MODE` | `demo` locally, `cloud` on Cloud Run | `demo`, `live` or `cloud` |
| `CENSUS_API_KEY` | none | **Needed for US imports data.** Free: https://api.census.gov/data/key_signup.html |
| `FAS_API_KEY` | none | Enables USDA supply and demand data. Free: https://apps.fas.usda.gov/opendatawebv2/#/signup |
| `DASH_PASSWORD` | none | Requires HTTP basic auth (any username) for the whole app. Always set it on a public server. |
| `NEWS_EVERY` / `DATA_EVERY` | `900` / `21600` | Live-mode ingestion intervals, in seconds |
| `DEMO_DRIP_SECONDS` | `45` | Seconds between new demo headlines |
| `DEV_TOOLS` | on locally, off in cloud | Shows the Dev page (`#/dev`) |
| `ARABICA_SYMBOLS` | `KC=F` | Yahoo symbols to try for arabica, comma-separated |
| `QUOTE_TTL` / `WEATHER_TTL` | `60` / `1800` | Cache lifetimes, in seconds |
| `PORT` | `8080` | Local server port |

Without keys, everything except US imports and USDA data works.

## Project layout

```
app/
  main.py          FastAPI app: API endpoints, auth, in-process ingestion loop
  config.py        Origins, Costa Rica regions, feeds, queries, dataset settings
  tagging.py       Keyword tagging: coffee relevance, origins, topics, price signal
  sources.py       Live fetchers (Yahoo, FX fallback, Open-Meteo) with a TTL cache
  store.py         Archive storage: SQLite (local) and Firestore (cloud)
  settings.py      Run modes and .env loading
  dev.py           Dev page API (local only)
  ingest/          News and dataset ingestion jobs
  demo/            Offline fixtures and the demo headline generator
  static/          Single-page frontend (vanilla JS, no build step)
tests/             Offline tests (pytest)
deploy.sh          One-command Google Cloud deployment
```

The server reloads when you save a file under `app/`; refresh the browser to see the change. The Dev page has on-demand ingestion, a tagging playground that shows which keywords fired for any headline, and a feed tester for previewing an RSS feed before adding it to `app/config.py`.

## Data sources and terms of use

| Data | Source | Frequency | Key |
|---|---|---|---|
| Arabica futures, DXY, origin currencies | Yahoo Finance chart API (unofficial) | Live, delayed; daily closes archived | No |
| FX fallback | open.er-api.com | Daily | No |
| Weather and forecasts | Open-Meteo forecast and archive APIs | Every 3 h | No |
| Commitments of Traders, Coffee C | CFTC public reporting API | Weekly | No |
| IMF arabica (Other Milds) and robusta prices | FRED | Monthly | No |
| ENSO / Oceanic Niño Index | NOAA Climate Prediction Center | Monthly | No |
| US green coffee imports by origin (HS 090111) | US Census international trade API | Monthly | Yes |
| Production, exports, stocks by country | USDA FAS PSD API | Monthly | Yes |
| News | Publisher RSS, Google News RSS, GDELT DOC 2.0 | Every 15 min | No |

**Publisher RSS:** Daily Coffee News, Sprudge, Barista Magazine, Coffee Review, Tea & Coffee Trade Journal, Fresh Cup.

**Google News:** global market, crop, policy, logistics and industry topics; a local-language and an English query for each origin; and Costa Rica queries. Outlets that block automated feed access (Perfect Daily Grind, Comunicaffe, European Coffee Trip, The Tico Times, Global Coffee Report, World Coffee Portal, Barchart and others) are reached through Google News `site:` queries instead.

**Please respect the sources.** Data belongs to its providers and their terms apply to your use of it, not this project's MIT license. Yahoo Finance and Google News RSS are unofficial endpoints with no service guarantee, so use them for personal research, not redistribution. Only headlines and short excerpts (up to 280 characters) are stored, and every item links back to the publisher. Keep request rates modest; the defaults follow GDELT's guidance of one request per 5 seconds.

### Tagging

Each story is checked for coffee relevance, then tagged with origins and Costa Rica regions (using local-language place names), one or more of 13 topics, and a **bullish/bearish signal** from supply and price keywords such as frost, drought, bumper crop and plunge. The signal is a heuristic for triage only. All keyword lists are in `app/tagging.py`.

## Deploy to Google Cloud

Requirements: a Google Cloud project with billing enabled, and the `gcloud` CLI signed in.

```bash
PROJECT_ID=your-project DASH_PASSWORD='choose-a-password' \
  CENSUS_API_KEY=... FAS_API_KEY=... ./deploy.sh
```

The script is safe to re-run. It:
1. enables the APIs and creates Firestore with its indexes;
2. stores the password and a generated ingestion token in Secret Manager;
3. deploys Cloud Run;
4. schedules ingestion with Cloud Scheduler: news every 15 minutes, datasets daily, prices and weather every 3 hours;
5. starts the first run.

For personal use it is expected to stay in or near the free tiers. Cloud Run scales to zero, and Firestore reads are kept low by deduplicating against one list of recent IDs and caching news stats. If you go over, change the news schedule to `*/30` in `deploy.sh`.

## Known limitations

- **No live robusta price.** Yahoo delisted ICE London robusta and there is no free alternative, so robusta appears only as the IMF monthly price, and Uganda and Vietnam show no implied price.
- **Unofficial endpoints can rate-limit or change.** Check the Sources page after a live run.
- **GDELT only searches the last 3 months.** The archive keeps everything from when ingestion starts.
- **Costa Rica harvest windows and region coordinates are approximate.** Timing shifts with altitude and year.
- **Not investment advice.** Prices are delayed and signals are keyword heuristics.

## Roadmap

Ideas under consideration: landed-cost calculator, producer and cupping log, origin crop-risk scores, a daily brief, and more origin price indicators (Colombia FNC, CEPEA, Cecafé, ICO). Suggestions are welcome; open an issue.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests and the rules for adding data sources, and the [Code of Conduct](CODE_OF_CONDUCT.md). Report security issues privately as described in [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE). Bundled third-party components are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
