# Database

## Schema

| Table | Purpose |
| --- | --- |
| `chats` | Registered chats: next rotation date, interval in days, time zone, last published survey month |
| `platinum` | Pending queue of submitted trophies (hunter, game, platform, photo) |
| `history` | Archive of shown trophies, including the date the avatar was set |
| `scores` | Individual survey votes per trophy and user |
| `surveys` | Aggregated monthly results per trophy |

The models are documented in [`src.database.schemas`](reference/database.md#src.database.schemas),
the queries in [`src.database.connect`](reference/database.md#src.database.connect).

## Migrations

The schema is managed with [Alembic](https://alembic.sqlalchemy.org/). The
models in `src/database/schemas.py` are the source of truth; every schema change
ships as a revision in
[`src/database/alembic/versions/`](https://github.com/NickLyrick/ChatIconRotBot/tree/master/src/database/alembic/versions).

```bash
export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
export TOKEN=123456:dummy   # importing the models builds the Bot; any well-formed token works

alembic upgrade head                              # bring a database up to date
alembic revision --autogenerate -m "add x to y"   # create a revision, then review it
alembic check                                     # models and database must match
```

On Fly, `release_command` in
[`fly.toml`](https://github.com/NickLyrick/ChatIconRotBot/blob/master/fly.toml) runs
[`src/release.py`](reference/release.md), which applies the migrations once per
deploy, before the new version starts. CI applies all revisions to an
empty Postgres 14 and runs `alembic check`.

The first revision (`bbd72dbf4178`, baseline) describes the schema that existed
before Alembic. Databases created before it are marked once with
`alembic stamp bbd72dbf4178` instead of being migrated.

See [`src/database/alembic/README`](https://github.com/NickLyrick/ChatIconRotBot/blob/master/src/database/alembic/README)
for the workflow.
