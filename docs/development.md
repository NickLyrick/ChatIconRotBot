# Development

## Checks

Install the development tools (pinned to the versions CI uses) and run the same
checks as CI:

```bash
pip install -r requirements-dev.txt
pylint src           # rules live in .pylintrc
pytest --cov         # tests with coverage; settings in pytest.ini and .coveragerc
```

The tests need no database or Telegram access:
[`conftest.py`](https://github.com/NickLyrick/ChatIconRotBot/blob/master/conftest.py)
sets placeholder `TOKEN` and `DATABASE_URL` values.

## Documentation

The site is built with [MkDocs](https://www.mkdocs.org/) and
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/). Pages live
in `docs/`, the configuration in `mkdocs.yml`. The
[API reference](reference/index.md) is generated from the docstrings by
[mkdocstrings](https://mkdocstrings.github.io/), so documenting a function is
enough to have it on the site.

```bash
pip install -r requirements-docs.txt
mkdocs serve         # live preview at http://127.0.0.1:8000
mkdocs build         # strict build into site/, as in CI
```

Docstrings use the Sphinx style (`:param x:`, `:return:`). A new module shows
up in the reference once it is added to the matching page in `docs/reference/`.

## Project layout

```text
main.py                      entry point: webhook server, or long polling locally
src/release.py               once-per-deploy tasks (Fly release_command)
src/web/app.py               aiohttp app: /webhook, /jobs/tick, /health
src/bot/                     bot instance, settings, command descriptions, start announcement
src/dispatcher/              dispatcher, router and middleware registration
src/handlers/                message and callback handlers
  basic_handlers.py            /start in private chats, /help, global error handler
  records_handlers.py          trophy submission and deletion
  schedule_handlers.py         /start in groups, /set_date, /set_delta, /set_timezone, /show_settings
  settings_menu_handlers.py    /settings button menu
  tables_handlers.py           /show_queue, /top, /history
  game_score_handlers.py       inline survey flow
  wiki_handlers.py             /games_info
src/keyboards/inline/        survey and settings menu keyboards, callback data
src/filters/                 caption format, chat type and permission filters
src/middleware/              inject the DB request object
src/scheduler/               scheduled jobs
  runner.py                    decides what is due and claims it in the database
  jobs.py                      change_avatar, finish_survey
src/database/                SQLAlchemy models and all queries
  alembic/                     migration environment and revisions
src/utility/                 PlatinumRecord model, table messages, schedule and time zone helpers
src/data/quotations.yaml     random quotes posted on submission
docs/                        this documentation site (MkDocs)
tests/                       pytest suite
```
