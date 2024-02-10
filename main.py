""" Main script Bot  """

import logging
import asyncio

from src.bot.instance import bot
from src.bot.commands import set_bot_commands
from src.dispatcher.instance import dispatcher

from src.middleware.db import DBSession
from src.database.pool import create_pool

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# import random
# import psycopg2
#
# from pytz import timezone as tz
# from datetime import datetime, timezone, timedelta

# from src.utility.answers import answers, help_text
# from src.utility.utils import table
# from src.utility.bot_commands import set_bot_commands
#
# from src.handlers.commands import commands
#
# from src.scheduler.scheduler import scheduler
#
# db = psycopg2.connect(env.DATABASE_URL)
#
# bot_username = ''
#
#
# def history_date(chat_id, date: datetime):
#     date = date.astimezone(tz=tz('Europe/Moscow'))
#
#     with db.cursor() as cursor:
#         cursor.execute("SELECT hunter, COUNT(id) FROM history "
#                        "WHERE chat_id=%s AND date>=%s "
#                        "GROUP BY hunter "
#                        "ORDER BY COUNT(id) DESC",
#                        (chat_id, date))
#         data = cursor.fetchall()
#
#     if len(data) > 0:
#         img = table(data, ["Nickname", "Trophies"])
#
#         return img
#     else:
#         return None
#
#
# async def db_connection_check():
#     global db
#     try:
#         with db.cursor() as cursor:
#             cursor.execute("SELECT 1")
#     except psycopg2.Error:
#         logging.error("Has lost connection to database")
#         logging.info("Try reconnect to database")
#
#         try:
#             db = psycopg2.connect(DATABASE_URL)
#         except psycopg2.Error:
#             logging.exception("Connect to database failed: ")
#
#
# async def on_startup(dispatcher):
#     global bot_username
#     global where_run
#
#     bot_user = await bot.me
#     bot_username = bot_user.username
#
#     start_db_check = datetime.now(timezone.utc) + timedelta(minutes=1)
#     scheduler.add_job(db_connection_check, "interval", minutes=1, start_date=start_db_check)
#
#     with db.cursor() as cursor:
#         cursor.execute("SELECT * FROM chats")
#         where_run = {chat_id: {'date': date, 'delta': delta}
#                      for chat_id, date, delta in cursor.fetchall()}
#
#     for chat_id in where_run.keys():
#         date = where_run[chat_id]['date']
#         delta = where_run[chat_id]['delta']
#         print(date)
#         add_job(chat_id, date, delta)
#
#     scheduler.print_jobs()
#     scheduler.start()


async def main() -> None:
    """" Entry Point """

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    await set_bot_commands(bot)

    pool_connect = create_pool()

    dispatcher.update.middleware.register(DBSession(pool_connect))

    # await dispatcher.start_polling(bot, on_startup=on_startup)
    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        bot.session.close()
