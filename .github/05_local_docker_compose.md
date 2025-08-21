# Copilot Instructions 05 - Local Docker Compose
Date: 2025-08-21

## Goal
Run MySQL, API, and frontend locally with a single command.

## Tasks
1. Create `infra/docker/docker-compose.yml` with services:
   - `mysql` - MySQL 8, volume for data, env from `.env`.
   - `api` - built from `infra/docker/Dockerfile.api`, port 8080.
   - `frontend` - built from `infra/docker/Dockerfile.frontend`, port 3000 or 8081.
   - `seed` - built from `infra/docker/Dockerfile.seed`, run once.
2. Add a `Makefile` at repo root with targets:
   - `make up`, `make down`, `make logs`, `make seed`.
3. Ensure `api` waits for `mysql` health before starting.

## Deliverables
- One command local spin up.

## Definition of Done
- `make up` starts services and seed runs to completion.

## Self-test
```bash
make up
sleep 5
curl -s http://localhost:8080/health | jq '.status=="ok"'
curl -s http://localhost:8080/patients?page=1&pageSize=5 | jq type
```
