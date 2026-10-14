#!/usr/bin/env bash
# Deploy Coffee Origin Monitor to Cloud Run + Firestore + Cloud Scheduler.
#
#   PROJECT_ID=my-project DASH_PASSWORD='choose-one' ./deploy.sh
#
# Optional: REGION (default us-central1), CENSUS_API_KEY, FAS_API_KEY
# Safe to re-run: every step creates or updates.
set -euo pipefail

: "${PROJECT_ID:?set PROJECT_ID}"
: "${DASH_PASSWORD:?set DASH_PASSWORD (the dashboard login password)}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-coffee-monitor}"
TZ_SCHED="${TZ_SCHED:-America/Chicago}"

gcloud config set project "$PROJECT_ID" >/dev/null
echo "▸ Enabling APIs"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com firestore.googleapis.com cloudscheduler.googleapis.com

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "▸ Firestore (native mode, free tier applies to the (default) database)"
if ! gcloud firestore databases describe --database='(default)' >/dev/null 2>&1; then
  gcloud firestore databases create --location=nam5 --type=firestore-native
fi
# Composite indexes: one array-contains filter + newest-first ordering.
for f in origins topics tokens; do
  gcloud firestore indexes composite create --collection-group=articles \
    --field-config="field-path=${f},array-config=contains" \
    --field-config="field-path=published,order=descending" --async --quiet 2>/dev/null || true
done
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:${RUN_SA}" \
  --role=roles/datastore.user --condition=None >/dev/null

echo "▸ Secrets"
put_secret() {  # name value
  if ! gcloud secrets describe "$1" >/dev/null 2>&1; then
    printf '%s' "$2" | gcloud secrets create "$1" --data-file=- >/dev/null
  else
    printf '%s' "$2" | gcloud secrets versions add "$1" --data-file=- >/dev/null
  fi
  gcloud secrets add-iam-policy-binding "$1" --member="serviceAccount:${RUN_SA}" \
    --role=roles/secretmanager.secretAccessor >/dev/null
}
put_secret dash-password "$DASH_PASSWORD"
if gcloud secrets describe ingest-token >/dev/null 2>&1; then
  INGEST_TOKEN=$(gcloud secrets versions access latest --secret=ingest-token)
else
  INGEST_TOKEN=$(openssl rand -hex 24)
  put_secret ingest-token "$INGEST_TOKEN"
fi

ENV_VARS="STORE=firestore"
[[ -n "${CENSUS_API_KEY:-}" ]] && ENV_VARS="$ENV_VARS,CENSUS_API_KEY=$CENSUS_API_KEY"
[[ -n "${FAS_API_KEY:-}" ]] && ENV_VARS="$ENV_VARS,FAS_API_KEY=$FAS_API_KEY"

echo "▸ Building and deploying Cloud Run service"
gcloud run deploy "$SERVICE" \
  --source . --region "$REGION" --allow-unauthenticated \
  --set-secrets DASH_PASSWORD=dash-password:latest,INGEST_TOKEN=ingest-token:latest \
  --set-env-vars "$ENV_VARS" \
  --min-instances 0 --max-instances 2 --memory 512Mi --cpu 1 \
  --timeout 900 --concurrency 40
URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')

echo "▸ Scheduling ingestion"
schedule() {  # name cron path
  args=(--location "$REGION" --schedule "$2" --time-zone "$TZ_SCHED" --uri "${URL}$3" --http-method POST
        --headers "X-Ingest-Token=${INGEST_TOKEN}" --attempt-deadline 900s)
  gcloud scheduler jobs create http "$1" "${args[@]}" --quiet 2>/dev/null \
    || gcloud scheduler jobs update http "$1" "${args[@]}" --quiet >/dev/null
}
schedule coffee-news        "*/15 * * * *" "/tasks/ingest/news"
schedule coffee-data-daily  "20 6 * * *"   "/tasks/ingest/data"
schedule coffee-data-fast   "5 */3 * * *"  "/tasks/ingest/data?only=closes,weather"

echo "▸ Running first ingestion (takes a minute or two)"
gcloud scheduler jobs run coffee-data-daily --location "$REGION" >/dev/null
gcloud scheduler jobs run coffee-news --location "$REGION" >/dev/null

echo
echo "✓ Deployed: $URL"
echo "  Log in with any username and the password you set."
echo "  Firestore indexes build in the background; news search/filters work once they finish (~5 min)."
