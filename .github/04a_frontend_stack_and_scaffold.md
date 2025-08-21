# Copilot Instructions 04a — Frontend Stack & Scaffold
Date: 2025-08-21

## Decision (concise)
- **Framework:** React + **TypeScript** (Vite) — simple, fast, no SSR needed for this demo.
- **Routing:** React Router.
- **Server state:** TanStack Query (React Query).
- **Tables:** TanStack Table.
- **Charts:** Recharts.
- **Styling:** CSS Modules. *You *can* add Tailwind later if desired.*
- **Tests:** Vitest + React Testing Library; Playwright for e2e.
- **Config:** `VITE_API_BASE_URL` env.

## Tasks
1. Scaffold:
   ```bash
   npm create vite@latest apps/frontend -- --template react-ts
   cd apps/frontend
   npm i react-router-dom @tanstack/react-query @tanstack/react-table recharts axios zod
   npm i -D vitest @testing-library/react @testing-library/jest-dom @types/node jsdom @types/jsdom playwright
   npx playwright install --with-deps
   ```
2. Add `.env.local` (do not commit):
   ```ini
   VITE_API_BASE_URL=http://localhost:8080
   ```
3. Create structure:
   ```text
   apps/frontend/src/
     api/
       client.ts
       types.ts
       schemas.ts
     routes/
       router.tsx
     screens/
       FacilitySummary.tsx
       PatientList.tsx
       EdProjections.tsx
     components/
       KpiCard.tsx
       DataTable.tsx
       ErrorState.tsx
       Loading.tsx
     lib/
       format.ts
     App.tsx
     main.tsx
   ```
4. Add scripts to `package.json`:
   ```json
   {
     "scripts": {
       "dev": "vite",
       "build": "vite build",
       "preview": "vite preview --port 8081",
       "test": "vitest run",
       "test:ui": "vitest",
       "e2e": "playwright test"
     }
   }
   ```

## Definition of Done
- `npm run dev` serves the app.
- `import.meta.env.VITE_API_BASE_URL` is readable in code.

## Self‑test
- `npm run test` runs (even with zero tests).
- `npm run e2e` executes Playwright sample test after init.
