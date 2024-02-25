"""Jobs for scheduler."""

import datetime
import logging

from aiogram import Bot
from aiogram.types import BufferedInputFile

from src.database.connect import Request


async def change_avatar(bot: Bot, request: Request, chat_id: int, where_run: dict):
    """Change chat avatar."""

    logging.info(f"Changing avatar for chat {chat_id}")

    file_id, text = await request.get_avatar(chat_id)

    if file_id is not None:
        avatar = await bot.download(file=file_id)
        await bot.set_chat_photo(
            chat_id=chat_id,
            photo=BufferedInputFile(file=avatar.read(), filename="avatar.png"),
        )

    await bot.send_message(chat_id, text)

    t_delta = datetime.timedelta(days=where_run[chat_id]["delta"])
    date = where_run[chat_id]["date"] + t_delta
    await request.set_chat_date(chat_id, date)


async def check_db_connection(request: Request):
    """Check database connection."""

    logging.info("Checking database connection")
    await request.check_db_connection()
