# Copilot Instructions 04e — Screen 3: ED Projections
Date: 2025-08-21

## Goal
Line chart of ED projections with year and method selectors; export CSV.

## Tasks
1. Implement `src/screens/EdProjections.tsx`:
   - Form controls: `year` select, `method` select (e.g., "simple","arima" placeholder).
   - Fetch with `useEdProjections({ year, method })`.
   - Render `Recharts` LineChart with tooltips.
   - Add "Export CSV" that converts current series to CSV and triggers download.
2. Route `/ed/projections` → EdProjections.
3. Tests `EdProjections.test.tsx`:
   - Changing year refetches
   - CSV export produces a blob with header row

## Definition of Done
- Chart renders and responds to control changes.
- CSV exports current view.

## Self‑test
- Manual: change year and confirm network call parameters change.
