# API reference

Generated from the docstrings in [`src/`](https://github.com/NickLyrick/ChatIconRotBot/tree/dev/src).
The code is read statically: building the docs imports nothing, so it needs
no `TOKEN` and no database.

| Package | Contents |
| --- | --- |
| [Bot](bot.md) | Bot instance, settings, command descriptions, start announcement |
| [Dispatcher](dispatcher.md) | Dispatcher, router and middleware registration |
| [Handlers](handlers.md) | Message and callback handlers |
| [Keyboards](keyboards.md) | Survey and settings menu keyboards, callback data |
| [Filters](filters.md) | Caption format, chat type and permission filters |
| [Middleware](middleware.md) | Injects the database request object |
| [Scheduler](scheduler.md) | What is due on a tick, and the jobs themselves |
| [Database](database.md) | SQLAlchemy models and queries |
| [Utilities](utility.md) | Trophy record model, table messages, schedule helpers |
| [Web app](web.md) | `/webhook`, `/jobs/tick`, `/health` |
| [Release tasks](release.md) | Migrations, webhook and command lists on every deploy |
