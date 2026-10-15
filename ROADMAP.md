# Roadmap

Priority order for ideas. An item here is **not** approved work: the agent turns items into
`proposal` issues, and only issues Z labels `approved` get built (see `docs/DEVELOPMENT.md`).
Z can reorder, delete or add items in a PR or by commenting on any issue.

## Now (top = next)

- [ ] Costa Rica trip mode: turn the trip planner into a practical field guide — per-region
      farm/mill/cooperative visit list, harvest status during trip dates, what to ask producers,
      price-check calculator presets (USD/lb FOB ↔ ₡/fanega ↔ ₡/kg). Trip: Jan 4–17, 2027 (sourcing mission).
- [ ] Competitor & adjacent-software landscape: first full pass into `agent/COMPETITORS.md`.
- [ ] Source health: audit every feed in `app/config.py`, replace dead ones with working free alternatives.
- [ ] Differentials: add a reference table of typical specialty differentials by origin/grade
      (sourced, dated), and use it as defaults in the implied-local-price tool.

## Next

- [ ] Weekly market brief page: auto-generated summary of price moves, CFTC positioning,
      weather anomalies and top-tagged news per origin (rule-based, no LLM).
- [ ] Alerts: user-defined thresholds (C price, BRL, rainfall anomaly) shown as a banner.
- [ ] Exporter / importer directory for Costa Rica (public sources only), linked to regions.
- [ ] Harvest & shipment calendar across all 18 origins in one view.

## Later

- [ ] Cloud deployment hardening for GCP (only when Z asks to go live).
- [ ] Personas: views tailored for roasters, green buyers, importers, cafes.

## Done

- v1.1.0 (2026-10-12) — see CHANGELOG.
