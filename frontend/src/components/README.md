# Components Module Guide

## Purpose
`src/components` contains reusable UI modules. Keep components grouped by domain to preserve cohesion and avoid a flat component dump.

## Folder Rules
- `common/`: Reusable UI primitives used across domains.
- `layout/`: Shell/navigation modules used by `layouts/`.
- `thread/`: Thread-specific components only.
- `comment/`: Comment-specific components only.
- `notification/`: Notification-specific components only.

## Design Rules
- Single Responsibility: each component should have one clear UI responsibility.
- Dependency Inversion: pages/layouts should import folder barrels (`index.js`) instead of deep file paths when possible.
- Open/Closed: prefer extending with composition/props rather than editing shared components for one-off behavior.
- Keep business logic in `services/` or `context/`; keep components mostly presentational and interaction-focused.

## Import Pattern
Prefer:
```js
import { Pagination, SearchBar } from '../components/common'
import { ThreadCard } from '../components/thread'
```

Avoid new cross-domain coupling (for example, `thread/` importing from `dashboard/`).

## File Pairing
For CSS modules, keep style and component together:
- `Component.jsx`
- `Component.module.css`
