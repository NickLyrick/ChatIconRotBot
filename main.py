""" Main script Bot  """

import asyncio
import contextlib
import logging
import os

from aiohttp import web

from src.bot.instance import bot
from src.bot.settings import settings
from src.dispatcher.instance import dispatcher
from src.scheduler.runner import run_due_jobs
from src.web.app import build_app

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# How often a polling bot checks for due jobs. A webhook bot is woken up by the
# external cron instead (POST /jobs/tick).
POLLING_TICK_SECONDS = 60


def run_webhook() -> None:
    """Serve updates and scheduler ticks over HTTP."""

    logging.info("Starting webhook server on port %s", settings.webhook.port)
    web.run_app(
        build_app(bot, dispatcher),
        host=settings.webhook.host,
        port=settings.webhook.port,
        print=None,
    )


async def tick_forever() -> None:
    """Run the due jobs once a minute, standing in for the external cron."""

    while True:
        await asyncio.sleep(POLLING_TICK_SECONDS)
        request = dispatcher.get("request")
        if request is None:
            continue
        try:
            await run_due_jobs(bot, request)
        except Exception:
            logging.exception("Scheduled tick failed")


async def run_polling() -> None:
    """Long polling for local development."""

    logging.info("WEBHOOK_BASE_URL is not set, starting long polling")
    # Telegram refuses getUpdates while a webhook is registered.
    await bot.delete_webhook(drop_pending_updates=False)

    ticker = asyncio.create_task(tick_forever())
    try:
        await dispatcher.start_polling(bot)
    finally:
        ticker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await ticker
        await bot.session.close()


def main() -> None:
    """Entry Point"""

    logging.basicConfig(level=logging.INFO)

    if settings.webhook.enabled:
        run_webhook()
    else:
        with contextlib.suppress(KeyboardInterrupt):
            asyncio.run(run_polling())


if __name__ == "__main__":
    main()
