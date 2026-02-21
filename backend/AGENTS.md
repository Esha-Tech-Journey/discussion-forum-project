# AGENTS.md

**Project:** Advanced Real-Time Discussion Forum
**Architecture Standard:** Layered + Event-Driven + Realtime Scalable

This file defines the authoritative rules, architecture, and governance standards for all AI coding agents and contributors working on this repository.

Agents MUST read and comply with this file before generating or modifying code.

---

# 1. System Architecture

The backend follows a strict layered architecture:

```
API → Services → Repositories → Models → Database
                     ↓
               Integrations
                     ↓
            Redis / WebSocket
```

### Folder Structure

```
backend/app/
├── api/                # HTTP route handlers
├── services/           # Business logic
├── repositories/       # DB persistence layer
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic schemas
├── dependencies/       # Auth/RBAC dependencies
├── websocket/          # WS managers + handlers
├── integrations/       # Redis, external services
├── utils/              # Helpers
├── core/               # Config, constants
└── db/                 # Session, base, migrations
```

---

# 2. Coding & Layer Rules

Agents MUST enforce:

* API layer contains no business logic.
* Services orchestrate workflows only.
* Repositories handle all DB queries.
* No ORM calls inside services.
* No DB/session usage inside API routes.

---

# 3. Database Standards

All user-facing entities MUST include:

```
id
created_at
updated_at
is_deleted (soft delete)
```

Soft delete is mandatory for:

* Users
* Threads
* Comments
* Notifications
* Moderation records

---

# 4. RBAC & Permissions

System supports multi-role users.

### Role Model

```
User ↔ Roles (Many-to-Many)
```

### Standard Roles

* ADMIN
* MODERATOR
* USER

### Dependency Pattern

```
require_user
require_moderator
require_admin
```

Agents MUST enforce RBAC on:

* Moderation endpoints
* Role management
* Admin dashboards
* Sensitive analytics

---

# 5. Realtime Architecture

WebSocket is used for realtime features:

* Live comments
* Likes
* Mentions
* Notifications
* Thread updates

Redis Pub/Sub is used for horizontal scaling.

### Event Flow

```
Action → Service → Redis Publish → WS Manager → Clients
```

Agents must ensure:

* Channel subscription matches publishers.
* No duplicate fan-out.
* Origin deduplication when scaled.

---

# 6. Caching Strategy

Redis is used for backend caching.

### Cacheable Data

* Threads list
* Thread details
* Comment lists (initial load)
* User profile
* Notification unread count

### Invalidation Rules

Agents MUST invalidate cache on:

* Thread creation/update/delete
* Comment create/delete
* Like/unlike
* Notification creation/read

Central invalidation utilities required.

---

# 7. Notification System (MANDATORY FEATURE)

A hybrid notification system MUST be implemented.

Notifications must support:

* Realtime delivery
* Offline persistence
* Read/unread tracking
* Multi-entity references

---

## 7.1 Notification Delivery Model

```
Event Occurs
     ↓
Create Notification (DB)
     ↓
Is User Online?
   ├─ Yes → Send via WebSocket
   └─ No  → Deliver via API later
```

WebSocket NEVER replaces DB storage.

DB is the source of truth.

---

## 7.2 Notification Events

Agents must generate notifications for:

* New comment on thread
* Reply to comment
* Mentions
* Likes
* Thread subscriptions
* Moderation actions
* Role changes

---

## 7.3 Notification Database Schema

Required model fields:

```
id
recipient_id
actor_id
type
title
message
entity_type
entity_id
is_read
created_at
```

Indexes required on:

```
recipient_id
is_read
created_at
```

---

## 7.4 Notification Services

Agents must implement:

```
create_notification()
get_user_notifications()
mark_as_read()
mark_all_as_read()
get_unread_count()
```

Flow rules:

1. Save to DB first.
2. Then attempt realtime delivery.
3. Never skip persistence.

---

## 7.5 WebSocket Integration

WS Manager must support:

```
user_id → connection mapping
```

Function required:

```
send_notification_to_user(user_id, payload)
```

If Redis Pub/Sub exists:

* Publish notification event.
* Subscribers deliver to sockets.

---

## 7.6 Notification APIs

Required endpoints:

```
GET    /notifications
PATCH  /notifications/{id}/read
PATCH  /notifications/read-all
GET    /notifications/unread-count
```

Must enforce ownership checks.

Users can only access their notifications.

---

## 7.7 Notification Caching

Agents should cache:

* Unread counts
* Recent notifications

Invalidate when:

* New notification created
* Notification marked read

---

# 8. Security Standards

Agents MUST enforce:

* No secrets in repo
* Env-based config only
* Ownership validation
* Token type validation
* Role enforcement

Never commit:

```
.env
credentials
API keys
```

---

# 9. Migration Governance

Agents must ensure:

* No empty revisions
* Models match migrations
* No schema drift
* Env-based DB URLs

Alembic autogenerate must be validated before merge.

---

# 10. Observability & Logging

Structured logs required for:

* Authentication events
* Role changes
* Moderation actions
* Thread creation
* Notification delivery

Logs must include actor_id + entity references.

---

# 11. Testing Requirements

Agents must generate tests for:

* Auth & RBAC
* Moderation flows
* Notifications
* Realtime delivery
* Cache invalidation

Both unit and integration coverage required.

---

# 12. DevOps & CI

Agents must ensure:

* Dockerized services
* Redis + DB compose setup
* Migration checks in CI
* Test execution in pipelines

---

# 13. Repo Hygiene

Required `.gitignore` coverage:

```
.env
*.db
__pycache__/
.pytest_cache/
.venv/
node_modules/
```

No binaries or secrets allowed.

---

# 14. Agent Execution Rules

When generating code, agents must:

1. Read AGENTS.md first.
2. Follow architecture strictly.
3. Implement DB + realtime hybrid notifications.
4. Enforce RBAC everywhere.
5. Add cache invalidation.
6. Generate migrations & tests.

If conflicts arise → AGENTS.md overrides defaults.

---

**End of AGENTS.md**
