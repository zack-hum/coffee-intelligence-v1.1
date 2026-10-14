# Security Policy

## Supported versions

Only the latest release on the `main` branch receives security fixes.

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report them privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**. Include what you found, how to reproduce it, and the impact you expect. You should get a response within 7 days.

## Deployment notes

If you run your own instance:

- **Set `DASH_PASSWORD`** for any instance reachable from the internet. Without it, the dashboard and API are open to anyone. `deploy.sh` requires it and stores it in Secret Manager.
- **Keep `DEV_TOOLS` off in public deployments.** The Dev page can reset the archive and trigger ingestion. It is off by default on Cloud Run.
- **Never commit `.env`.** It holds your API keys and is excluded by `.gitignore`. If a key is ever committed, revoke it with the provider and issue a new one; deleting the file from Git history is not enough.
- **The ingestion endpoints** (`/tasks/*`) require the `X-Ingest-Token` header, which `deploy.sh` generates and stores in Secret Manager.
