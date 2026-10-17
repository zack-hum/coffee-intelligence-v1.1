# Free hosting before the Costa Rica trip (Jan 4, 2027)

Date: 2026-10-16 · Topic rotation: engineering / infrastructure (prerequisite for user zero on the trip)

## Question

Z needs the platform reachable from his phone, away from his laptop, before Jan 4 — at **$0**, and
ideally with **nothing that can silently start billing** (CLAUDE.md: "the MVP must be free").
What is the best free home for the current FastAPI app?

## What the app needs from a host

- A long-running Python container (FastAPI + uvicorn; `Dockerfile` already exists).
- A **durable** archive. `APP_MODE=cloud` already uses `FirestoreStore` (`app/store.py`), which was
  written to stay inside Firestore's free quotas. SQLite needs a persistent disk.
- A scheduler that POSTs `/tasks/ingest/news` (every 15–30 min) and `/tasks/ingest/data`
  (daily + every 3 h) with the `X-Ingest-Token` header. Already implemented in `app/main.py`.
- HTTP basic auth via `DASH_PASSWORD` (already implemented).
- Offline use on farms is a **client** concern (service worker / PWA), not a hosting one — it is
  needed whichever host we pick (see proposal #10, Field mode).

## Options checked (October 2026)

| Option | Free allowance | Card / billing account | Durable storage | Verdict |
|---|---|---|---|---|
| **Google Cloud Run + Firestore + Cloud Scheduler** (current `deploy.sh`) | 180k vCPU-s, 360k GiB-s, 2M requests, 1 GiB N.A. egress / month; Firestore 1 GiB + 50k reads / 20k writes per day; 3 Scheduler jobs per billing account | **Required** — the GCP free tier needs a billing account; usage past free tier is billed | Firestore | Works, but can bill. See cost check below. |
| **Render Free web service** | 750 instance-hours / month per workspace; spins down after 15 min idle, ~1 min to wake | Docs only mention a payment method for overages; without one, free services are **suspended**, not billed | **Ephemeral** filesystem, no disks; free Postgres expires after 30 days | Good compute host if storage lives elsewhere. |
| **Firestore on Firebase Spark plan** | Same Firestore free quotas (50k reads / 20k writes per day, 1 GiB) | **No** payment info; exceeding a quota **shuts that product off** for the month instead of charging | Firestore | Card-free durable store — and our code already speaks Firestore. |
| **GitHub Actions `schedule`** | Free and unmetered for **public** repos on standard runners (this repo is public) | No | n/a | Free cron to call `/tasks/ingest/*` (and keep the Render service warm). Best-effort timing; GitHub can delay or (after 60 days of repo inactivity) disable scheduled workflows. |
| Koyeb free | 1 web service, 512 MB, 0.1 vCPU, Frankfurt / Washington only | Card required ($29 pre-auth hold) | Unclear | Rejected: card + tiny CPU. |
| Hugging Face Spaces | CPU Basic free (2 vCPU, 16 GB) | — | Not persistent | Rejected: **Docker Spaces now need a paid plan**. |
| PythonAnywhere free | 1 web app, 512 MiB | No | Yes | Rejected: free web apps expire after 1 month; new accounts (since Jan 2026) get no scheduled tasks; WSGI-first. |
| GitHub Pages static snapshot | Free | No | n/a | Rejected for now: would mean rewriting the FastAPI app as static; publishing a public data snapshot conflicts with Yahoo / Google News "personal research, not redistribution" terms; private CRM/field data can't live there. |

### Cost check on the current Cloud Run path

News ingestion runs 8 GDELT queries at `GDELT_DELAY=5.5` s plus ~65 RSS feeds, so one run is
roughly ≥ 60 s of request time. With request-based billing CPU is charged for the whole request:
60 s × 96 runs/day × 30 days ≈ **173k vCPU-seconds — about 96 % of the 180k free allowance** before
counting the data jobs and Z's own page views. At the `deploy.sh` default of `*/15`, the free tier is
at risk; `*/30` halves it. The README already hints at this ("If you go over, change the news schedule
to `*/30`"). Budget alerts on GCP notify but do **not** cap spending.

## Recommendation

**Render Free (compute) + Firestore on Firebase Spark (storage) + GitHub Actions cron (scheduler).**

- **Card-free by construction.** Spark hard-stops at quota; Render suspends instead of billing when
  no payment method is on file; Actions is free on public repos. Nothing can silently start billing.
- **Almost no app code.** The app already runs in `APP_MODE=cloud` with `STORE=firestore`, token-auth
  ingestion endpoints and basic auth. New pieces are config: a `render.yaml` blueprint, a Firestore
  index file, a scheduled workflow that `curl`s the task endpoints, and a deploy guide.
- **Cold starts mostly hidden.** The 15-minute news cron keeps the service warm most of the day.
  One always-on service uses ≤ 744 h of the 750 h monthly allowance.
- **Main alternative rejected:** keep Cloud Run (`deploy.sh`) at `*/30`. It is already built and
  more robust, but needs a card on a billing account and runs close to the vCPU free tier — a paid
  risk the MVP rule says to avoid unless there is a really good reason. It stays available for
  "go live" later.

### Risks / open points

- Render may suspend free services with "unusually high service-initiated traffic"; ~65 feeds every
  15–30 min is modest but should be watched on the Sources page. Mitigation: 30-min news cadence.
- GitHub cron can run late by several minutes and is disabled after 60 days without repo activity
  (agent PRs keep it active; the workflow can also be run manually).
- The Firestore service-account key must live only as a Render secret file and a GitHub Actions
  secret for the ingest token — never in the repo. Z creates the accounts (agent can't sign up).
- The Firestore composite indexes (`origins`/`topics`/`tokens` + `published desc`) that `deploy.sh`
  creates with `gcloud` need to be created another way on Spark (console or a
  `firestore.indexes.json` deployed with the free Firebase CLI).
- Ingestion jobs on Render share the single 0.1–0.5 vCPU instance with page views; acceptable for
  one user.

## Implications for us

1. Proposal #13: **card-free hosting on Render + Firestore (Spark) + GitHub Actions cron** — needs Z's
   approval because it touches deployment and CI.
2. Whatever the host, Field mode (#10) must ship a PWA shell + offline cache so the app works with no
   signal on farms; hosting only solves "reachable when there is signal".
3. If Z ever moves back to Cloud Run, change the `deploy.sh` news schedule to `*/30` and add a budget
   alert — log as a follow-up, not now.

## Sources

- Render, "Deploy for Free": https://render.com/docs/free
- Render platform review (mid-2026 plan change, bandwidth): https://jwatte.com/blog/render-com-platform-review.md
- Firebase pricing plans (Spark: no payment info, usage shut off at quota): https://firebase.google.com/docs/projects/billing/firebase-pricing-plans
- Cloud Run pricing (free tier amounts): https://cloud.google.com/run/pricing
- GCP free tier summary (billing account required, Scheduler 3 jobs, Firestore quotas): https://agentdeals.dev/gcp-free-tier-2026
- GitHub Actions billing (free for public repos on standard runners): https://docs.github.com/en/billing/concepts/product-billing/github-actions
- Koyeb pricing FAQ (free instance specs, card + pre-auth): https://www.koyeb.com/docs/faq/pricing
- Hugging Face Spaces overview (Docker Spaces need a paid plan; disk not persistent): https://huggingface.co/docs/hub/en/spaces-overview
- PythonAnywhere free account features: https://help.pythonanywhere.com/pages/FreeAccountsFeatures/

"Would improve quality" (paid, not proposed): Render Starter instance (no spin-down, persistent disk);
Cloud Run min-instances=1 (no cold start).
