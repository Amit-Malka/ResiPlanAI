# Project Epics and Stories - ResiPlanAI

## Epic 1: Project Foundations and Scaffolding
**Goal:** Establish the polyglot monorepo structure and core service scaffolding as defined in the architecture.

### Story 1.1: Initialize Nx Monorepo
**Description:** Create the integrated Nx workspace to manage the React and Python codebase.
**Acceptance Criteria:**
- Nx workspace created at project root.
- `nx.json` configured for integrated apps.

### Story 1.2: Scaffold Core Applications
**Description:** Generate the Frontend (React), API (Node.js), and Solver (FastAPI) applications within the monorepo.
**Acceptance Criteria:**
- `apps/frontend` (React + Vite) initialized.
- `apps/api` (Node.js) initialized.
- `apps/solver` (Python FastAPI) initialized.

### Story 1.3: Database and Auth Foundations
**Description:** Configure PostgreSQL 18 connection and initial Auth0 integration.
**Acceptance Criteria:**
- `docker-compose.yml` with Postgres 18 and Redis.
- Auth0 configuration placeholders in environment files.
