"""Initialize dispatcher"""

import pytz
from aiogram import Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.database.connect import get_pool

# Routers
from src.handlers.basic import basic
from src.handlers.records import records_router
from src.handlers.schedule import schedule_router
from src.handlers.tables import table_router

# Middlewares
from src.middleware.db import DBSession
from src.middleware.scheduler import SchedulerMW


def register_routers(dp: Dispatcher) -> None:
    """Register Routers"""

    dp.include_router(basic)
    dp.include_router(table_router)
    dp.include_router(schedule_router)
    dp.include_router(records_router)


def register_middlewares(
    dp: Dispatcher, db_middleware: DBSession, scheduler_middleware: SchedulerMW
) -> None:
    """Register Middlewares"""

    dp.update.middleware.register(db_middleware)
    dp.message.middleware.register(scheduler_middleware)


# Initialize bot and dispatcher
dispatcher = Dispatcher()


async def get_dispatcher() -> Dispatcher:
    """Method to get dispatcher instance with all routers and middlewares registered."""

    pool_connection = await get_pool()
    scheduler = AsyncIOScheduler(timezone=pytz.utc)
    scheduler.start()

    register_middlewares(
        dp=dispatcher,
        db_middleware=DBSession(connector=pool_connection),
        scheduler_middleware=SchedulerMW(scheduler=scheduler),
    )
    register_routers(dp=dispatcher)

    return dispatcher
