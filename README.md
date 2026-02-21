# Advanced Real-Time Discussion Forum

## Project Overview
Advanced Real-Time Discussion Forum is a full-stack discussion platform with a FastAPI backend and a React frontend. It supports authentication, role-based access control, moderation workflows, real-time updates, and notifications.

## Features
- User registration, login, token refresh, and password change
- JWT-based authenticated APIs
- Role-based authorization (`ADMIN`, `MODERATOR`, `MEMBER`)
- Thread CRUD with soft delete
- Comment and reply support with soft delete
- Likes on threads and comments
- Mentions and notifications
- Moderation review and reporting flow
- WebSocket endpoint for real-time events
- Search for threads
- Automated backend tests with coverage enforcement

## Tech Stack
### Frontend
- JavaScript (ES6+)
- React 18
- Vite
- React Router
- Axios

### Backend
- Python 3.11
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- JWT (`python-jose`) + `bcrypt` password hashing
- Pytest + pytest-cov

### Infrastructure
- Docker
- Docker Compose
- Nginx (in Docker Compose setup)

## Installation
### Prerequisites
- Node.js 20+
- Python 3.11+
- PostgreSQL
- Redis

### 1. Clone repository
```bash
git clone <your-repo-url>
cd discussion-forum
```

### 2. Backend setup
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
# Windows
copy .env.example .env
# macOS/Linux
# cp .env.example .env
```

### 3. Frontend setup
```bash
cd ../frontend
npm install
# Windows
copy .env.example .env
# macOS/Linux
# cp .env.example .env
```

## Usage
### Run backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run frontend
```bash
cd frontend
npm run dev
```

### Run with Docker Compose
```bash
docker compose up --build
```

### API docs
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Run backend tests
```bash
cd backend
pytest
```

`pytest` is configured to run coverage and fail if total coverage drops below the configured threshold.

## Project Structure
```text
discussion-forum/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── dependencies/
│   │   ├── integrations/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── websocket/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── docker/
│   └── docker-compose.yml (deprecated shim)
├── nginx/
├── docker-compose.yml
└── README.md
```

## Environment Variables
### Backend (`backend/.env`)
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: JWT signing key
- `REDIS_URL`: Redis connection string
- `BOOTSTRAP_ADMIN_EMAIL`: bootstrap admin email
- `BOOTSTRAP_ADMIN_PASSWORD`: bootstrap admin password
- `BOOTSTRAP_ADMIN_NAME`: bootstrap admin display name

Use `backend/.env.example` as the reference template.

### Frontend (`frontend/.env`)
- `VITE_API_URL`: backend API base URL (example: `http://localhost:8000/api/v1`)
- `VITE_WS_URL`: backend WebSocket base URL (example: `ws://localhost:8000/api/v1`)

Use `frontend/.env.example` as the reference template.

## Authentication
- Access and refresh tokens are issued from `/api/v1/auth/login`.
- Protected endpoints require `Authorization: Bearer <access_token>`.
- Access token refresh is available at `/api/v1/auth/refresh`.
- Current user profile endpoints are available under `/api/v1/auth/me` and `/api/v1/users/me`.

## Database Info
- Primary database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic (`backend/app/db/migrations`)
- Core domain tables include users, roles, threads, comments, likes, notifications, mentions, and moderation reviews.
- Redis is used for pub/sub and cache-related flows.

## Contributing
1. Create a feature branch.
2. Make focused changes.
3. Add or update tests.
4. Run `pytest` in `backend/` and verify frontend build/lint where relevant.
5. Open a pull request with a clear summary.

## License
This repository currently does not include a `LICENSE` file.
