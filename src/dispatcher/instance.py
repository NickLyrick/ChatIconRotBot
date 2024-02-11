from aiogram import Dispatcher

# Routers
from src.handlers.basic import basic
from src.handlers.chat_handlers import chat_router


def register_routers(dp: Dispatcher) -> None:
    """Register Routers"""

    dp.include_router(basic)
    dp.include_router(chat_router)


# Initialize bot and dispatcher
dispatcher = Dispatcher()

register_routers(dispatcher)
