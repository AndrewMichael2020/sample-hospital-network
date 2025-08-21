# Copilot Instructions 04 - Frontend Vertical Slices
Date: 2025-08-21

## Goal
Implement 2 to 3 end-to-end pages using the previously frozen API contract. Use the existing `frontend_copilot_instructions.md` as base.

## Pages in order
1. Facility Summary
2. Patient List
3. ED Projections

## Tasks
1. In `apps/frontend`, scaffold the app per `frontend_copilot_instructions.md`.
2. Create a shared API client module that reads `API_BASE_URL` from env.
3. Implement Facility Summary:
   - Fetch `/facilities/summary`, show KPIs and a simple chart.
4. Implement Patient List:
   - Fetch `/patients` with pagination controls.
5. Implement ED Projections:
   - Fetch `/ed/projections?year=2025` and render a line chart.

## Deliverables
- Each page wired to live endpoints with loading and error states.

## Definition of Done
- Local dev server shows data for all 3 pages against local API.

## Self-test
- Script `tests/e2e/smoke_frontend.sh`:
  ```bash
  set -e
  curl -sf ${API_BASE_URL:-http://localhost:8080}/facilities/summary >/dev/null
  curl -sf ${API_BASE_URL:-http://localhost:8080}/patients?page=1&pageSize=5 >/dev/null
  curl -sf ${API_BASE_URL:-http://localhost:8080}/ed/projections?year=2025 >/dev/null
  echo OK
  ```
