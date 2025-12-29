---
project_name: 'ResiPlanAI'
user_name: 'Amit'
date: '2025-12-29'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'quality_rules', 'workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 22
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Frontend:** React 19.2, Vite, MUI v6 (DataGrid Premium), Zustand 5, React Query
- **Backend (Orchestrator):** Node.js 20+, Express/NestJS, Auth0 SDK
- **Backend (Solver):** Python 3.11+, FastAPI 0.128, Google OR-Tools, Celery, Redis
- **Database:** PostgreSQL 18.1 (with temporal tables)
- **Build System:** Nx Monorepo (Integrated)

## Critical Implementation Rules

### Language-Specific Rules

- **TypeScript:** Strict mode enabled. Interfaces shared via `libs/api-interfaces`.
- **Python:** Type hints required for all functions. Pydantic models for all data shapes.
- **Dates:** Strictly **ISO 8601 Strings** (`YYYY-MM-DD`). NO Unix timestamps.

### Framework-Specific Rules

- **React:** Use `useGridStore` for high-frequency matrix updates. Use React Query for server state.
- **FastAPI:** All endpoints must be async. Use dependency injection for DB sessions.
- **Nx:** Use `nx g` to generate new components/libraries. Do not manually create folders outside the Nx structure.

### Testing Rules

- **Co-location:** Tests MUST be siblings to source files (`Grid.tsx` -> `Grid.test.tsx`, `solver.py` -> `test_solver.py`).
- **Integration:** Write integration tests for the `api -> solver` handoff using the local Docker stack.

### Code Quality & Style Rules

- **Naming:**
    - API Payloads: **camelCase** (Frontend/Node)
    - Database/Python: **snake_case**
    - *CRITICAL:* Trust the middleware to convert cases. Do not mix cases in business logic.
- **Error Handling:** Return semantic error codes (e.g., `CONFLICT_SYLLABUS`) to drive the UX Conflict Panel.

### Development Workflow Rules

- **Feature Flags:** Use "Anchors" as the primary user constraint mechanism.
- **State:** Use optimistic updates for the Grid, but rollback on Solver failure.

### Critical Don't-Miss Rules

- **Solver Isolation:** The Frontend MUST NOT call the Solver directly. Always go through the Node.js API.
- **Immutable Past:** Logic must reject any write operation to a month < Current Month.
- **Anchor Priority:** The Solver must treat "Anchors" as infinite-weight constraints.

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2025-12-29
