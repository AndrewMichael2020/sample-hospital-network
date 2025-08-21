# Copilot Instructions 01 - API Contract (OpenAPI First)
Date: 2025-08-21

## Goal
Freeze a minimal read-only API contract that the frontend will target.

## Endpoints
- `GET /facilities` - list facilities with paging and filters.
- `GET /facilities/summary` - rollups for bed counts, ED visits, occupancy.
- `GET /patients` - list patients with paging and filters.
- `GET /ed/encounters` - encounter list with time filters.
- `GET /ed/projections` - simple projection endpoint for demo charts, accepts `year` and `method`.

## Contract Rules
- Pagination: `page`, `pageSize` with defaults `page=1`, `pageSize=25`.
- Filtering: `q` free-text where applicable.
- All responses contain a top-level `data` array and `meta` object with `page`, `pageSize`, `total`.
- Timestamps in ISO-8601 UTC.
- No mutation in this demo.

## Tasks
1. Create `apps/api/openapi.yaml` that defines the endpoints above with schemas:
   - `Facility`, `FacilitySummary`, `Patient`, `EdEncounter`, `ProjectionPoint`.
2. Add error schema `ErrorResponse` with `code`, `message`, `details`.
3. Generate a FastAPI router scaffold from `openapi.yaml` using Copilot.
4. Place DTOs in `apps/api/app/schemas.py` using Pydantic models that match the OpenAPI.

## Deliverables
- `apps/api/openapi.yaml` checked in.
- FastAPI router stubs that match the spec.
- Pydantic schemas aligned with OpenAPI.

## Definition of Done
- `redocly lint apps/api/openapi.yaml` or `speccy lint` passes, or `openapi-python-client` can parse it.
- `from openapi_client import *` generation works if tried.

## Self-test
- Run `python -m uvicorn app.main:app --reload` in `apps/api`.
- `curl http://localhost:8000/openapi.json` returns JSON.
- `curl http://localhost:8000/facilities?page=1&pageSize=5` returns shape:
  ```json
  {"data": [], "meta": {"page":1,"pageSize":5,"total":0}}
  ```
