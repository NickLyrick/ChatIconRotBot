# Deployment

Deployment targets [Fly.io](https://fly.io) via GitHub Actions:

| Branch | What runs |
| --- | --- |
| `master` | Checks, then deploy of the `platinum` app ([`fly.yml`](https://github.com/NickLyrick/ChatIconRotBot/blob/master/.github/workflows/fly.yml)) |
| `stage` | Checks, then deploy of the `platinum-dev` app ([`stage.yml`](https://github.com/NickLyrick/ChatIconRotBot/blob/master/.github/workflows/stage.yml)) |
| any other | Checks only ([`dev.yml`](https://github.com/NickLyrick/ChatIconRotBot/blob/master/.github/workflows/dev.yml)) |

The checks ([`checks.yml`](https://github.com/NickLyrick/ChatIconRotBot/blob/master/.github/workflows/checks.yml))
are three jobs: Pylint, Tests (results and coverage tables in the run summary)
and Migrations (upgrade, `alembic check`, downgrade and upgrade again on
Postgres 14). A deploy starts only if all three pass.

Deploys require the `FLY_API_TOKEN` repository secret. `TOKEN`, `DATABASE_URL`,
`WEBHOOK_BASE_URL`, `WEBHOOK_SECRET` and `JOBS_SECRET` are expected to be set
as Fly secrets (each app has its own values). A `Procfile` is included for
Heroku-style platforms.

The app receives updates over a webhook, and the Fly proxy suspends the machine
when it is idle and wakes it on the next request. Run a single machine
(`fly scale count 1`). Each deploy, [`src/release.py`](reference/release.md)
applies the migrations, registers the webhook and publishes the command lists.

## Scheduled jobs

There is no scheduler inside the process: a sleeping machine could not run it.
An external cron ([cron-job.org](https://cron-job.org)) calls

```http
POST https://<app>.fly.dev/jobs/tick
Authorization: Bearer <JOBS_SECRET>
```

once an hour. The request wakes the machine, and
[`src.scheduler.runner`](reference/scheduler.md#src.scheduler.runner) runs
whatever is due according to the `chats` table:

- **Avatar rotation** when `chats.date` has passed. The date moves forward by
  `delta` days (past `now`, if the bot slept through several periods) before the
  rotation runs.
- **Survey results** from 12:00 UTC on the 1st, once per month
  (`chats.survey_period`).

Each job is claimed with a conditional `UPDATE` before it runs, so repeated or
concurrent ticks never run it twice. As a result a rotation happens at the
first tick after its time: within an hour with an hourly cron.

!!! note
    Do not tick more often than every hour or so: the machine would never get
    idle long enough to stop.

## Documentation site

This site is built with MkDocs by
[`docs.yml`](https://github.com/NickLyrick/ChatIconRotBot/blob/master/.github/workflows/docs.yml).
Every branch builds it in strict mode, so broken links and docstring
references fail the run; pushes to `master` also publish it to GitHub Pages.
