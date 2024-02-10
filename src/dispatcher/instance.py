from aiogram import Dispatcher

# Routers
from src.handlers.basic import basic


def register_routers(dp: Dispatcher) -> None:
    """Register Routers"""

    dp.include_router(basic)


# Initialize bot and dispatcher
dispatcher = Dispatcher()

register_routers(dispatcher)
