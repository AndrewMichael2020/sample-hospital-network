# Copilot Instructions 02 - Backend API Implementation
Date: 2025-08-21

## Goal
Implement the API server that serves the contract against MySQL using connection pooling.

## Tasks
1. Create `apps/api/app/main.py` with FastAPI app, CORS, and routers from step 01.
2. Add `apps/api/app/db.py` with async MySQL pool using `asyncmy` or `aiomysql`.
3. Add `apps/api/app/repositories/` with query modules:
   - `facilities.py`, `patients.py`, `ed.py`.
   Each exports async functions that take filters and return DTOs.
4. Add config loader `apps/api/app/config.py` that reads env vars: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DB`, `MYSQL_USER`, `MYSQL_PASSWORD`.
5. Implement endpoints to query real tables with safe parameterized SQL. Keep queries simple and add `LIMIT/OFFSET` for pagination.
6. Add lightweight auth off-switch:
   - If `DISABLE_AUTH=true`, endpoints are public for demo.
7. Add Dockerfile at `infra/docker/Dockerfile.api`:
   - Multi-stage build
   - Expose 8080
   - Healthcheck on `GET /health`

## Deliverables
- Running API returning real data.
- Docker image builds locally.

## Definition of Done
- `pytest -q` green for repository unit tests.
- API returns non-empty `data` for at least one endpoint given seeded DB.

## Self-test
- Unit tests: create `tests/api/test_pagination.py` and `tests/api/test_shapes.py` that hit a test app with a temporary DB or a stubbed repo.
- Integration: with local Compose up, run:
  ```bash
  curl -s http://localhost:8080/facilities?page=1&pageSize=5 | jq '.meta.pageSize==5'
  curl -s "http://localhost:8080/ed/encounters?page=1&pageSize=5&from=2025-01-01" | jq '.data | length >= 0'
  ```
