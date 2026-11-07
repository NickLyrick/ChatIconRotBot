"""Schedule handlers module"""

from datetime import datetime, timezone

from aiogram import Bot, Router, types
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import error_event
from aiogram.utils import formatting

from src.bot.settings import settings
from src.database import Request
from src.filters import my_filters
from src.utility.schedule import (
    MAX_DELTA_DAYS,
    describe_settings,
    describe_zone,
    example_rotation_date,
    format_chat_date,
    parse_delta,
    parse_rotation_date,
    parse_timezone,
)

schedule_router = Router(name=__name__)

NOT_STARTED_TEXT = "Бот ещё не запущен в этом чате. Сначала выполните /start"


@schedule_router.message(CommandStart(), my_filters.from_group_or_supergroup)
async def start(message: types.Message, request: Request) -> None:
    """Register the chat; its first rotation runs on the next scheduled tick."""

    await request.add_chat(
        chat_id=message.chat.id, date=datetime.now(timezone.utc), delta=1
    )
    await message.answer("Да начнётся охота!")


@schedule_router.message(
    Command("set_date"),
    my_filters.from_group_or_supergroup,
    my_filters.check_permissions,
)
async def set_date(
    message: types.Message,
    command: CommandObject,
    request: Request,
) -> None:
    """Set the date of the next chat avatar change, in the chat's time zone."""

    now = datetime.now(timezone.utc)
    zone = await request.get_chat_timezone(message.chat.id)
    usage = (
        f"Укажите дату и время ({describe_zone(zone, now)}): "
        "/set_date ДД/ММ/ГГГГ ЧЧ:ММ\n"
        f"Например: /set_date {example_rotation_date(now, zone)}"
    )

    if not command.args:
        await message.reply(usage)
        return

    try:
        date = parse_rotation_date(command.args, zone)
    except ValueError:
        await message.reply(f"Неверный формат даты.\n{usage}")
        return

    if date <= now:
        await message.reply(
            "Ближайшая дата смены оказалась в прошлом.\nЯ не могу изменить прошлое!"
        )
        return

    if not await request.set_chat_date(message.chat.id, date):
        await message.reply(NOT_STARTED_TEXT)
        return

    await message.reply(
        f"Ближайшая дата смены фото чата установлена на {format_chat_date(date, zone)}.\n"
        "Фото сменится в ближайшую проверку расписания после этого времени."
    )


@schedule_router.message(
    Command("set_timezone"),
    my_filters.from_group_or_supergroup,
    my_filters.check_permissions,
)
async def set_timezone(
    message: types.Message,
    command: CommandObject,
    request: Request,
) -> None:
    """Set the chat's time zone by city from the menu or by IANA name."""

    zone = parse_timezone(command.args)
    if zone is None:
        await message.reply(
            "Укажите город из меню /settings или название пояса из базы IANA.\n"
            "Например: /set_timezone Екатеринбург или /set_timezone Europe/Berlin"
        )
        return

    if not await request.set_chat_timezone(message.chat.id, zone):
        await message.reply(NOT_STARTED_TEXT)
        return

    chat_settings = await request.get_chat_settings(message.chat.id)
    await message.reply(
        "Часовой пояс чата изменён. Время смены не сдвигалось, "
        "поправить его можно в /settings.\n\n"
        + describe_settings(chat_settings.date, chat_settings.delta, zone)
    )


@schedule_router.message(
    Command("set_delta"),
    my_filters.from_group_or_supergroup,
    my_filters.check_permissions,
)
async def set_delta(
    message: types.Message,
    command: CommandObject,
    request: Request,
) -> None:
    """Set the interval between chat avatar changes, in days."""

    delta = parse_delta(command.args)
    if delta is None:
        await message.reply(
            "Промежуток между сменами фото должен быть целым числом дней "
            f"от 1 до {MAX_DELTA_DAYS}. Например: /set_delta 3"
        )
        return

    if not await request.set_chat_delta(chat_id=message.chat.id, delta=delta):
        await message.reply(NOT_STARTED_TEXT)
        return

    await message.reply(
        f"Промежуток между сменами фото чата установлен на {delta}д.\n"
        "Он начнёт действовать после ближайшей смены."
    )


@schedule_router.message(
    Command("show_settings"),
    my_filters.from_group_or_supergroup,
    my_filters.check_permissions,
)
async def show_settings(message: types.Message, request: Request) -> None:
    """Show the current chat settings."""

    chat_settings = await request.get_chat_settings(chat_id=message.chat.id)
    if chat_settings is None:
        await message.reply(NOT_STARTED_TEXT)
        return

    text = describe_settings(chat_settings.date, chat_settings.delta, chat_settings.timezone)
    default_avatar = chat_settings.default_photo_id

    if default_avatar is None:
        await message.reply(text + "\nСтандартный аватар не установлен")
        return

    try:
        await message.reply_photo(photo=default_avatar, caption=text)
    except Exception:
        await message.reply(
            text + f"\nИзображение с photo_id={default_avatar} недоступно для данного бота"
        )


@schedule_router.error()
async def error_handler(event: error_event.ErrorEvent, bot: Bot) -> None:
    """Handle errors in schedule router."""

    content = formatting.as_list(
        formatting.Text(f"Ошибка в {__name__}:"),
        formatting.Pre(event.exception),
    )
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text=content.as_html())
