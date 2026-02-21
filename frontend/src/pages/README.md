# Pages Module Guide

## Purpose
`src/pages` contains route-level modules only. A page composes domain components and orchestrates data loading.

## Folder Rules
- `auth/`: Login/register/password flow pages.
- `thread/`: Thread listing/detail pages.
- `dashboard/`: Role-based dashboard pages.

## Design Rules
- Single Responsibility: page handles route orchestration, not low-level reusable widget behavior.
- Separation of Concerns: call data/services via `services/` and state via `context/`; keep rendering delegated to `components/`.
- Interface Segregation: pass minimal props to child components.
- Keep route imports stable through `App.jsx` and avoid duplicate page folders.

## Page Checklist
- Route component owns loading/error/empty states.
- Domain rendering delegated to `components/*`.
- No duplicated UI logic that belongs in shared components.
- Imports should follow module boundaries (`components/common`, `components/thread`, etc.).
