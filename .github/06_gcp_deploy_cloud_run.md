# Copilot Instructions 06 - GCP Deploy with Cloud Run and Cloud SQL
Date: 2025-08-21

## Goal
Deploy containers to GCP using managed services. No scale required, but the setup should be clean.

## Architecture
- API → Cloud Run service
- DB → Cloud SQL for MySQL
- Seed → Cloud Run Job
- Images → Artifact Registry
- Secrets → Secret Manager

## Tasks
1. Create `infra/gcp/README.md` with a short plan and variables.
2. Create scripts:
   - `infra/gcp/build_and_push.sh` builds `api`, `frontend`, `seed` and pushes to Artifact Registry.
   - `infra/gcp/deploy_api.sh` deploys Cloud Run service for API, attaches Cloud SQL connection.
   - `infra/gcp/deploy_frontend.sh` deploys frontend (Cloud Run simple static server) or GCS+CDN if preferred.
   - `infra/gcp/deploy_seed_job.sh` deploys Cloud Run Job and runs it once.
3. Add minimal IAM notes to grant the Cloud Run service accounts access to Secret Manager and Cloud SQL.
4. Add `.env.gcp.example` for GCP env vars and DB secrets mapping.

## Deliverables
- Shell scripts under `infra/gcp/` ready to run with `gcloud`.

## Definition of Done
- API reachable at a Cloud Run URL and returns data after the seed job runs.

## Self-test
- After deploy, run:
  ```bash
  curl -s https://<api-cloud-run-url>/facilities?page=1&pageSize=5 | jq type
  ```
- Confirm Cloud SQL has tables and rows via `gcloud sql connect` or Adminer if used.
