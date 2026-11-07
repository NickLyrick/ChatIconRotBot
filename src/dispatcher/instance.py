"""Initialize dispatcher"""

import logging

from aiogram import Dispatcher
from aiogram.utils.chat_action import ChatActionMiddleware

from src.database import Request

# Routers
from src.handlers.basic_handlers import basic_router
from src.handlers.game_score_handlers import game_score_router
from src.handlers.records_handlers import records_router
from src.handlers.schedule_handlers import schedule_router
from src.handlers.settings_menu_handlers import settings_router
from src.handlers.tables_handlers import table_router
from src.handlers.wiki_handlers import wiki_router

# Middlewares
from src.middleware.db_middleware import DBSession

dispatcher = Dispatcher()

# Routers are included at import time: the webhook is registered with
# dispatcher.resolve_used_update_types(), which only sees included routers.
dispatcher.include_routers(
    basic_router,
    game_score_router,
    table_router,
    schedule_router,
    settings_router,
    records_router,
    wiki_router,
)


async def register_middlewares(dp: Dispatcher, request: Request) -> None:
    """Register Middlewares"""

    chat_action_middleware = ChatActionMiddleware()

    dp.message.middleware.register(chat_action_middleware)
    dp.update.middleware.register(chat_action_middleware)
    dp.error.middleware.register(chat_action_middleware)

    dp.update.middleware.register(DBSession(request=request))


@dispatcher.startup()
async def on_startup(dispatcher: Dispatcher) -> None:
    """Open the database pool and wire it into the handlers."""

    request = Request()
    await request.create_connection()
    dispatcher["request"] = request
    logging.info("Connection created")

    await register_middlewares(dp=dispatcher, request=request)
    logging.info("Middlewares registered")


@dispatcher.shutdown()
async def on_shutdown(dispatcher: Dispatcher) -> None:
    """Release database resources."""

    request = dispatcher.get("request")
    if request is not None:
        await request.close()
