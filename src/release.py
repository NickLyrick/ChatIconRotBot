"""Once-per-deploy tasks, run by Fly's release_command before the new version starts.

    python -m src.release

1. Apply the database migrations.
2. Register the webhook with the current URL and secret.
3. Publish the command lists and tell the admins about the new version.

A failure here aborts the deploy, and the previous version keeps running.
"""

import asyncio
import logging

from alembic import command
from alembic.config import Config

from src.bot.announce import announce_start
from src.bot.instance import bot
from src.bot.settings import settings
from src.dispatcher.instance import dispatcher
from src.web.app import register_webhook


def migrate() -> None:
    """Upgrade the database to the latest revision."""

    command.upgrade(Config("alembic.ini"), "head")


async def configure_telegram() -> None:
    """Register the webhook and announce the deploy."""

    # A polling bot announces itself on start (see basic_handlers.bot_started).
    if not settings.webhook.enabled:
        return

    try:
        await register_webhook(bot, dispatcher, force=True)
        await announce_start(bot, text="Бот обновлён!")
    finally:
        await bot.session.close()


def main() -> None:
    """Entry point."""

    logging.basicConfig(level=logging.INFO)
    migrate()
    asyncio.run(configure_telegram())


if __name__ == "__main__":
    main()
