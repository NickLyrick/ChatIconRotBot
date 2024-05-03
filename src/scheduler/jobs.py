"""Jobs for scheduler."""

import datetime
import logging

from operator import itemgetter
from typing import List, Tuple

from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.utils import formatting

from src.bot.settings import settings
from src.database.connect import Request
from src.database.schemas import Scores
from src.keyboards.inline import GameSurveyCallbackData, build_start_survey_keyboard
from src.utility.tools import table


async def change_avatar(bot: Bot, request: Request, chat_id: int, where_run: dict):
    """Change chat avatar."""
    try:
        logging.info(f"Changing avatar for chat {chat_id}")

        file_id, hunter_id, game, platform, text = await request.get_avatar(chat_id)

        if file_id is not None:
            avatar = await bot.download(file=file_id)
            await bot.set_chat_photo(
                chat_id=chat_id,
                photo=BufferedInputFile(file=avatar.read(), filename="avatar.png"),
            )

        if hunter_id is not None:
            history_id = await request.get_history_id(
                chat_id=chat_id, user_id=hunter_id, game=game, platform=platform
            )

            callback_data = GameSurveyCallbackData(
                hunter_id=hunter_id, history_id=history_id
            )

            avatar.seek(0)

            await bot.send_photo(
                photo=BufferedInputFile(file=avatar.read(), filename="game.png"),
                chat_id=chat_id,
                caption=text,
                reply_markup=build_start_survey_keyboard(
                    text="Оценить", callback_data=callback_data
                ),
            )

        t_delta = datetime.timedelta(days=where_run[chat_id]["delta"])
        date = where_run[chat_id]["date"] + t_delta
        await request.set_chat_date(chat_id, date)
    except Exception as e:
        for admin_id in settings.bot.admin_ids:
            await bot.send_message(
                admin_id, text=f"{__name__}:\n {formatting.Pre(e).as_html()}"
            )

async def send_results(bot: Bot, request: Request, chat_id: int, score):
    """Get and send results to Chat"""
    text = "Результаты опроса в категории "
    if score is Scores.game:
        text += "Игра"
    elif score is Scores.picture:
        text += "Картинка"
    elif score is Scores.difficulty:
        text += "Сложность"

    results = await request.get_survey_results(chat_id=chat_id, field=score)
    if len(results) == 0:
        await bot.send_message(chat_id=chat_id, text=f"{text}: опрос не проводился")
    else:
        await bot.send_media_group(chat_id=chat_id,
                                media=table(results,
                                            ["Hunter", "Game", "Score"],
                                            text))


async def finish_survey(bot: Bot, request: Request, chat_id: int):
    """Distribution of survey results"""
    for score in (Scores.game, Scores.picture, Scores.difficulty):
        await send_results(bot=bot, request=request, chat_id=chat_id, score=score)


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
