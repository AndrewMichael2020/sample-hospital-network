# Copilot Instructions 07 - CI and CD (GitHub Actions)
Date: 2025-08-21

## Goal
Automate build, test, and deploy to Cloud Run on push to `main` and tagged releases.

## Tasks
1. Create `.github/workflows/ci.yml`:
   - Triggers on PR and push
   - Steps: checkout, set up Python and Node, lint, unit tests, build api and frontend containers, run API tests.
2. Create `.github/workflows/cd.yml`:
   - Trigger on `main` with a path filter for `apps/**` or on tags `v*`
   - Build and push to Artifact Registry
   - Deploy API and frontend via `gcloud` scripts in `infra/gcp/`
3. Cache dependencies where sensible to speed up CI.

## Deliverables
- CI runs on PR and shows green.
- CD deploys to a dev environment on merge to main.

## Definition of Done
- A PR that touches the API runs unit tests and fails if a contract breaks.
- A tag `v0.1.0` results in new images and a deployed revision.

## Self-test
- Open PR that intentionally breaks pagination. Verify CI fails on tests in `tests/api/test_pagination.py`.
- Merge a harmless change and watch CD logs complete.
