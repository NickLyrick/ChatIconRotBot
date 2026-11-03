"""This module contains handlers for adding and deleting records in the database."""

import logging
import random

import yaml
from aiogram import Bot, F, Router, types
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.exceptions import AiogramError
from aiogram.filters import Command
from aiogram.types import error_event
from aiogram.utils import formatting

from src.bot.settings import settings
from src.database import Request
from src.filters import my_filters
from src.utility.platinum_record import PlatinumRecord

records_router = Router(name=__name__)

QUOTATION_KEYS = ("quotation", "author", "game")


def load_quotations(path: str = "src/data/quotations.yaml") -> list[dict]:
    """Load the quotations, skipping entries that miss a field."""

    with open(path, "r", encoding="utf8") as file:
        items = yaml.safe_load(file)["quotations"]

    valid = []
    for item in items:
        if isinstance(item, dict) and all(item.get(key) for key in QUOTATION_KEYS):
            valid.append(item)
        else:
            logging.warning(f"Skipping malformed quotation: {item!r}")

    return valid


quotations = load_quotations()


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


@records_router.message(F.photo, my_filters.platinum_check)
async def add_record(message: types.Message, bot: Bot, request: Request) -> None:
    """Add record to the database."""

    chat_id = message.chat.id
    username = message.from_user.username
    user_id = message.from_user.id
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

    is_default = game == "*Default*"
    if is_default:
        if not await check_permissions(message):
            return
        username = "*Default*"

    # Save first, so a problem with the reply can't lose the trophy.
    if username is not None:
        record = PlatinumRecord(username, game, file_id, platform, user_id)
        await request.add_record(chat_id=chat_id, record=record)

    if is_default:
        text = "Стандартный аватар установлен"
    else:
        quotation = random.choice(quotations)
        text = formatting.as_list(
            formatting.Text(formatting.Italic(f" \"{quotation['quotation']}\" ©", "\n")),
            formatting.Text(f"{quotation['author']}", "\n", f"{quotation['game']}"),
        ).as_html()

    await message.reply(text)


@records_router.message(Command("delete_game"))
async def delete_game(message: types.Message, bot: Bot, request: Request):
    """Delete record from the database."""

    chat_id = message.chat.id
    username = message.from_user.username
    user_id = message.from_user.id

    text = await request.delete_record(
        chat_id=chat_id, username=username, user_id=user_id
    )

    await message.reply(text)


@records_router.error()
async def error_handler(event: error_event.ErrorEvent, bot: Bot) -> None:
    """Handle errors in records router."""

    content = formatting.as_list(
        formatting.Text(f"Ошибка в {__name__}:"),
        formatting.Pre(event.exception),
    )
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text=content.as_html())
