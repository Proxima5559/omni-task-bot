# Backend

FastAPI REST API + WebSocket, Telegram bot (aiogram), and a Celery worker for voice transcription. Part of the [Omni-Channel Task Manager](../README.md).

## How it works

1. **Text message** → the bot creates a task straight away.
2. **Voice message** → the bot validates it (max duration / size), replies *"transcribing…"* immediately, saves a placeholder task and pushes a job to the Redis `transcription` queue.
3. The **worker** downloads the audio from Telegram, sends it to Gemini and saves the text. A second job on the `notifications` queue edits the bot's message with the result.
4. Every create/update/delete is published to Redis pub/sub; the API forwards it through **`/ws/tasks`** to all open dashboards.

### Error handling for voice processing

- **Temporary errors** (network issues, 429, 5xx) → retried with exponential backoff, up to `TRANSCRIPTION_MAX_RETRIES`.
- **Permanent errors** (no speech, bad audio, missing API key) → fail fast; the task is marked `failed` and the user gets a clear message.
- Unexpected exceptions never leave a task stuck in "transcribing": it is always marked `done` or `failed`.
- Jobs are idempotent (a duplicate delivery does not process the same task twice) and acknowledged late, so a crashed worker's job is redelivered.
- Publishing events to Redis never breaks the main request: failures are logged and ignored.

## Structure

```
backend/
├── main.py                  # entry point: `uv run python main.py`
├── pyproject.toml / uv.lock
├── alembic.ini, alembic/    # migrations
├── seed/                    # seed.py / unseed.py (demo data)
└── app/
    ├── app_p.py             # FastAPI app factory + lifespan
    ├── config.py            # settings (Pydantic BaseSettings, reads .env)
    ├── database.py          # async engine (API/bot) + sync engine (worker)
    ├── redis_client.py
    ├── models/              # SQLAlchemy: Task, User
    ├── schemas/             # Pydantic request/response schemas
    ├── repositories/        # DB access (CRUD)
    ├── services/            # business logic: tasks, voice intake, events,
    │                        #   transcription (Gemini), Telegram HTTP client
    ├── api/                 # tasks (REST), ws (WebSocket), bot (webhook), /health
    ├── bot/                 # aiogram handlers, keyboards, lifecycle
    ├── worker/              # Celery app + tasks (transcribe_voice, notify_user)
    └── utils/               # errors, logging, formatting
```

## Requirements

- Python ≥ 3.14 and [`uv`](https://docs.astral.sh/uv/)
- PostgreSQL and Redis (or just Docker — see the [root README](../README.md))
- A Telegram bot token and a Gemini API key (or `TRANSCRIBER=fake`)

## Configuration

Settings are read from environment variables or a `.env` file (`../.env` or `./.env`).

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/tasks` | Async Postgres URL (the worker derives a sync one automatically) |
| `REDIS_URL` | `redis://localhost:6379/0` | Queue broker + pub/sub |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | JSON list of allowed origins |
| `TELEGRAM_BOT_TOKEN` | – | Bot token from @BotFather |
| `TELEGRAM_MODE` | `polling` | `polling` (dev) or `webhook` (production) |
| `TELEGRAM_WEBHOOK_URL` | – | Public HTTPS URL of `/api/bot/webhook` (webhook mode) |
| `TELEGRAM_WEBHOOK_SECRET` | – | Secret token checked on webhook requests |
| `TRANSCRIBER` | `gemini` | `gemini` or `fake` (returns a dummy text, no key needed) |
| `GEMINI_API_KEY` | – | Google Gemini API key |
| `WHISPER_MODEL` | `gemini-3.8-flash` | Model name used for transcription |
| `VOICE_MAX_DURATION_SEC` | `120` | Longer voice messages are rejected |
| `VOICE_MAX_FILE_MB` | `20` | Bigger voice files are rejected |
| `TRANSCRIPTION_MAX_RETRIES` | `3` | Retries for temporary errors |
| `TRANSCRIPTION_TIMEOUT_SEC` | `60` | Timeout per transcription attempt |
| `DEBUG` | `false` | `true` enables auto-reload in `main.py` |
| `LOG_LEVEL` | `INFO` | Logging level |

## Run (without Docker)

```bash
cd backend
uv sync                          # install dependencies
uv run alembic upgrade head      # create / update the database schema
uv run python main.py            # API on http://localhost:8000
```

In a second terminal, start the worker (needed for voice messages and bot notifications):

```bash
cd backend
uv run celery -A app.worker.celery_app.celery_app worker -Q transcription,notifications -l info
```

> On **Windows** add `--pool=solo` to the Celery command.

In `polling` mode (default) the **bot runs inside the API process** — there is nothing else to start. Don't also run `python -m app.bot` at the same time: two pollers on one token conflict.

Check it is alive: http://localhost:8000/health → `{"status":"ok"}`. Interactive API docs: http://localhost:8000/docs.

### Webhook mode (production)

Set `TELEGRAM_MODE=webhook`, `TELEGRAM_WEBHOOK_URL=https://your-domain/api/bot/webhook` and a `TELEGRAM_WEBHOOK_SECRET`. The API registers the webhook on startup.

## Run with Docker

From the project root:

```bash
docker compose up --build
```

The API container runs `alembic upgrade head` before starting. See the [root README](../README.md).

## Demo data

```bash
uv run python -m seed.seed       # inserts a demo user and 3 tasks
uv run python -m seed.unseed     # drops the tables and the Alembic history (full reset!)
```

After `unseed`, run `uv run alembic upgrade head` to recreate the schema.

## Database migrations

```bash
uv run alembic upgrade head                              # apply
uv run alembic revision --autogenerate -m "message"      # create a new migration after changing models
uv run alembic downgrade -1                              # roll back one step
```

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | DB + Redis health check |
| `GET` | `/api/tasks` | List tasks (`?status=`, `limit`, `offset`) |
| `POST` | `/api/tasks` | Create a task `{ "title": "...", "description": "..." }` |
| `GET` | `/api/tasks/{id}` | Get one task |
| `PATCH` | `/api/tasks/{id}` | Update title / description / status |
| `PATCH` | `/api/tasks/{id}/status` | Change status: `pending`, `in_progress`, `completed` |
| `DELETE` | `/api/tasks/{id}` | Delete a task |
| `WS` | `/ws/tasks` | Live events: `task.created`, `task.updated`, `task.deleted` |
| `POST` | `/api/bot/webhook` | Telegram webhook (webhook mode only) |

WebSocket message format:

```json
{ "type": "task.updated", "task": { "id": 1, "title": "...", "status": "in_progress", "source": "voice", "transcription_status": "done", "...": "..." } }
```

## Bot commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/tasks` | Your latest tasks, with status buttons |
| `/delete last` | Delete your most recent task |
| `/delete all` | Delete all your tasks |
| *text message* | Creates a task |
| *voice message* | Transcribed, then creates a task |

## Troubleshooting

- **Voice stays on "transcribing…"** — the worker isn't running, or Redis isn't reachable from it.
- **`GEMINI_API_KEY is not configured`** — set the key, or use `TRANSCRIBER=fake` to test the pipeline.
- **Dashboard shows "Offline"** — the API isn't running or the WebSocket can't connect.
- **Bot doesn't answer / `Conflict: terminated by other getUpdates`** — another process is polling with the same token.
- **Celery crashes on Windows** — add `--pool=solo`.
