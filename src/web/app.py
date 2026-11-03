"""aiohttp application: the Telegram webhook, the scheduler tick and a health check.

Every endpoint does its work before answering. Fly stops an idle machine, and
a request in flight is what tells it the machine is busy, so nothing may keep
running after its response has been sent.
"""

import hmac
import logging
from dataclasses import asdict

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from src.bot.settings import settings
from src.scheduler.runner import run_due_jobs

BOT_KEY = web.AppKey("bot", Bot)
DISPATCHER_KEY = web.AppKey("dispatcher", Dispatcher)


async def register_webhook(bot: Bot, dispatcher: Dispatcher, force: bool = False) -> None:
    """Point Telegram at this deployment.

    Telegram does not report the secret token back, so only ``force`` (used
    once per deploy) re-sends it; a normal start only fixes a wrong URL or
    update list, which costs a single getWebhookInfo call.
    """

    allowed_updates = dispatcher.resolve_used_update_types()

    if not force:
        info = await bot.get_webhook_info()
        if info.url == settings.webhook.url and set(info.allowed_updates or []) == set(
            allowed_updates
        ):
            return

    await bot.set_webhook(
        url=settings.webhook.url,
        secret_token=settings.webhook.secret,
        allowed_updates=allowed_updates,
        drop_pending_updates=False,
    )
    logging.info(f"Webhook set to {settings.webhook.url}")


def _tick_authorized(request: web.Request) -> bool:
    """Check the bearer token sent by the external cron."""

    expected = settings.webhook.jobs_secret
    if not expected:
        return False
    received = request.headers.get("Authorization", "")
    return hmac.compare_digest(received.encode(), f"Bearer {expected}".encode())


async def tick(request: web.Request) -> web.Response:
    """Run the scheduled jobs that are due. Called by the external cron."""

    if not _tick_authorized(request):
        return web.json_response({"error": "unauthorized"}, status=401)

    dispatcher = request.app[DISPATCHER_KEY]
    report = await run_due_jobs(request.app[BOT_KEY], dispatcher["request"])
    return web.json_response(asdict(report))


async def health(_: web.Request) -> web.Response:
    """Liveness check for the Fly proxy."""

    return web.json_response({"status": "ok"})


def build_app(bot: Bot, dispatcher: Dispatcher) -> web.Application:
    """Assemble the web application."""

    if not settings.webhook.secret:
        raise RuntimeError("WEBHOOK_SECRET must be set when WEBHOOK_BASE_URL is set")
    if not settings.webhook.jobs_secret:
        logging.warning("JOBS_SECRET is not set: /jobs/tick will reject every call")

    app = web.Application()
    app[BOT_KEY] = bot
    app[DISPATCHER_KEY] = dispatcher

    SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.webhook.secret,
        handle_in_background=False,
    ).register(app, path=settings.webhook.path)
    app.router.add_post("/jobs/tick", tick)
    app.router.add_get("/health", health)

    # Runs the dispatcher startup (database pool) first, then the webhook check.
    setup_application(app, dispatcher, bot=bot)

    async def ensure_webhook(_: web.Application) -> None:
        await register_webhook(bot, dispatcher)

    app.on_startup.append(ensure_webhook)
    return app
