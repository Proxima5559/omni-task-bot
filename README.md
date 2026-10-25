# Omni-Channel Task Manager

Create tasks from a **Telegram bot** (text or voice) and manage them on a **real-time web dashboard**.

Voice messages are transcribed asynchronously: the bot answers instantly with "transcribing…", a worker turns the audio into text in the background, and the task appears on the dashboard the moment it is ready — no page refresh.

> This repository has two more READMEs with the details:
> - [`backend/README.md`](backend/README.md) — API, bot, worker, database, configuration
> - [`frontend/README.md`](frontend/README.md) — Vue dashboard

## Features

- Telegram bot: text messages become tasks, voice messages are transcribed (Gemini) and become tasks
- Inline buttons in Telegram to change task status; `/tasks` and `/delete` commands
- Dashboard with **Board (Kanban)** and **List** views
- Status toggles: Pending → In progress → Completed
- Live updates over WebSocket (tasks created by the bot show up instantly)
- Resilient voice processing: retries with backoff for temporary errors, clear failure messages to the user
- Fully containerised with `docker-compose.yml`

## Architecture

```
 Telegram ──► Bot (aiogram) ─┐
                             ├─► FastAPI ──► PostgreSQL   (tasks, users)
 Dashboard (Vue) ◄─ REST ────┘      │
        ▲                           ├─► Redis queue ──► Celery worker ──► Gemini (speech-to-text)
        └──── WebSocket ◄── Redis pub/sub ◄───────────────┘
```

| Part | Tech |
|---|---|
| Backend API | FastAPI, SQLAlchemy (async), Alembic, Pydantic |
| Bot | aiogram 3 |
| Queue / worker | Redis + Celery (queues: `transcription`, `notifications`) |
| Real-time | Redis pub/sub → WebSocket (`/ws/tasks`) |
| Database | PostgreSQL |
| Transcription | Google Gemini (`google-genai`) |
| Frontend | Vue 3, TypeScript, Vite, Pinia, Axios, Bulma |
| Packaging | `uv` (backend), `npm` (frontend), Docker Compose |

## Project structure

```
.
├── docker-compose.yml
├── .env                 # your secrets (not committed)
├── backend/             # FastAPI + bot + Celery worker   → see backend/README.md
└── frontend/            # Vue dashboard                    → see frontend/README.md
```

## Prerequisites

- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/) (or set `TRANSCRIBER=fake` to test without one)
- Either **Docker**, or: Python ≥ 3.14 with [`uv`](https://docs.astral.sh/uv/), Node.js 22+, PostgreSQL and Redis

## Configuration

Create a `.env` file in the project root:

```env
# Telegram
TELEGRAM_BOT_TOKEN=123456:your-token
TELEGRAM_MODE=polling

# Voice transcription
TRANSCRIBER=gemini            # gemini | fake (fake needs no API key)
GEMINI_API_KEY=your-key

# Only needed for the manual (non-Docker) setup
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tasks
REDIS_URL=redis://localhost:6379/0

# Only used by docker-compose
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=tasks
```

The full list of variables is in [`backend/README.md`](backend/README.md#configuration).

## How to run

### Option A — Docker

```bash
docker compose up --build
```

- Dashboard: http://localhost:8080
- API: http://localhost:8000 (interactive docs at `/docs`)

This starts PostgreSQL, Redis, the API (which also runs the bot in polling mode), the Celery worker and the frontend.

### Option B — Manually (no Docker)

You need PostgreSQL and Redis running and reachable through the URLs in `.env`. Then use **three terminals**:

```bash
# 1) API + Telegram bot
cd backend
uv sync
uv run alembic upgrade head
uv run python main.py

# 2) Worker (voice transcription + Telegram notifications)
cd backend
uv run celery -A app.worker.celery_app.celery_app worker -Q transcription,notifications -l info
#   on Windows add:  --pool=solo

# 3) Dashboard
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

Details, troubleshooting and the extra commands (seed data, etc.) are in the [backend](backend/README.md) and [frontend](frontend/README.md) READMEs.

## Using it

1. Open your bot in Telegram and send `/start`.
2. Send a text message → a task is created. Send a voice message → the bot replies "transcribing…" and edits that message when the text is ready.
3. Watch the dashboard: tasks appear live, and you can change their status with the toggle buttons (also possible from the bot's inline buttons).

Bot commands: `/start`, `/tasks`, `/delete last`, `/delete all`.
