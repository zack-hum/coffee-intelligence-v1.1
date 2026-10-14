# Contributing

Thanks for helping improve Coffee Origin Monitor. Bug reports, new data sources, new origins, tagging fixes and UI improvements are all welcome.

## Getting set up

You need Python 3.10 or newer and Git.

```bash
git clone https://github.com/<owner>/coffee-intelligence-v1.1.git
cd coffee-intelligence-v1.1
./dev.sh          # macOS / Linux (Windows: dev.bat)
```

The first run creates `.venv`, installs `requirements-local.txt` and copies `.env.example` to `.env`. Demo mode runs fully offline, so you can work on almost everything without API keys or internet access. Use `./dev.sh live` (or `dev.bat live`) when you need real sources.

## Before you open a pull request

```bash
./dev.sh test                          # or: dev.bat test
.venv/bin/ruff check app tests         # Windows: .venv\Scripts\ruff check app tests
.venv/bin/ruff check app tests --fix   # applies safe fixes
```

CI runs the same lint and tests on Python 3.10 to 3.12 (Linux) and 3.12 (Windows), and checks that the Docker image builds.

Please:

- **Keep pull requests focused.** One feature or fix per PR is easier to review.
- **Match the existing style.** Plain Python and vanilla JavaScript; no build step for the frontend.
- **Add or update tests** in `tests/` for parsers, tagging and ingestion changes. Tests must run offline: use the fixtures in `app/demo/fixtures.py` and the mock HTTP transport rather than real network calls.
- **Update the README** if you change setup, configuration or data sources, and add a line to `CHANGELOG.md` under "Unreleased".

## Common contributions

| Change | Where |
|---|---|
| Add an origin, feed, Google News or GDELT query | `app/config.py` |
| Improve tagging (origins, topics, bullish/bearish keywords) | `app/tagging.py`; try it in the Dev page's tagging playground |
| Add a dataset | a `job_*` function plus an entry in `JOBS` in `app/ingest/data.py`, and a fixture in `app/demo/fixtures.py` so demo mode and tests cover it |
| UI | `app/static/app.js`, `app/static/app.css` |

### Rules for data sources

This project depends on other people's data, so new sources must:

1. be **free to access** and allow automated access under their terms of use and `robots.txt`;
2. **not bypass** paywalls, logins, bot protection or rate limits (don't spoof browser user agents to get around a block);
3. store **headlines and short excerpts only** for news (the code caps excerpts at 280 characters) and always link to the publisher;
4. be **optional** if they need an API key: skip cleanly with a `"skipped: set XYZ_KEY ..."` error when the key is missing, as the Census and USDA jobs do.

If a source needs a key, document it in `.env.example` and in the README's data source table.

## Reporting bugs and requesting features

Use the issue templates. For security problems, see [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Code of conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating you agree to uphold it.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
