"""Initialize dispatcher"""

import logging

import pytz
from aiogram import Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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


def register_routers(dp: Dispatcher) -> None:
    """Register Routers"""

    dp.include_router(basic_router)
    dp.include_router(table_router)
    dp.include_router(schedule_router)
    dp.include_router(records_router)
    dp.include_router(wiki_router)


def register_middlewares(
    dp: Dispatcher, db_middleware: DBSession, scheduler_middleware: SchedulerMW
) -> None:
    """Register Middlewares"""

    dp.update.middleware.register(db_middleware)
    dp.message.middleware.register(scheduler_middleware)


async def on_startup() -> None:
    """On startup"""

    pool_connection = await get_pool()
    logging.info("Connected to database")

    scheduler = AsyncIOScheduler(timezone=pytz.utc)
    logging.info("Scheduler created")

    register_middlewares(
        dp=dispatcher,
        db_middleware=DBSession(connector=pool_connection),
        scheduler_middleware=SchedulerMW(scheduler=scheduler),
    )
    logging.info("Middlewares registered")

    register_routers(dp=dispatcher)
    logging.info("Routers registered")


dispatcher = Dispatcher()
dispatcher.startup.register(on_startup)
