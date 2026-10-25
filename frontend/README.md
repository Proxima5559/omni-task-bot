# Frontend

Real-time task dashboard built with **Vue 3 + TypeScript + Vite**, **Pinia** for state, **Axios** for the API and **Bulma** for styling (dark teal theme). Part of the [Omni-Channel Task Manager](../README.md).

## Features

- **Board (Kanban)** and **List** views — your choice is remembered
- Status toggle on every task: Pending / In progress / Completed (updates instantly, rolls back if the server rejects it)
- **Live updates** via WebSocket: tasks created by the Telegram bot appear immediately, with a short highlight
- Voice tasks show a *"Transcribing voice message…"* spinner and switch to the text when ready; failed transcriptions show the reason
- Quick-add form, delete button, status counters
- Connection indicator in the navbar (Live / Connecting / Offline) with automatic reconnect and re-sync

## Structure

```
frontend/
├── index.html
├── vite.config.ts            # dev server + proxy for /api and /ws
├── package.json
└── src/
    ├── main.ts, App.vue
    ├── types.ts              # Task types and statuses
    ├── api/                  # Axios client + tasks API
    ├── stores/               # Pinia store: tasks + WebSocket connection
    ├── views/                # DashboardView
    ├── components/           # AppNavbar, TaskForm, TaskBoard, TaskColumn,
    │                         #   TaskCard, TaskList, StatusToggle
    ├── styles/               # theme.css (colour variables), app.css
    └── utils/                # time formatting
```

## Requirements

- Node.js 22+
- The backend running on `http://localhost:8000` (see [`../backend/README.md`](../backend/README.md))

## Run

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

In dev mode Vite proxies `/api` and `/ws` to the backend, so no extra CORS setup is needed.

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Dev server with hot reload (port 5173) |
| `npm run build` | Type-check (`vue-tsc`) and build to `dist/` |
| `npm run preview` | Serve the production build locally |

## Configuration

Optional variables in `frontend/.env`:

| Variable | Example | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api` | REST base URL (default: same-origin `/api`) |
| `VITE_WS_URL` | `ws://localhost:8000/ws/tasks` | WebSocket URL (default: same-origin `/ws/tasks`) |
| `VITE_BACKEND_URL` | `http://localhost:8000` | Where the Vite dev proxy points |

If `VITE_API_URL` points to another origin, that origin must be listed in the backend's `CORS_ORIGINS`.

## Docker

The frontend has its own `Dockerfile` (builds the app, serves it with nginx) and is started together with everything else from the project root:

```bash
docker compose up --build
```

Dashboard: http://localhost:8080

## How the live updates work

`src/stores/tasks.ts` loads the tasks over REST, then opens a WebSocket to `/ws/tasks`. Each event (`task.created`, `task.updated`, `task.deleted`) is merged into the store, so REST responses and WebSocket events never create duplicates. If the connection drops, the store reconnects with exponential backoff and reloads the list to catch anything it missed.
