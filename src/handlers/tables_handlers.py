"""This module contains handlers for tables commands."""

from datetime import datetime, timezone

from aiogram import Bot, Router, flags, types
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandObject
from aiogram.types import ReplyParameters, error_event
from aiogram.utils import formatting

from src.bot.settings import settings
from src.database import Request
from src.utility.rich_table import table_message
from src.utility.schedule import localize

table_router = Router(name=__name__)


@table_router.message(Command("show_queue"))
@flags.chat_action(action=ChatAction.TYPING)
async def show_queue(message: types.Message, request: Request) -> None:
    """Show the queue of trophies."""

    chat_id = message.chat.id

    data = []
    try:
        data = await request.get_queue(chat_id)
    except Exception as e:
        await message.reply(
            text=f"Не удалось получить очередь трофеев\n\n"
            f"Ошибка: \n"
            f"{formatting.Pre(e).as_html()}"
        )

    if len(data) > 0:
        await message.bot.send_rich_message(
            chat_id=chat_id,
            rich_message=table_message(
                data,
                columns=["Nickname", "Game", "Platform"],
                caption="Очередь трофеев",
            ),
            reply_parameters=ReplyParameters(message_id=message.message_id),
        )
    else:
        await message.reply(text="Список пуст!")


@table_router.message(Command("top"))
@flags.chat_action(action=ChatAction.TYPING)
async def top(message: types.Message, command: CommandObject, request: Request) -> None:
    """Show the top of the chat."""

    chat_id = message.chat.id
    arguments = command.args
    date = datetime(1980, 1, 1, tzinfo=timezone.utc)

    caption = "Топ за всё время"
    if arguments is not None:
        try:
            # The day starts at midnight in the chat's time zone.
            date = localize(
                datetime.strptime(arguments.strip(), "%d.%m.%Y"),
                await request.get_chat_timezone(chat_id),
            )
            caption = f"Топ от {arguments.strip()}"
        except ValueError:
            caption = "Топ за всё время"

    data = []
    try:
        data = await request.get_top(chat_id=chat_id, date=date)
    except Exception as e:
        await message.reply(
            text=f"Не удалось получить топ от {date}\n\n"
            f"Ошибка: \n"
            f"{formatting.Pre(e).as_html()}"
        )

    if len(data) > 0:
        # Pilot of the native table block; the other commands still send images.
        await message.bot.send_rich_message(
            chat_id=chat_id,
            rich_message=table_message(
                data, columns=["Nickname", "Trophies"], caption=caption
            ),
            reply_parameters=ReplyParameters(message_id=message.message_id),
        )
    else:
        await message.reply("Список пуст!")


@table_router.message(Command("history"))
@flags.chat_action(action=ChatAction.TYPING)
async def get_history(message: types.Message, command: CommandObject, request: Request):
    """Get the history of the user's trophies."""

    chat_id = message.chat.id
    arguments = command.args

    username = None
    user_id = message.from_user.id

    if arguments is not None:
        username = arguments.strip().lstrip("@") or None

    data = []
    try:
        data = await request.get_history(
            chat_id=chat_id, user_id=user_id, username=username
        )
    except Exception as e:
        display_name = ("@" + username) if username else "пользователя"
        await message.reply(
            text=f"Не удалось получить историю {display_name}\n\n"
            f"Ошибка: \n"
            f"{formatting.Pre(e).as_html()}"
        )

    if len(data) > 0:
        display_name = ("@" + username) if username else message.from_user.full_name
        await message.bot.send_rich_message(
            chat_id=chat_id,
            rich_message=table_message(
                data,
                columns=["Game", "Date", "Platform"],
                caption=f"Список всех трофеев: {display_name}",
            ),
            reply_parameters=ReplyParameters(message_id=message.message_id),
        )
    else:
        await message.reply("Список пуст!")


@table_router.error()
async def error_handler(event: error_event.ErrorEvent, bot: Bot) -> None:
    """Handle errors in tables router."""

    content = formatting.as_list(
        formatting.Text(f"Ошибка в {__name__}:"),
        formatting.Pre(event.exception),
    )
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text=content.as_html())
