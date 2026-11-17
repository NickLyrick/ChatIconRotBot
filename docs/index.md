# ChatIconRotBot

A Telegram bot for communities of trophy hunters. It collects platinum-trophy
screenshots posted by chat members, rotates them as the group chat avatar on a
schedule, and runs a monthly rating survey on the games that were shown.

Built with [aiogram 3](https://docs.aiogram.dev/) (async, webhook over aiohttp),
SQLAlchemy 2 + PostgreSQL, Alembic. All bot messages are in Russian.

## How it works

1. **Submit a trophy.** A member posts a photo captioned `@YourBotName Game Title`
   (append `Xbox` for the Xbox platform, otherwise PlayStation is assumed).
   The bot stores it in the chat's queue and replies with a random gaming quote
   from [`src/data/quotations.yaml`](https://github.com/NickLyrick/ChatIconRotBot/blob/master/src/data/quotations.yaml).
2. **Rotate the avatar.** Every `delta` days the scheduled tick (see
   [Scheduled jobs](deployment.md#scheduled-jobs)) takes the next entry
   from the queue, sets it as the chat photo, posts and pins an announcement with
   the hunter and the game, then removes the entry from the queue and moves the
   history record forward. If the queue is empty, the chat's default avatar is
   used instead.
3. **Rate the game.** The pinned announcement carries an inline *«Оценить»*
   button that opens a private survey with the bot. Members score the game on
   three axes from 1 to 10: *Game*, *Picture*, *Difficulty*. The hunter who
   submitted the trophy only scores *Difficulty*.
4. **Monthly results.** From 12:00 UTC on the 1st of each month the bot
   aggregates the previous month's scores, posts one message with a table per
   category and pins it, once per chat and month.

## Where to go next

- [Commands](commands.md): everything members and admins can type.
- [Setup](setup.md): configuration and running the bot locally.
- [Deployment](deployment.md): Fly.io, CI and the external cron.
- [Database](database.md): tables and Alembic migrations.
- [Development](development.md): checks, tests and the project layout.
- [API reference](reference/index.md): generated from the docstrings.
