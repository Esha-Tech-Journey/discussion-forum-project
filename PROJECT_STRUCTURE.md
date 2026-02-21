# Project Folder Structure

```text
discussion-forum
|-- backend
|   |-- app
|   |   |-- api
|   |   |   |-- v1
|   |   |   |   |-- auth.py
|   |   |   |   |-- comments.py
|   |   |   |   |-- likes.py
|   |   |   |   |-- moderation.py
|   |   |   |   |-- notifications.py
|   |   |   |   |-- router.py
|   |   |   |   |-- search.py
|   |   |   |   |-- threads.py
|   |   |   |   |-- users.py
|   |   |   |   \-- websocket.py
|   |   |   \-- deps.py
|   |   |-- core
|   |   |   |-- config.py
|   |   |   |-- constants.py
|   |   |   |-- exceptions.py
|   |   |   |-- logging.py
|   |   |   \-- security.py
|   |   |-- db
|   |   |   |-- migrations
|   |   |   |   |-- versions
|   |   |   |   |   |-- 53c06d30f18b_initial_schema.py
|   |   |   |   |   |-- 6e6371028572_add_threads_table.py
|   |   |   |   |   \-- ff04f9f90f51_add_audit_tags_moderation_updates.py
|   |   |   |   |-- env.py
|   |   |   |   |-- README
|   |   |   |   \-- script.py.mako
|   |   |   |-- base.py
|   |   |   |-- seed_roles.py
|   |   |   \-- session.py
|   |   |-- dependencies
|   |   |   |-- __init__.py
|   |   |   |-- auth.py
|   |   |   |-- permissions.py
|   |   |   \-- rate_limit.py
|   |   |-- integrations
|   |   |   |-- __init__.py
|   |   |   |-- email_service.py
|   |   |   \-- redis_client.py
|   |   |-- models
|   |   |   |-- __init__.py
|   |   |   |-- audit_log.py
|   |   |   |-- base.py
|   |   |   |-- comment.py
|   |   |   |-- like.py
|   |   |   |-- mention.py
|   |   |   |-- moderation.py
|   |   |   |-- notification.py
|   |   |   |-- role.py
|   |   |   |-- tag.py
|   |   |   |-- thread.py
|   |   |   |-- thread_tag.py
|   |   |   \-- user.py
|   |   |-- repositories
|   |   |   |-- __init__.py
|   |   |   |-- base.py
|   |   |   |-- comment.py
|   |   |   |-- like.py
|   |   |   |-- mention.py
|   |   |   |-- moderation.py
|   |   |   |-- notification.py
|   |   |   |-- role.py
|   |   |   |-- thread.py
|   |   |   \-- user.py
|   |   |-- schemas
|   |   |   |-- __init__.py
|   |   |   |-- auth.py
|   |   |   |-- base.py
|   |   |   |-- comment.py
|   |   |   |-- like.py
|   |   |   |-- mention.py
|   |   |   |-- moderation.py
|   |   |   |-- notification.py
|   |   |   |-- search.py
|   |   |   |-- thread.py
|   |   |   |-- user.py
|   |   |   \-- user_activity.py
|   |   |-- services
|   |   |   |-- __init__.py
|   |   |   |-- auth_service.py
|   |   |   |-- bootstrap_service.py
|   |   |   |-- comment_service.py
|   |   |   |-- like_service.py
|   |   |   |-- mention_service.py
|   |   |   |-- moderation_service.py
|   |   |   |-- notification_service.py
|   |   |   |-- search_service.py
|   |   |   |-- thread_service.py
|   |   |   \-- user_service.py
|   |   |-- utils
|   |   |   |-- __init__.py
|   |   |   |-- mention_parser.py
|   |   |   |-- pagination.py
|   |   |   \-- rate_limiter.py
|   |   |-- websocket
|   |   |   |-- __init__.py
|   |   |   |-- events.py
|   |   |   |-- handlers.py
|   |   |   |-- manager.py
|   |   |   \-- notifications_handler.py
|   |   \-- main.py
|   |-- tests
|   |   |-- integration
|   |   |   |-- test_api_core_flows.py
|   |   |   |-- test_auth.py
|   |   |   |-- test_notifications.py
|   |   |   |-- test_threads.py
|   |   |   |-- test_threads_users_api_extended.py
|   |   |   \-- test_websocket.py
|   |   |-- unit
|   |   |   |-- test_repositories
|   |   |   |   |-- test_repositories.py
|   |   |   |   \-- test_thread_user_repositories_extra.py
|   |   |   |-- test_services
|   |   |   |   |-- test_bootstrap_service.py
|   |   |   |   |-- test_mentions.py
|   |   |   |   |-- test_notification_service.py
|   |   |   |   |-- test_thread_service.py
|   |   |   |   |-- test_thread_service_coverage.py
|   |   |   |   \-- test_user_service_coverage.py
|   |   |   |-- test_api_websocket_endpoint.py
|   |   |   |-- test_core_dependencies_utils.py
|   |   |   \-- test_websocket_stack.py
|   |   |-- __init__.py
|   |   \-- conftest.py
|   |-- .env
|   |-- .env.example
|   |-- AGENTS.md
|   |-- alembic.ini
|   |-- Dockerfile
|   |-- pytest.ini
|   |-- requirements.txt
|   \-- requirements-dev.txt
|-- docker
|   \-- docker-compose.yml (deprecated shim)
|-- frontend
|   |-- public
|   |   |-- favicon.ico
|   |   \-- index.html
|   |-- src
|   |   |-- components
|   |   |   |-- comment
|   |   |   |   |-- Comment.jsx
|   |   |   |   |-- Comment.module.css
|   |   |   |   |-- CommentForm.jsx
|   |   |   |   |-- CommentForm.module.css
|   |   |   |   |-- CommentTree.jsx
|   |   |   |   |-- CommentTree.module.css
|   |   |   |   \-- index.js
|   |   |   |-- common
|   |   |   |   |-- ActivityBanner.jsx
|   |   |   |   |-- ActivityBanner.module.css
|   |   |   |   |-- index.js
|   |   |   |   |-- LikeButton.jsx
|   |   |   |   |-- LikeButton.module.css
|   |   |   |   |-- Pagination.jsx
|   |   |   |   |-- Pagination.module.css
|   |   |   |   |-- SearchBar.jsx
|   |   |   |   \-- SearchBar.module.css
|   |   |   |-- layout
|   |   |   |   |-- AdminSidebar.jsx
|   |   |   |   |-- AdminSidebar.module.css
|   |   |   |   |-- Footer.jsx
|   |   |   |   |-- Footer.module.css
|   |   |   |   |-- Header.jsx
|   |   |   |   |-- Header.module.css
|   |   |   |   |-- index.js
|   |   |   |   |-- Sidebar.jsx
|   |   |   |   \-- Sidebar.module.css
|   |   |   |-- notification
|   |   |   |   |-- index.js
|   |   |   |   |-- NotificationPanel.jsx
|   |   |   |   \-- NotificationPanel.module.css
|   |   |   |-- thread
|   |   |   |   |-- CreateThreadModal.jsx
|   |   |   |   |-- CreateThreadModal.module.css
|   |   |   |   |-- index.js
|   |   |   |   |-- ThreadCard.jsx
|   |   |   |   \-- ThreadCard.module.css
|   |   |   \-- README.md
|   |   |-- context
|   |   |   |-- AuthContext.jsx
|   |   |   |-- NotificationsContext.jsx
|   |   |   \-- ThreadsContext.jsx
|   |   |-- layouts
|   |   |   |-- AdminLayout.jsx
|   |   |   |-- AdminLayout.module.css
|   |   |   |-- MainLayout.jsx
|   |   |   \-- MainLayout.module.css
|   |   |-- pages
|   |   |   |-- auth
|   |   |   |   |-- ForgotPasswordPage.jsx
|   |   |   |   |-- ForgotPasswordPage.module.css
|   |   |   |   |-- LoginPage.jsx
|   |   |   |   |-- LoginPage.module.css
|   |   |   |   |-- RegisterPage.jsx
|   |   |   |   |-- RegisterPage.module.css
|   |   |   |   |-- ResetPasswordPage.jsx
|   |   |   |   \-- ResetPasswordPage.module.css
|   |   |   |-- dashboard
|   |   |   |   |-- AdminDashboard.jsx
|   |   |   |   |-- AdminDashboard.module.css
|   |   |   |   |-- AdminUserProfile.jsx
|   |   |   |   |-- AdminUserProfile.module.css
|   |   |   |   |-- MemberDashboard.jsx
|   |   |   |   |-- MemberDashboard.module.css
|   |   |   |   |-- ModeratorDashboard.jsx
|   |   |   |   \-- ModeratorDashboard.module.css
|   |   |   |-- thread
|   |   |   |   |-- ThreadDetailPage.jsx
|   |   |   |   |-- ThreadDetailPage.module.css
|   |   |   |   |-- ThreadsPage.jsx
|   |   |   |   \-- ThreadsPage.module.css
|   |   |   |-- NotFoundPage.jsx
|   |   |   |-- NotFoundPage.module.css
|   |   |   |-- README.md
|   |   |   |-- SearchPage.jsx
|   |   |   \-- SearchPage.module.css
|   |   |-- routes
|   |   |   \-- RouteGuards.jsx
|   |   |-- services
|   |   |   |-- apiClient.js
|   |   |   |-- index.js
|   |   |   \-- websocket.js
|   |   |-- styles
|   |   |   |-- global.css
|   |   |   \-- index.css
|   |   |-- utils
|   |   |   |-- datetime.js
|   |   |   |-- mentions.js
|   |   |   \-- mentions.jsx
|   |   |-- App.jsx
|   |   \-- main.jsx
|   |-- .env
|   |-- .env.example
|   |-- .eslintrc.json
|   |-- AGENTS.md
|   |-- Dockerfile
|   |-- index.html
|   |-- jsconfig.json
|   |-- package.json
|   |-- package-lock.json
|   |-- README.md
|   \-- vite.config.js
|-- nginx
|   \-- nginx.conf
|-- .env.example
|-- .gitignore
|-- docker-compose.yml
|-- frontend_restore.zip
|-- PROJECT_STRUCTURE.md
\-- README.md
```

