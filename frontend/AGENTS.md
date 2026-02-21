# AGENTS.md — Frontend Implementation Governance (v2)

**Project:** Advanced Real-Time Discussion Forum
**Layer:** Frontend (React / JavaScript / Vite)

---

# 1. Agent Mission

You are implementing the frontend of a **scalable real-time discussion forum** that enables interactive collaboration between users.

Your goals:

* Build a production-grade UI from scratch
* Integrate all backend APIs
* Support real-time collaboration
* Render nested discussions efficiently
* Follow mentor & requirement constraints
* Maintain minimal dark professional design

Do not generate placeholder UI or incomplete integrations.

---

# 2. Tech Stack Contract

Use only:

| Layer      | Technology          |
| ---------- | ------------------- |
| Framework  | React               |
| Language   | JavaScript          |
| State      | Context API / Store |
| API Client | Axios               |
| Realtime   | WebSocket           |
| Routing    | React Router        |
| Styling    | CSS Modules         |
| Icons      | Lucide / Heroicons  |

Do not introduce Redux, Next.js, or other frameworks.

---

# 3. UI / UX Design System

## Theme

Minimal dark professional interface.

### Color Tokens

| Element        | Color   |
| -------------- | ------- |
| Background     | #0f172a |
| Card           | #111827 |
| Border         | #1f2937 |
| Primary Text   | #f9fafb |
| Secondary Text | #9ca3af |
| Accent         | #6366f1 |
| Success        | #10b981 |
| Error          | #ef4444 |

---

## Design Principles

* Minimal clutter
* High readability
* Soft shadows
* Rounded cards
* Consistent spacing
* Flat UI (no heavy gradients)

---

# 4. Layout Architecture

```
MainLayout
 ├── Header
 ├── Sidebar
 ├── Content
 └── Footer
```

Admin uses:

```
AdminLayout
```

Sidebar navigation is role-aware.

---

# 5. Routing Contract

Required routes:

```
/login
/register
/threads
/threads/:id
/dashboard/member
/dashboard/moderator
/dashboard/admin
```

Guards:

* ProtectedRoute
* RoleRoute

---

# 6. Authentication UX

Implement:

* Registration
* Login
* JWT token storage
* Token refresh handling
* Auto logout on expiry
* Password reset UI

Errors must be user-friendly.

---

# 7. User Profile Management

Frontend must support:

* Profile view
* Profile update
* Avatar upload preview
* Bio editing

Cache profile locally.

---

# 8. Thread System UI

Thread listing must include:

* Title
* Description preview
* Author
* Tags
* Likes
* Comment count
* Created time

Thread creation form includes:

* Title input
* Description editor
* Tag selector

Pagination mandatory.

---

# 9. Nested Comment Rendering (CRITICAL)

Must support:

* Multi-level nesting
* Recursive rendering
* Indentation hierarchy
* Reply editor per comment
* Collapse/expand threads
* Lazy loading replies

Avoid prop drilling via context/store.

---

# 10. Soft Delete UX Rules

## Deleted Comment

Render placeholder:

```
[ Comment deleted ]
```

Children replies remain visible.

---

## Deleted User

Replace name with:

```
User deleted
```

Threads/comments remain intact.

---

# 11. Like System UI

Features:

* Like/unlike toggle
* Live like count
* Optimistic UI updates
* One-like constraint handling

Realtime updates via WebSocket.

---

# 12. Real-Time Collaboration

WebSocket must reflect:

* New comments
* Replies
* Likes
* Notifications

Feed strategy:

Show activity banner:

```
New activity available — Refresh
```

Do not auto-inject content unless required.

---

# 13. Notification System UI

Include:

* Bell icon
* Unread badge
* Dropdown panel
* Mention alerts
* Reply alerts
* Read/unread toggle

Realtime push required.

---

# 14. Search Interface

Support search by:

* Thread title
* Content
* Tags

Include:

* Search bar
* Filters
* Highlight matches
* Debounced queries

---

# 15. Role-Based Dashboards

## Member Dashboard

* Create threads
* Comment
* Like
* Notifications

---

## Moderator Dashboard

* Review queue
* Pending reviews
* Completed reviews
* Moderation actions

---

## Admin Dashboard

* Manage users
* Change roles
* Monitor moderation stats
* System activity overview

---

# 16. Pagination Strategy

Pagination must be:

* Backend-driven
* Consistent params
* Reusable hook/component

Used in:

* Threads
* Moderation lists
* Notifications (if paginated)

---

# 17. Frontend Caching Layer

Cache locally:

* User profile
* Thread lists
* Notifications
* Like counts

Avoid redundant API calls.

---

# 18. State Management Rules

Centralize state for:

* Auth session
* Threads
* Comment tree
* Notifications
* WebSocket events

Avoid deep prop drilling.

---

# 19. API Integration Rules

All calls go through:

```
src/services/
```

Never call Axios inside components.

Handle:

* Errors
* Retries
* Token expiry

---

# 20. WebSocket Client Rules

Implement:

* Connection manager
* Auto reconnect
* Event listeners
* User-scoped channels

---

# 21. Moderation UX Rules

Moderators must:

* View flagged content
* Take actions
* Mark reviews completed

Admins can override moderation decisions.

---

# 22. Performance Optimization

Optimize:

* Nested rendering
* Virtualized lists
* Memoized components
* Lazy loading

---

# 23. Accessibility

Ensure:

* Keyboard navigation
* Focus states
* Screen reader labels
* Color contrast compliance

---

# 24. Testing Expectations

Test:

* Auth flows
* Thread creation
* Nested comments
* Pagination
* Notifications

---

# 25. Definition of Done

A feature is complete only if:

* UI implemented
* API integrated
* State handled
* Permissions enforced
* Realtime wired
* Cached where needed
* Responsive UI verified

---

# 26. Requirement Coverage Mapping

Frontend must satisfy:

* JWT authentication UI
* Profile management
* Thread creation/listing
* Nested comments
* Likes
* Realtime updates
* Search filters
* Notifications
* Role dashboards
* Moderation tools

---

# End of AGENTS.md v2

This file governs all AI-generated frontend implementation and ensures compliance with project requirements and mentor expectations.
