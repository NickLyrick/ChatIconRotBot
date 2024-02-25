""" Main script Bot  """

import asyncio
import logging
import os

from src.bot.instance import bot
from src.dispatcher.instance import dispatcher

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    """Entry Point"""

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logging.info("Bot started")

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(bot.session.close())
    finally:
        asyncio.run(bot.session.close())
