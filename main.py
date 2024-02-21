""" Main script Bot  """

import asyncio
import logging

from src.bot.commands import set_bot_commands
from src.bot.instance import bot
from src.dispatcher.instance import get_dispatcher

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    """Entry Point"""

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    await set_bot_commands(bot)

    dispatcher = await get_dispatcher()

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.run(bot.session.close)
