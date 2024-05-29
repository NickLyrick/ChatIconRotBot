"""Schedule handlers module"""

from datetime import datetime, timezone

import pytz
from aiogram import Bot, Router, types
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.utils import formatting

from src.database import Request
from src.filters import my_filters
from src.scheduler.scheduler import Scheduler

from . import error_handler

schedule_router = Router(name=__name__)


@schedule_router.message(CommandStart(), my_filters.from_group_or_supergroup)
async def start(
    message: types.Message, bot: Bot, request: Request, scheduler: Scheduler
) -> None:
    """Start the scheduler for the chat."""

    chat_id = message.chat.id
    if chat_id not in scheduler.where_run:
        date = datetime.now(timezone.utc)
        await request.add_chat_data(chat_id=chat_id, date=date, delta=1)

        await scheduler.add_change_avatar_job(
            bot=bot, request=request, chat_id=chat_id, date=date, delta=1
        )

    await message.answer("Да начнётся охота!")


@schedule_router.message(Command("set_date"), my_filters.check_permissions)
async def set_date(
    message: types.Message,
    command: CommandObject,
    bot: Bot,
    request: Request,
    scheduler: Scheduler,
) -> None:
    """Set the date for the chat avatar change."""

    chat_id = message.chat.id
    arguments = command.args

    date = datetime.strptime(arguments, "%d/%m/%Y %H:%M")
    date = date.replace(tzinfo=pytz.utc)

    if date > datetime.now(timezone.utc):
        await request.set_chat_date(chat_id, date)
        await scheduler.add_change_avatar_job(
            bot=bot, request=request, chat_id=chat_id, date=date
        )

        date.strftime("%d.%m.%Y %H:%M")
        text = (
            f"Ближайшая дата смены фото чата успешно установлена на: "
            f" {date.astimezone(tz=pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')}"
        )
    else:
        text = (
            "Ближайшая дата смены оказалась в прошлом. \n" "Я не могу изменить прошлое!"
        )

    await message.reply(text)


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

    chat_id = message.chat.id
    delta = int(command.args)

    if delta > 0:
        await request.set_chat_delta(chat_id=chat_id, delta=delta)
        await scheduler.add_change_avatar_job(
            bot=bot, request=request, chat_id=chat_id, date=None, delta=delta
        )
        text = f"Промежуток между сменами фото чата успешно установлен на {delta}д."
    else:
        text = "Промежуток между сменами фото должен быть больше нуля и целым числом"

    await message.reply(text=text)


@schedule_router.message(
    Command("show_settings"),
    my_filters.from_group_or_supergroup,
    my_filters.check_permissions,
)
async def show_settings(message: types.Message, bot: Bot, request: Request):
    """Show the current chat settings."""

    chat_id = message.chat.id

    try:
        date, delta, default_avatar = await request.get_chat_settings(chat_id=chat_id)
    except Exception as e:
        content = formatting.as_list(
            formatting.Text(f"Ошибка в {__name__}.show_settings():"),
            formatting.Pre(e),
            formatting.Text(
                f"Бот не запущен в чате c {chat_id=}, где он пытается получить настройки"
            ),
        ).as_html()
        await message.reply(text=content)
        return

    text = (
        f"Ближайшая дата смены: {date.strftime('%d.%m.%Y %H:%M')}.\n"
        f"Промежуток между сменами: {delta}д."
    )

    if default_avatar is not None:
        photo_id = default_avatar
        try:
            await message.reply_photo(photo=photo_id, caption=text)
        except Exception as e:
            text += f"\n Изображение с {photo_id=} недоступно для данного бота"
            await message.reply(text)
    else:
        text += "\nСтандартный аватар не установлен"
        await message.reply(text)


# Add error handler to the router
error_handler = schedule_router.error(error_handler)
