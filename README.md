# ChatIconRotBot

A Telegram bot for communities of trophy hunters. It collects platinum-trophy
screenshots posted by chat members, rotates them as the group chat avatar on a
schedule, and runs a monthly rating survey on the games that were shown.

Built with [aiogram 3](https://docs.aiogram.dev/) (async), APScheduler,
SQLAlchemy 2.0 + PostgreSQL. All bot messages are in Russian.

## How it works

1. **Submit a trophy.** A member posts a photo captioned `@YourBotName Game Title`
   (append `Xbox` for the Xbox platform, otherwise PlayStation is assumed).
   The bot stores it in the chat's queue and replies with a random gaming quote
   from [`src/data/quotations.yaml`](src/data/quotations.yaml).
2. **Rotate the avatar.** Every `delta` days a scheduled job takes the next entry
   from the queue, sets it as the chat photo, posts and pins an announcement with
   the hunter and the game, then removes the entry from the queue and moves the
   history record forward. If the queue is empty, the chat's default avatar is
   used instead.
3. **Rate the game.** The pinned announcement carries an inline *«Оценить»*
   button that opens a private survey with the bot. Members score the game on
   three axes from 1 to 10 — *Game*, *Picture*, *Difficulty*. The hunter who
   submitted the trophy only scores *Difficulty*.
4. **Monthly results.** On the 1st of each month the bot aggregates the previous
   month's scores, renders one table image per category, sends them as an album
   and pins it.

## Commands

### Everyone

| Command | Description |
| --- | --- |
| `/start` | Start the bot in the chat (registers the chat and its schedule) |
| `/help` | Show the command reference |
| `/show_queue` | Show the queue of pending trophies as a table image |
| `/delete_game` | Delete your most recently submitted trophy |
| `/history [@username]` | List all trophies of yourself or another user |
| `/top [dd.mm.yyyy]` | Trophy leaderboard, all-time or since the given date |
| `/games_info` | Wikipedia links for the games currently in the queue |

### Chat owner / bot admins

| Command | Description |
| --- | --- |
| `/show_settings` | Show the next rotation date, the interval and the default avatar |
| `/set_date DD/MM/YYYY HH:MM` | Set the next avatar rotation (UTC) |
| `/set_delta N` | Set the interval between rotations, in days |

Posting a photo captioned `@YourBotName *Default*` as a user with
*change group info* rights sets the chat's fallback avatar, used whenever the
queue runs dry.

## Requirements

- Python 3.12
- PostgreSQL
- System packages for table rendering: `poppler-utils`, `pango`, and a font with
  Cyrillic coverage (the Docker image installs `font-noto`)

## Configuration

The bot is configured entirely through environment variables:

| Variable | Description |
| --- | --- |
| `TOKEN` | Telegram Bot API token from [@BotFather](https://t.me/BotFather) |
| `DATABASE_URL` | Async SQLAlchemy DSN, e.g. `postgresql+asyncpg://user:pass@host:5432/db` |

Bot administrator IDs are currently hardcoded in
[`src/bot/settings.py`](src/bot/settings.py) (`admin_ids`) — change them there.
Admins receive startup/shutdown notices and every unhandled error traceback.

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

3. Install the native dependencies (Debian/Ubuntu):

   ```bash
   sudo apt-get install poppler-utils libpango-1.0-0 fonts-noto
   ```

4. Provide the environment variables and run:

   ```bash
   export TOKEN="123456:ABC-DEF..."
   export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
   python main.py
   ```

> **Note:** the database schema is not created automatically. Create the tables
> described in [`src/database/schemas.py`](src/database/schemas.py) (`chats`,
> `platinum`, `history`, `scores`, `surveys`) before the first run.

### Docker

```bash
docker build -t chaticonrotbot .
docker run --rm -e TOKEN=... -e DATABASE_URL=... chaticonrotbot python main.py
```

### Dev container

The repository ships a VS Code dev container
([`.devcontainer/`](.devcontainer/)) with Python 3.12 and a PostgreSQL service,
so you can open the project in a container and get a local database for free.

## Project layout

```
main.py                      entry point: starts long polling
src/bot/                     bot instance, settings, command descriptions
src/dispatcher/              dispatcher, router and middleware registration
src/handlers/                message and callback handlers
  basic_handlers.py            /start, /help, global error handler
  records_handlers.py          trophy submission and deletion
  schedule_handlers.py         /set_date, /set_delta, /show_settings
  tables_handlers.py           /show_queue, /top, /history
  game_score_handlers.py       inline survey flow
  wiki_handlers.py             /games_info
src/keyboards/inline/        survey keyboards and callback data
src/filters/                 caption format, chat type and permission filters
src/middleware/              inject the DB request object and the scheduler
src/scheduler/               APScheduler wrapper and jobs
  jobs.py                      change_avatar, finish_survey, check_db_connection
src/database/                SQLAlchemy models and all queries
  alembic/                     migration environment and revisions
src/utility/                 PlatinumRecord model, HTML → PNG table renderer
src/data/quotations.yaml     random quotes posted on submission
```

Table images are produced by rendering a pandas DataFrame to HTML, converting it
to PDF with WeasyPrint, rasterising it with pdf2image, and trimming the result
with Pillow — see [`src/utility/tools.py`](src/utility/tools.py).

## Database schema

| Table | Purpose |
| --- | --- |
| `chats` | Registered chats: next rotation date and interval in days |
| `platinum` | Pending queue of submitted trophies (hunter, game, platform, photo) |
| `history` | Archive of shown trophies, including the date the avatar was set |
| `scores` | Individual survey votes per trophy and user |
| `surveys` | Aggregated monthly results per trophy |

## Database migrations

The schema is managed with [Alembic](https://alembic.sqlalchemy.org/). The
models in [`src/database/schemas.py`](src/database/schemas.py) are the source of
truth; every schema change ships as a revision in
[`src/database/alembic/versions/`](src/database/alembic/versions/).

```bash
export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
export TOKEN=123456:dummy   # importing the models builds the Bot; any well-formed token works

alembic upgrade head                              # bring a database up to date
alembic revision --autogenerate -m "add x to y"   # create a revision, then review it
alembic check                                     # models and database must match
```

On Fly, `release_command` in [`fly.toml`](fly.toml) runs `alembic upgrade head`
once per deploy, before the new version starts. CI applies all revisions to an
empty Postgres 14 and runs `alembic check`.

The first revision (`bbd72dbf4178`, baseline) describes the schema that existed
before Alembic. Databases created before it are marked once with
`alembic stamp bbd72dbf4178` instead of being migrated.

See [`src/database/alembic/README`](src/database/alembic/README) for the workflow.

## Deployment

Deployment targets [Fly.io](https://fly.io) via GitHub Actions:

- **`master`** → deploys the `platinum` app ([`.github/workflows/fly.yml`](.github/workflows/fly.yml))
- **`stage`** → deploys the `platinum-dev` app ([`.github/workflows/stage.yml`](.github/workflows/stage.yml))
- **any other branch** → runs `pylint src` only ([`.github/workflows/dev.yml`](.github/workflows/dev.yml))

Deploys require the `FLY_API_TOKEN` repository secret. `TOKEN` and
`DATABASE_URL` are expected to be set as Fly secrets. A `Procfile` is included
for Heroku-style platforms.

## Development

Lint the codebase the same way CI does:

```bash
pip install pylint
pylint src
```

Rules live in [`.pylintrc`](.pylintrc).
