# Setup

## Requirements

- Python 3.14
- PostgreSQL

No system packages are needed: tables are sent as native Telegram tables.

## Configuration

The bot is configured entirely through environment variables:

| Variable | Description |
| --- | --- |
| `TOKEN` | Telegram Bot API token from [@BotFather](https://t.me/BotFather) |
| `DATABASE_URL` | Async SQLAlchemy DSN, e.g. `postgresql+asyncpg://user:pass@host:5432/db` |
| `WEBHOOK_BASE_URL` | Public base URL, e.g. `https://platinum.fly.dev`. Unset → long polling |
| `WEBHOOK_SECRET` | Secret Telegram sends with every update; required with `WEBHOOK_BASE_URL` |
| `JOBS_SECRET` | Bearer token the external cron sends to `POST /jobs/tick` |
| `PORT` | HTTP port of the webhook server, default `8080` |

Bot administrator IDs are currently hardcoded in
[`src/bot/settings.py`](reference/bot.md#src.bot.settings) (`admin_ids`); change them there.
Admins receive a notice on every deploy (on every start in polling mode) and
every unhandled error traceback.

The bot must be an administrator in the group with permission to change chat
info and pin messages.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/NickLyrick/ChatIconRotBot.git
    cd ChatIconRotBot
    ```

2. Create a virtual environment and install the dependencies:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3. Provide the environment variables and run:

    ```bash
    export TOKEN="123456:ABC-DEF..."
    export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    alembic upgrade head
    python main.py
    ```

Without `WEBHOOK_BASE_URL` the bot uses long polling and runs the scheduled
jobs itself once a minute.

!!! warning
    Starting the bot deletes its webhook, so use a separate test bot locally,
    never the production token.

## Docker

```bash
docker build -t chaticonrotbot .
docker run --rm -e TOKEN=... -e DATABASE_URL=... chaticonrotbot python main.py
```

## Dev container

The repository ships a VS Code dev container
([`.devcontainer/`](https://github.com/NickLyrick/ChatIconRotBot/tree/master/.devcontainer))
with Python 3.14 and a PostgreSQL service, so you can open the project in a
container and get a local database for free.
