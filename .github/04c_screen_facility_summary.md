# Copilot Instructions 04c — Screen 1: Facility Summary
Date: 2025-08-21

## Goal
Render KPIs and a simple chart from `/facilities/summary` with loading and error states.

## Tasks
1. Create `src/components/KpiCard.tsx` to display a label, value, and delta (optional).
2. Implement `src/screens/FacilitySummary.tsx`:
   - Use `useFacilitiesSummary()`.
   - Render 3–6 KPI cards (required beds, staffed beds, gap, nursing FTE).
   - Render a small `Recharts` bar/line chart if series exist.
   - Provide `ErrorState` and `Loading` fallbacks.
3. Wire route in `src/routes/router.tsx`:
   - `/` → FacilitySummary
4. Add unit tests `src/screens/FacilitySummary.test.tsx`:
   - Renders loading
   - Renders KPIs when data arrives
   - Renders ErrorState on failure (mock query error)

## Definition of Done
- Page renders with mock data and real API.
- Axe-lite check: semantic headings and labels present.

## Self‑test
- `npm run test` shows the 3 tests passing.
- Manual: stop API; page shows a readable error.
