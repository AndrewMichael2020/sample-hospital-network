# Copilot Instructions 04f — Router, App Shell, Accessibility
Date: 2025-08-21

## Goal
Provide a minimal shell with nav, keyboard focus management, and basic a11y checks.

## Tasks
1. `src/App.tsx`:
   - Header with app title and nav links to the 3 screens.
   - Main region with `Outlet` from React Router.
   - Skip-to-content link for keyboard users.
2. Router in `src/routes/router.tsx` with lazy-loaded routes.
3. Add focus ring styles and ensure tab order is logical.
4. Add Playwright e2e specs in `tests/e2e/`:
   - `nav.spec.ts`: can navigate to each screen and see a heading.
   - `api.spec.ts`: if `VITE_API_BASE_URL` is reachable, confirm `/facilities/summary` populates KPIs.

## Definition of Done
- Keyboard-only navigation works end-to-end.
- e2e passes locally.

## Self‑test
- `npm run e2e` shows green on nav tests.
