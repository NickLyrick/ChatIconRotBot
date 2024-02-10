""" Main script Bot  """

import logging
import asyncio

from src.bot.instance import bot
from src.bot.commands import set_bot_commands
from src.dispatcher.instance import dispatcher

from src.middleware.db import DBSession
from src.database.pool import create_pool

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    """" Entry Point """

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    await set_bot_commands(bot)

    pool_connect = create_pool()

    dispatcher.update.middleware.register(DBSession(pool_connect))

    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        bot.session.close()
