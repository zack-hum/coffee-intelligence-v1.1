# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.1.0] - 2026-10-12

First public release.

### Added
- Open-source project files: contributing guide, code of conduct, security policy, issue and pull request templates, CI (lint, tests, Docker build), Dependabot, `pyproject.toml` tool config, `.editorconfig`, `.gitattributes`, `.dockerignore`.
- Google News `site:` queries for Perfect Daily Grind, Comunicaffe, European Coffee Trip and The Tico Times, whose own feeds block automated access.

### Changed
- US imports by origin now request country-level rows and use shipping weight for kilograms; previously only the all-countries total was returned.
- The Census job requires `CENSUS_API_KEY` (the Census API no longer serves requests without one) and is skipped cleanly when it is missing.
- The Docker image runs as a non-root user.

### Removed
- Live robusta futures (tile, chart, market hours, daily closes). Yahoo delisted `RC=F`/`RM=F` and there is no free alternative. IMF monthly robusta prices remain on the Data page.
- RSS feeds that no longer exist or can't be reached: Royal Coffee, STiR, World Coffee Research, ICAFE, CRHoy, El Financiero (CR).

### Fixed
- Overview, Origins and Costa Rica pages failing to load on Windows: added the `tzdata` dependency so time zones resolve.

## [1.0.0] - 2026-10-09

Initial private version.

[Unreleased]: https://github.com/<owner>/coffee-intelligence-v1.1/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/<owner>/coffee-intelligence-v1.1/releases/tag/v1.1.0
