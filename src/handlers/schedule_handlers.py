"""Schedule handlers module"""

from datetime import datetime, timezone

import pytz
from aiogram import Bot, Router, types
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import error_event
from aiogram.utils import formatting

from src.bot.settings import settings
from src.database import Request
from src.filters import my_filters

schedule_router = Router(name=__name__)


@schedule_router.message(CommandStart(), my_filters.from_group_or_supergroup)
async def start(message: types.Message, request: Request) -> None:
    """Register the chat; its first rotation runs on the next scheduled tick."""

    chat_id = message.chat.id
    if not await request.chat_exists(chat_id):
        await request.add_chat_data(
            chat_id=chat_id, date=datetime.now(timezone.utc), delta=1
        )

    await message.answer("Да начнётся охота!")


@schedule_router.message(Command("set_date"), my_filters.check_permissions)
async def set_date(
    message: types.Message,
    command: CommandObject,
    request: Request,
) -> None:
    """Set the date for the chat avatar change."""

    chat_id = message.chat.id
    arguments = command.args

    if arguments is None:
        await message.reply(text="Вы не указали дату")
        return

    if not arguments:
        await message.reply("Укажите дату: /set_date ДД/ММ/ГГГГ ЧЧ:ММ")
        return

    try:
        date = datetime.strptime(arguments, "%d/%m/%Y %H:%M")
    except ValueError:
        await message.reply("Неверный формат даты. Пример: /set_date 31/12/2026 18:00")
        return
    date = date.replace(tzinfo=pytz.utc)

    if date > datetime.now(timezone.utc):
        await request.set_chat_date(chat_id, date)

        text = (
            f"Ближайшая дата смены фото чата успешно установлена на: "
            f" {date.astimezone(tz=pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')}"
            "\nФото сменится в ближайшую проверку расписания после этого времени."
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
    request: Request,
):
    """Set the delta for the chat avatar change."""
    chat_id = message.chat.id

    try:
        delta = int(command.args) if command.args is not None else 0
    except ValueError:
        delta = 0

    if delta > 0:
        await request.set_chat_delta(chat_id=chat_id, delta=delta)
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


@schedule_router.error()
async def error_handler(event: error_event.ErrorEvent, bot: Bot) -> None:
    """Handle errors in schedule router."""

    content = formatting.as_list(
        formatting.Text(f"Ошибка в {__name__}:"),
        formatting.Pre(event.exception),
    )
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text=content.as_html())
