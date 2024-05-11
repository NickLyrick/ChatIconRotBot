"""Schedule handlers module"""

from datetime import datetime, timezone

import pytz
from aiogram import Bot, Router, types
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types.error_event import ErrorEvent
from aiogram.utils import formatting

from src.bot.settings import settings
from src.database import Request
from src.filters import my_filters
from src.scheduler.scheduler import Scheduler

schedule_router = Router(name=__name__)


@schedule_router.message(CommandStart(), my_filters.from_group_or_supergroup)
async def start(
    message: types.Message, bot: Bot, request: Request, scheduler: Scheduler
) -> None:
    """Start the scheduler for the chat."""

    try:
        chat_id = message.chat.id
        if chat_id not in scheduler.where_run:
            date = datetime.now(timezone.utc)
            await request.add_chat_data(chat_id=chat_id, date=date, delta=1)
            await scheduler.add_change_avatar_job(
                bot=bot, request=request, chat_id=chat_id, date=date, delta=1
            )

        await message.answer("Да начнётся охота!")
    except Exception as e:
        await message.answer(text=f"Ошибка: \n" f"{formatting.Pre(e)}.as_html()")


@schedule_router.message(Command("set_date"), my_filters.check_permissions)
async def set_date(
    message: types.Message,
    command: CommandObject,
    bot: Bot,
    request: Request,
    scheduler: Scheduler,
) -> None:
    """Set the date for the chat avatar change."""

    try:
        chat_id = message.chat.id
        arguments = command.args

        date = datetime.strptime(arguments, "%d/%m/%Y %H:%M")
        date = date.replace(tzinfo=pytz.utc)

        if date > datetime.now(timezone.utc):
            await request.set_chat_date(chat_id, date)
            await scheduler.add_change_avatar_job(
                bot=bot, request=request, chat_id=chat_id, date=date, delta=None
            )

            date.strftime("%d.%m.%Y %H:%M")
            text = (
                f"Ближайшая дата смены фото чата успешно установлена на: "
                f" {date.astimezone(tz=pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')}"
            )
        else:
            text = (
                "Ближайшая дата смены оказалась в прошлом. \n"
                "Я не могу изменить прошлое!"
            )

        await message.reply(text)
    except Exception as e:
        await message.reply(
            text=(
                f"Дата введена неверно или что-то пошло не так.\n"
                f"Пример: /set_date 22/07/1941 04:00\n"
                f"{formatting.Pre(e).as_html()}"
            )
        )


@schedule_router.message(Command("set_delta"), my_filters.check_permissions)
async def set_delta(
    message: types.Message,
    command: CommandObject,
    bot: Bot,
    request: Request,
    scheduler: Scheduler,
):
    """Set the delta for the chat avatar change."""
    bot = await bot.get_me()
    bot_username = bot.username

    try:
        chat_id = message.chat.id
        delta = int(command.args)

        if delta > 0:
            await request.set_chat_delta(chat_id=chat_id, delta=delta)
            await scheduler.add_change_avatar_job(
                bot=bot, request=request, chat_id=chat_id, date=None, delta=None
            )
            text = f"Промежуток между сменами фото чата успешно установлен на {delta}д."
        else:
            text = (
                "Промежуток между сменами фото должен быть больше нуля и целым числом"
            )

        await message.reply(text=text)
    except Exception as e:
        await message.reply(
            text=(
                f"Промежуток задан не верно. Пример: /set_delta@{bot_username} 3\n"
                f"Ошибка: \n"
                f"{formatting.Pre(e).as_html()}"
            )
        )


@schedule_router.message(
    Command("show_settings"),
    my_filters.from_group_or_supergroup,
    my_filters.check_permissions,
)
async def show_settings(message: types.Message, request: Request):
    """Show the current chat settings."""

    chat_id = message.chat.id

    try:
        date, delta, default_avatar = await request.get_chat_settings(chat_id=chat_id)

        text = (
            f"Ближайшая дата смены: {date.strftime('%d.%m.%Y %H:%M')}.\n"
            f"Промежуток между сменами: {delta}д."
        )

        if default_avatar is not None:
            photo_id = default_avatar
            await message.reply_photo(photo=photo_id, caption=text)
        else:
            text += "\nСтандартный аватар не установлен"
            await message.reply(text)

    except Exception as e:
        await message.reply(
            text=(
                f"Ну удалось получить настройки чата: {chat_id}\n"
                f"Ошибка: \n"
                f"{formatting.Pre(e).as_html()}"
            )
        )


@schedule_router.error()
async def error_handler(event: ErrorEvent, bot: Bot) -> None:
    """Handle errors."""

    content = formatting.as_list(
        formatting.Text(f"Ошибка в {__name__}:"),
        formatting.Pre(event.exception),
    )
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text=content.as_html())
