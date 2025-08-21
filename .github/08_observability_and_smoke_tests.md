# Copilot Instructions 08 - Observability and Smoke Tests
Date: 2025-08-21

## Goal
Provide minimal visibility and alarms suitable for a demo.

## Tasks
1. Add a `/health` and `/ready` endpoint in API that reports DB connectivity latency.
2. Add basic structured logging with request id and timing.
3. Add `tests/e2e/smoke_api.sh` that checks 3 endpoints and non-empty payloads.
4. Document how to view Cloud Run request logs and error logs in Cloud Logging.
5. Optionally add a 1-minute uptime check using a GitHub Actions cron that curls the API URL.

## Deliverables
- Health endpoints, structured logs, e2e script, and a short doc.

## Definition of Done
- `bash tests/e2e/smoke_api.sh` prints OK locally and against Cloud Run URL.

## Self-test
- Break DB credentials locally and confirm `/ready` reports unhealthy.
- Restore and confirm it flips to healthy within a few seconds.
