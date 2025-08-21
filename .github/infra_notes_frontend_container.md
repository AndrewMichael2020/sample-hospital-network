# Frontend Container Notes
Date: 2025-08-21

## Goal
Containerize the frontend as a static site served by a simple HTTP server.

## Tasks
1. Create `infra/docker/Dockerfile.frontend`:
   - Stage 1: build frontend
   - Stage 2: copy build artifacts to a minimal HTTP server image (node or nginx or a tiny Go static server).
2. Expose 8081 and set a `HEALTHCHECK` route `/`.

## Self-test
- `docker build -f infra/docker/Dockerfile.frontend -t frontend:dev .`
- `docker run -p 8081:8081 frontend:dev`
- Visit `http://localhost:8081`.
