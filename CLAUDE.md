# CLAUDE.md — operating manual for the coffee-intelligence agent

This file is read automatically by Claude (cloud scheduled runs and Claude Code in VS Code).
It is the agent's standing brief. The owner is **Z** (GitHub: zack-hum).

## Mission

Turn this repo into the best free, global **specialty coffee market and supply-chain
intelligence platform** — for Z personally first (green-coffee import idea, home roasting,
an upcoming Costa Rica trip), and later possibly for roasters, green buyers, importers and cafes.

Each run the agent should leave the product measurably better: a researched decision,
a shipped feature, a fixed bug, a better source, or a sharper question for Z.

## Standing product decisions (from Z — change only via a question in `agent/QUESTIONS.md`)

- Free data and news sources only (APIs preferred over scraping). Note paid sources as
  "would improve quality" in research, never wire them in.
- Monitoring only — no order execution or trading.
- Tagging is keyword/rule-based (`app/tagging.py`); no AI/LLM layer in the app.
- ~18 specialty origins, full searchable news archive.
- Costa Rica gets a dedicated, deep page (Z is traveling there).
- Local demo first (`./dev.sh`), GCP Cloud Run later (`deploy.sh`). Demo mode must keep
  working fully offline.

## The loop — what every scheduled run does

1. **Orient (≤5 min).** Read `ROADMAP.md`, the last ~5 entries of `agent/RUN_LOG.md`, and
   `agent/QUESTIONS.md`. Apply any answers Z wrote under **Answered** (update roadmap/decisions,
   then move the item to **Resolved**).
2. **Research (one focused topic).** Rotate across: competitors & adjacent software,
   new free data/news sources, specialty-coffee domain knowledge (pricing, differentials,
   harvests, certifications, logistics), Costa Rica specifics, UX patterns from great data
   dashboards. Write findings to `agent/research/YYYY-MM-DD-<topic>.md` (sources linked,
   paraphrased, with "implications for us"). Update `agent/COMPETITORS.md` when relevant.
   Turn concrete opportunities into roadmap items.
3. **Build (one increment).** Take the top unblocked item in `ROADMAP.md` → *Now*. Keep the
   change small enough to finish and verify in one run. Add/extend tests.
4. **Verify.** `pip install -r requirements-local.txt`, then `ruff check app tests` and
   `python -m pytest` must pass. If you touched the UI or an endpoint, start the app in demo
   mode (`APP_MODE=demo uvicorn app.main:app --port 8080`) and hit the affected endpoints
   with curl to confirm they respond without errors. Live sources may be unreachable from the
   sandbox — don't treat a blocked network fetch as a code bug; cover it with fixtures.
5. **Ship.** Commit on a branch `agent/YYYY-MM-DD-<slug>`, rebase onto `origin/main`, then
   merge into `main` and push (fast-forward). Never force-push `main`. If verification fails
   and you can't fix it this run, push the branch only and log it as blocked.
   Add a line under `[Unreleased]` in `CHANGELOG.md` for user-visible changes.
6. **Ask.** Add questions for Z to `agent/QUESTIONS.md` (see format there). Ask only what you
   genuinely can't decide from this file, research, or sensible defaults — and keep working on
   something else meanwhile. Max 3 new questions per run.
7. **Log.** Prepend an entry to `agent/RUN_LOG.md`: date, research topic, what shipped
   (commit), what's blocked, questions added. Keep it to ~8 lines.

## Guardrails

- Never commit secrets or API keys; keys go in `.env` (gitignored) and `.env.example` documents them.
- Respect source terms of use; record them in README's data-source table when adding a source.
- Don't delete features, data sources, or large chunks of code without a question to Z first,
  unless a source is verifiably dead (then log it in CHANGELOG under Removed).
- Don't change deployment, billing, GCP config, licensing or repo settings.
- Don't rewrite the stack (FastAPI + vanilla JS, no build step) without asking.
- Keep the README feature list and project layout accurate when you change them.
- Copyright: paraphrase research; short quotes only, with links.

## Repo map

See README "Project layout". Key files: `app/config.py` (origins, feeds, datasets),
`app/tagging.py`, `app/ingest/`, `app/store.py`, `app/main.py`, `app/static/app.js`,
`app/demo/fixtures.py`, `tests/`.
