# Copilot Instructions 04b — API Client, Types, and Guards
Date: 2025-08-21

## Goal
Create a typed API client that validates responses at runtime and exposes simple hooks.

## Tasks
1. Define Zod schemas in `src/api/schemas.ts`:
   - `Meta`, `Paged<T>`, `Facility`, `FacilitySummary`, `Patient`, `EdEncounter`, `ProjectionPoint`.
2. Export TypeScript types from `src/api/types.ts` derived from Zod (`z.infer`).
3. Create Axios client `src/api/client.ts`:
   - Base URL `import.meta.env.VITE_API_BASE_URL`.
   - Interceptor to attach `x-request-id` header.
   - Functions:
     - `getFacilitiesSummary()` → `FacilitySummary`
     - `getPatients(page, pageSize, q?)` → `Paged<Patient>`
     - `getEdProjections(year, method?)` → `ProjectionPoint[]`
   - Validate each response with Zod; throw on parse failure.
4. Add React Query hooks in the same file or `src/api/hooks.ts`:
   - `useFacilitiesSummary()`
   - `usePatients(params)`
   - `useEdProjections(params)`

## Definition of Done
- Bad JSON from API is rejected with a clear error (ZodError).

## Self‑test
- Add `src/api/client.test.ts` (Vitest) to mock Axios and verify:
  - Correct URL and params
  - Zod validation failure throws
