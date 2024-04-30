"""Jobs for scheduler."""

import datetime
import logging

from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.utils import formatting

from src.bot.settings import settings
from src.database.connect import Request
from src.keyboards.inline import GameSurveyCallbackData, build_start_survey_keyboard


async def change_avatar(bot: Bot, request: Request, chat_id: int, where_run: dict):
    """Change chat avatar."""
    try:
        logging.info(f"Changing avatar for chat {chat_id}")

        file_id, text = await request.get_avatar(chat_id)

        if file_id is not None:
            avatar = await bot.download(file=file_id)
            await bot.set_chat_photo(
                chat_id=chat_id,
                photo=BufferedInputFile(file=avatar.read(), filename="avatar.png"),
            )

        # TODO: for Artem
        # hunter_id, hunter_name, history_id, game_name = request.get_everything()

        # callback_data = GameSurveyCallbackData(
        #     hunter_id=hunter_id,
        #     hunter_name=hunter_name,
        #     history_id=history_id,
        #     game_name=game_name,
        # )

        await bot.send_message(
            chat_id=chat_id,
            text=text,
            # reply_markup=build_start_survey_keyboard(
            #     text="Оценить", callback_data=callback_data
            # ),
        )

        t_delta = datetime.timedelta(days=where_run[chat_id]["delta"])
        date = where_run[chat_id]["date"] + t_delta
        await request.set_chat_date(chat_id, date)
    except Exception as e:
        for admin_id in settings.bot.admin_ids:
            await bot.send_message(
                admin_id, text=f"{__name__}:\n {formatting.Pre(e).as_html()}"
            )


async def check_db_connection(bot: Bot, request: Request):
    """Check database connection."""

    try:
        logging.info("Checking database connection")
        await request.check_db_connection()
    except Exception as e:
        for admin_id in settings.bot.admin_ids:
            await bot.send_message(
                admin_id, text=f"{__name__}:\n {formatting.Pre(e).as_html()}"
            )
