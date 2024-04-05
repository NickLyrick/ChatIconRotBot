"""This module contains handlers for adding and deleting records in the database."""

import random

import yaml
from aiogram import Bot, F, Router, types
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.exceptions import AiogramError
from aiogram.filters import Command
from aiogram.types.error_event import ErrorEvent
from aiogram.utils import formatting

from src.bot.settings import settings
from src.database import Request
from src.filters import my_filters
from src.utility.platinum_record import PlatinumRecord

records_router = Router(name=__name__)


async def check_permissions(message: types.Message) -> bool:
    """Check if user has permissions to change group info."""

    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status == ChatMemberStatus.CREATOR or member.can_change_info
    except AiogramError as e:
        await message.reply(
            text=f"Не хватает прав для изменения информации группы!\n"
            f"Ошибка: \n"
            f"{formatting.Pre(e)}.as_html()"
        )


# TODO: Split on 2 functions. Process Default avatar separately. Use my_filter.check_permissions and remove 17-24
@records_router.message(F.photo, my_filters.platinum_check)
async def add_record(message: types.Message, bot: Bot, request: Request) -> None:
    """Add record to the database."""

    chat_id = message.chat.id
    username = message.from_user.username
    bot = await bot.get_me()
    bot_username = bot.username
    game = (
        message.caption.replace(f"@{bot_username}", "")
        .replace("Xbox", "")
        .replace("Playstation", "")
        .strip()
    )

    platform = "Playstation"
    if message.caption.find("Xbox") != -1:
        platform = "Xbox"

    file_id = message.photo[-1].file_id

    with open("src/data/quotations.yaml", "r", encoding="utf8") as file:
        quotations = yaml.safe_load(file)["quotations"]

    quotation = random.choice(quotations)

    text = formatting.as_list(
        formatting.Text(formatting.Italic(f" \"{quotation['quotation']}\" ©", "\n")),
        formatting.Text(f"{quotation['author']}", "\n", f"{quotation['game']}"),
    ).as_html()

    if game == "*Default*":
        if await check_permissions(message):
            username = "*Default*"
            text = "Стандартный аватар установлен"
        else:
            return

    if username is not None:
        record = PlatinumRecord(username, game, file_id, platform)
        await request.add_record(chat_id=chat_id, record=record)

    await message.reply(text)


@records_router.message(Command("delete_game"))
async def delete_game(message: types.Message, bot: Bot, request: Request):
    """Delete record from the database."""

    chat_id = message.chat.id
    username = message.from_user.username

    text = await request.delete_record(chat_id=chat_id, username=username)

    await message.reply(text)


@records_router.error()
async def error_handler(event: ErrorEvent, bot: Bot) -> None:
    """Handle errors."""

    content = formatting.as_list(
        formatting.Text(f"Ошибка в {__name__}:"),
        formatting.Pre(event.exception),
    )
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text=content.as_html())
