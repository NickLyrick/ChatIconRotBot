"""Jobs for scheduler."""

import logging
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta

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

        if hunter_id is not None and game is not None:
            history_id = await request.get_history_id(
                chat_id=chat_id, user_id=hunter_id, game=game, platform=platform
            )

            await request.add_avatar_date(history_id=history_id, date=datetime.now(timezone.utc))

            callback_data = GameSurveyCallbackData(
                hunter_id=hunter_id, history_id=history_id
            )

            avatar.seek(0)

            sended_message = await bot.send_photo(
                photo=BufferedInputFile(file=avatar.read(), filename="game.png"),
                chat_id=chat_id,
                caption=text,
                reply_markup=build_start_survey_keyboard(
                    text="Оценить", callback_data=callback_data
                ),
            )
            await bot.pin_chat_message(chat_id=chat_id, message_id=sended_message.message_id)
        else:
            await bot.send_message(chat_id=chat_id, text=text)

        t_delta = timedelta(days=where_run[chat_id]["delta"])
        date = where_run[chat_id]["date"] + t_delta
        await request.set_chat_date(chat_id, date)
    except Exception as e:
        for admin_id in settings.bot.admin_ids:
            await bot.send_message(
                admin_id, text=f"{__name__}:\n {formatting.Pre(e).as_html()}"
            )

async def finish_survey(bot: Bot, request: Request, chat_id: int):
    """Distribution of survey results"""

    now = datetime.now(timezone.utc)
    date = now + relativedelta(months=-1)

    media = []
    trophy_ids = set()
    for score in (Scores.game, Scores.picture, Scores.difficulty):
        text = "Результаты в категории "
        if score is Scores.game:
            text += "Игра"
        elif score is Scores.picture:
            text += "Картинка"
        elif score is Scores.difficulty:
            text += "Сложность"

        # [(trophy_id, hunter, game, score)]
        results = await request.get_survey_results(chat_id=chat_id,
                                                   field=score,
                                                   from_date=date,
                                                   to_date=now)
        if len(results) == 0:
            break

        trophy_ids.update(row[0] for row in results)

        media.extend(table(data=[(row[1], row[2], row[3]) for row in results],
                           columns=["Hunter", "Game", "Score"],
                           name=text))
        await request.add_survey_history(score_type=score.key,
                                         data=[(row[0], row[3]) for row in results])

    if len(media) == 0:
        await bot.send_message(chat_id=chat_id, text="Опрос не проводился")
    else:
        media[0].caption = f"Результаты опроса за {date.strftime("%m.%Y")}"
        await bot.send_media_group(chat_id=chat_id, media=media)
        await request.delete_scores(trophy_ids=trophy_ids)

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
