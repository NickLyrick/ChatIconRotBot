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
    logging.info("Bot started")

    await set_bot_commands(bot)
    logging.info("Bot commands set")

    dispatcher = await get_dispatcher()
    logging.info("Dispatcher created")

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(bot.session.close())
    finally:
        asyncio.run(bot.session.close())
