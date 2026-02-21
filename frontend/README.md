# Discussion Forum Frontend

## Setup

### Install dependencies
```bash
npm install
```

### Start development server
```bash
npm run dev
```

Server runs at `http://localhost:3001`

### Build for production
```bash
npm run build
```

## Environment Variables

See `.env.example` for required variables:
- `VITE_API_URL` - Backend API endpoint (default: http://localhost:8000/api/v1)
- `VITE_WS_URL` - WebSocket endpoint (default: ws://localhost:8000/api/v1)

## Architecture

### Folder Structure

```text
src/
+-- components/
¦   +-- common/         # Shared presentational modules
¦   +-- layout/         # Header/Footer/Sidebar modules
¦   +-- thread/         # Thread UI modules
¦   +-- comment/        # Comment UI modules
¦   +-- notification/   # Notification UI modules
+-- context/            # React Context state providers
+-- layouts/            # Page shells
+-- pages/
¦   +-- auth/           # Authentication pages
¦   +-- thread/         # Thread route pages
¦   +-- dashboard/      # Role dashboards
+-- routes/             # Route guards
+-- services/           # API and websocket service layer
+-- styles/             # Global styling
+-- utils/              # Utility helpers
+-- App.jsx
+-- main.jsx
```

### Module Docs

- `src/components/README.md`
- `src/pages/README.md`

### State Management

Uses React Context API for centralized state:
- **AuthContext** - User authentication, tokens, permissions
- **ThreadsContext** - Threads list, current thread, comments tree
- **NotificationsContext** - Notifications, unread count

### API Integration

All API calls go through `src/services/`:
- `apiClient.js` - Axios instance with auth/refresh handling
- `index.js` - Domain service methods (auth, threads, comments, etc.)

### Real-Time

WebSocket manager in `src/services/websocket.js`:
- Auto-reconnect with backoff
- Event listener registry
- Shared connection management
