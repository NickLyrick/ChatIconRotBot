"""Initialize dispatcher"""

import logging

import pytz
from aiogram import Bot, Dispatcher
from aiogram.utils.chat_action import ChatActionMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.database import Request
from src.database.connect import get_pool

# Routers
from src.handlers.basic_handlers import basic_router
from src.handlers.records_handlers import records_router
from src.handlers.schedule_handlers import schedule_router
from src.handlers.tables_handlers import table_router
from src.handlers.wiki_handlers import wiki_router

# Middlewares
from src.middleware.db_middleware import DBSession
from src.middleware.scheduler_middleware import SchedulerMW
from src.scheduler.scheduler import Scheduler

dispatcher = Dispatcher()


def register_routers(dp: Dispatcher) -> None:
    """Register Routers"""

    dp.include_routers(
        basic_router, table_router, schedule_router, records_router, wiki_router
    )


def register_middlewares(
    dp: Dispatcher, db_middleware: DBSession, scheduler_middleware: SchedulerMW
) -> None:
    """Register Middlewares"""

    dp.update.middleware.register(db_middleware)
    dp.update.middleware.register(scheduler_middleware)
    dp.update.middleware.register(ChatActionMiddleware())
    dp.error.middleware.register(ChatActionMiddleware())


@dispatcher.startup()
async def on_startup(dispatcher: Dispatcher, bot: Bot) -> None:
    """On startup"""

    # Create request manager
    pool_connection = await get_pool()
    logging.info("Pool created")

    # Create scheduler
    scheduler = Scheduler(AsyncIOScheduler(timezone=pytz.utc))
    logging.info("Scheduler created")

    async with pool_connection.connection() as connection:
        request = Request(connection)

    await scheduler.start(bot=bot, request=request)
    logging.info("Scheduler started")

    # Register middlewares
    register_middlewares(
        dp=dispatcher,
        db_middleware=DBSession(connector=pool_connection),
        scheduler_middleware=SchedulerMW(scheduler=scheduler),
    )
    logging.info("Middlewares registered")

    register_routers(dp=dispatcher)
    logging.info("Routers registered")
