# Copilot Instructions 00 - Prereqs and Repo Structure
Date: 2025-08-21

## Goal
Prepare the repository for a clean, incremental build with testing at every step.

## Context
- You already generate synthetic hospital data and write it into MySQL.
- Frontend instructions exist in `frontend_copilot_instructions.md`.
- Target stack for the backend: **FastAPI + MySQL**.
- Deployment target: **GCP** with **Cloud Run** and **Cloud SQL for MySQL**. Local dev via Docker Compose.

## Tasks
1. Create a top-level `apps/` folder with subfolders:
   - `apps/api`
   - `apps/frontend`
   - `apps/jobs/seed`
2. Create a top-level `infra/` folder with subfolders:
   - `infra/docker` for Dockerfiles and Compose
   - `infra/gcp` for Cloud Run and Cloud SQL manifests or scripts
   - `infra/ci` for GitHub Actions
3. Add a top-level `tests/` folder:
   - `tests/api/` for API tests
   - `tests/e2e/` for end to end smoke tests
4. Make a `.env.example` with placeholders:
   ```ini
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_DB=hospital
   MYSQL_USER=hospital_user
   MYSQL_PASSWORD=devpassword
   ```
5. Create a `pyproject.toml` at repo root for shared dev tooling:
   - Tools: ruff, black, pytest, httpx, pytest-asyncio, pydantic.
6. Create `README_LOCAL_DEV.md` with commands to run local Compose and smoke test endpoints.

## Deliverables
- Folder structure exists and is committed.
- `.env.example` present.
- `pyproject.toml` with shared dev dependencies.
- `README_LOCAL_DEV.md` with run instructions.

## Definition of Done
- `git status` shows the new folders and files committed.
- `uv pip install -e .` or `pip install -e .` succeeds for dev tooling scope if used.
- Pre-commit hooks run if configured.

## Self-test
- Run `tree -L 3` at repo root and verify the structure.
- Open `.env.example` and confirm variable names match later files.
