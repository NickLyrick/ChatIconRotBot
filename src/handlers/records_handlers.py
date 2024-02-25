"""This module contains handlers for adding and deleting records in the database."""

import random

from aiogram import Bot, F, Router, types
from aiogram.enums import ChatAction
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.exceptions import AiogramError
from aiogram.filters import Command
from aiogram.utils.chat_action import ChatActionSender

from src.database import Request
from src.filters import my_filters
from src.utility.answers import quotations
from src.utility.platinum_record import PlatinumRecord

records_router = Router()


async def check_permissions(message: types.Message) -> bool:
    """Check if user has permissions to change group info."""

    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status == ChatMemberStatus.CREATOR or member.can_change_info
    except AiogramError as e:
        await message.reply(
            text=f"Не хватает прав для изменения информации группы!\n"
            f"Ошибка: \n"
            f"<pre>\n{e}</pre>"
        )


# TODO: Split on 2 functions. Process Default avatar separately. Use my_filter.check_permissions and remove 17-24
@records_router.message(F.photo, my_filters.platinum_check)
async def add_record(message: types.Message, bot: Bot, request: Request) -> None:
    """Add record to the database."""

    action_sender = ChatActionSender(
        action=ChatAction.TYPING, chat_id=message.chat.id, bot=bot
    )

    try:
        async with action_sender:
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

            text = random.choice(quotations)
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
    except Exception as e:
        await message.answer(text=f"Ошибка: \n" f"<pre>\n{e}</pre>")


@records_router.message(Command("delete_game"))
async def delete_game(message: types.Message, bot: Bot, request: Request):
    """Delete record from the database."""

    action_sender = ChatActionSender(
        action=ChatAction.TYPING, chat_id=message.chat.id, bot=bot
    )

    try:
        async with action_sender:
            chat_id = message.chat.id
            username = message.from_user.username

            text = await request.delete_record(chat_id=chat_id, username=username)

            await message.reply(text)
    except Exception as e:
        await message.answer(text=f"Ошибка: \n" f"<pre>\n{e}</pre>")