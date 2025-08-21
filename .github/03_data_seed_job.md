# Copilot Instructions 03 - Data Seed Job
Date: 2025-08-21

## Goal
Package the existing generator and load process as a one-shot container that seeds MySQL.

## Tasks
1. Move generator entrypoint into `apps/jobs/seed/main.py` with arguments:
   - `--records` default 100000
   - `--drop-and-recreate` default false
2. Read DB config from env vars consistent with API.
3. Ensure idempotent inserts or clean rebuild if `--drop-and-recreate` is set.
4. Add Dockerfile at `infra/docker/Dockerfile.seed`.
5. For local dev, add a Compose service `seed` that depends on `mysql` and runs once.

## Deliverables
- Seed image builds and can populate DB locally and in GCP as a Cloud Run Job.

## Definition of Done
- Local run fills tables and API list endpoints return non-empty data.

## Self-test
- Local: `docker compose run --rm seed --records 50000`
- Verify counts via API:
  ```bash
  curl -s http://localhost:8080/patients?page=1&pageSize=1 | jq '.meta.total > 1000'
  ```
