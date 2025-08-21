# Copilot Instructions 04d — Screen 2: Patient List
Date: 2025-08-21

## Goal
Table with server-backed pagination and a search box.

## Tasks
1. Create `src/components/DataTable.tsx` using TanStack Table (client-side render).
2. Implement `src/screens/PatientList.tsx`:
   - Controls: search `q`, `page`, `pageSize`.
   - Use `usePatients({ page, pageSize, q })` and render rows.
   - Show total from `meta.total`; implement pager controls.
   - Preserve query state in URL via React Router search params.
3. Add route `/patients` → PatientList.
4. Add tests:
   - `PatientList.test.tsx` mocks API:
     - Initial fetch called with defaults
     - Changing page triggers new fetch
     - Search debounces and triggers new fetch

## Definition of Done
- Pagination round-trips with the API and updates URL.

## Self‑test
- With API and seed data running, you can navigate to page 2 and see rows change.
