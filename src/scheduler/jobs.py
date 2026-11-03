"""Jobs for scheduler."""

import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiogram.utils import formatting
from dateutil.relativedelta import relativedelta

from src.bot.settings import settings
from src.database.connect import Request
from src.database.schemas import Scores
from src.keyboards.inline import GameSurveyCallbackData, build_start_survey_keyboard
from src.utility.rich_table import heading_block, rich_message, table_block


async def change_avatar(bot: Bot, request: Request, chat_id: int):
    """Change chat avatar.

    The next rotation date is not touched here: the runner has already moved
    it forward when it claimed this rotation.
    """

    try:
        logging.info(f"Changing avatar for chat {chat_id}")

        queued = await request.get_avatar(chat_id)

        if queued.file_id is not None:
            avatar = await bot.download(file=queued.file_id)
            await bot.set_chat_photo(
                chat_id=chat_id,
                photo=BufferedInputFile(file=avatar.read(), filename="avatar.png"),
            )

        if queued.hunter_id is not None and queued.game is not None:
            history_id = await request.get_history_id(
                chat_id=chat_id,
                user_id=queued.hunter_id,
                game=queued.game,
                platform=queued.platform,
            )

            await request.add_avatar_date(history_id=history_id, date=datetime.now(timezone.utc))

            avatar.seek(0)

            sended_message = await bot.send_photo(
                photo=BufferedInputFile(file=avatar.read(), filename="game.png"),
                chat_id=chat_id,
                caption=queued.text,
                reply_markup=build_start_survey_keyboard(
                    text="Оценить",
                    callback_data=GameSurveyCallbackData(
                        hunter_id=queued.hunter_id, history_id=history_id
                    )
                ),
            )
            await bot.pin_chat_message(chat_id=chat_id, message_id=sended_message.message_id)
        else:
            await bot.send_message(chat_id=chat_id, text=queued.text)

        if queued.record_id is not None:
            await request.delete_queue_record(queued.record_id)
    except Exception as e:
        for admin_id in settings.bot.admin_ids:
            await bot.send_message(
                admin_id, text=f"{__name__}:\n {formatting.Pre(e).as_html()}"
            )

async def finish_survey(bot: Bot, request: Request, chat_id: int):
    """Distribution of survey results"""

    try:
        # Get first day of the previous month 00:00 UTC
        now = datetime.now(timezone.utc)
        date_start = now.replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=-1)
        # Get Last day of the previous month
        date_end = now.replace(day=1, hour=0, minute=0, second=0)

        tables = []
        trophy_ids = set()
        for score in (Scores.game, Scores.picture, Scores.difficulty):
            match score:
                case Scores.game:
                    text = "Результаты в категории Игра"
                case Scores.picture:
                    text = "Результаты в категории Картинка"
                case Scores.difficulty:
                    text = "Результаты в категории Сложность"

            # [(trophy_id, hunter, game, score)]
            results = await request.get_survey_results(chat_id=chat_id,
                                                    field=score,
                                                    from_date=date_start,
                                                    to_date=date_end)
            if len(results) == 0:
                break

            trophy_ids.update(row[0] for row in results)

            tables.append(table_block(data=[(row[1], row[2], row[3]) for row in results],
                                      columns=["Hunter", "Game", "Score"],
                                      caption=text))
            await request.add_survey_history(score_type=score.key,
                                            data=[(row[0], row[3]) for row in results])

        if len(tables) == 0:
            logging.warning(
                (
                    f"{__name__}: The survey has not been conducted "
                    f"or has already been completed in chat {chat_id}"
                )
            )
        else:
            # One message titled by a heading, with a table per category.
            survey_message = await bot.send_rich_message(
                chat_id=chat_id,
                rich_message=rich_message(
                    [
                        heading_block(
                            f"Результаты опроса за {date_start.strftime('%m.%Y')}"
                        ),
                        *tables,
                    ]
                ),
            )

            # Pin Survey Message
            await bot.pin_chat_message(chat_id=chat_id, message_id=survey_message.message_id)

            # Delete scores for calculated trophy_ids
            await request.delete_scores(trophy_ids=trophy_ids)
    except Exception as e:
        for admin_id in settings.bot.admin_ids:
            await bot.send_message(
                admin_id, text=f"{__name__}:\n {formatting.Pre(e).as_html()}"
            )
