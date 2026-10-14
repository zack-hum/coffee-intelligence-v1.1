# Third-party notices

This project's own code is MIT-licensed (see [LICENSE](LICENSE)). It includes or loads the following third-party components under their own licenses.

## Bundled

### TradingView Lightweight Charts v4.2.0

- File: `app/static/lightweight-charts.standalone.production.js` (unmodified)
- Copyright (c) 2024 TradingView, Inc.
- License: Apache License 2.0, https://www.apache.org/licenses/LICENSE-2.0
- Source: https://github.com/tradingview/lightweight-charts

The library's license requires attribution to TradingView. The charts keep the default TradingView attribution logo; leave it enabled (`layout.attributionLogo`) or otherwise credit TradingView with a link to https://www.tradingview.com/ if you change it.

## Loaded at runtime

- **Fonts:** IBM Plex Mono, Fraunces and Inter from Google Fonts, under the SIL Open Font License 1.1.

## Python dependencies

Installed from PyPI, not redistributed in this repository. See `requirements.txt` and `requirements-local.txt`. Main ones: FastAPI (MIT), Uvicorn (BSD-3-Clause), HTTPX (BSD-3-Clause), feedparser (BSD-2-Clause), tzdata (Apache-2.0), google-cloud-firestore (Apache-2.0).

## Data sources

The data this application fetches belongs to its providers and is subject to their terms, not to this project's license. See "Data sources and terms of use" in the README.
