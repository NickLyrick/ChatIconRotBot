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

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
