"""A module that contains filters for the handlers."""

import dataclasses

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from aiogram.utils import formatting

from src.bot.settings import settings


class CorrectPlatinumRecord(BaseFilter):
    """Check if the message is a correct platinum record."""

    async def __call__(self, message: Message, bot: Bot) -> bool:
        try:
            if message.caption is None:
                return False

            bot = await bot.get_me()
            bot_username = bot.username
            if not message.caption.startswith(f"@{bot_username}"):
                return False

            name = message.caption.replace(f"@{bot_username}", "").strip()
            if len(name) == 0 or name is None:
                await message.answer(
                    text="Платина не добавлена - Не указано название игры"
                )
                return False

            return message.photo is not None
        except Exception as e:
            await message.answer(
                text=f"Не удалось добавить платину:\n\n"
                f"Ошибка: \n"
                f"{formatting.Pre(e)}.as_html()"
            )
            return False


class FromPrivateChat(BaseFilter):
    """Check if the message is from private chat."""

    async def __call__(self, message: Message) -> bool:
        try:
            return message.chat.type == "private"
        except Exception as e:
            await message.answer(text=f"Ошибка: \n" f"{formatting.Pre(e)}.as_html()")
            return False


class FromGroupOrSuperGroup(BaseFilter):
    """Check if the message is from group or supergroup."""

    async def __call__(self, message: Message) -> bool:
        try:
            return message.chat.type in {"group", "supergroup"}
        except Exception as e:
            await message.answer(text=f"Ошибка: \n" f"{formatting.Pre(e)}.as_html()")
            return False


class CheckPermissions(BaseFilter):
    """Check if the user may change the bot settings: the chat owner or a bot admin.

    Works for commands and for presses on the settings menu buttons.
    """

    DENIED_TEXT = "У вас нет прав для изменения настроек бота для данного чата"

    async def __call__(self, event: Message | CallbackQuery, bot: Bot) -> bool:
        is_callback = not isinstance(event, Message)
        chat = event.message.chat if is_callback else event.chat

        try:
            if event.from_user.id in settings.bot.admin_ids:
                return True
            member = await bot.get_chat_member(chat_id=chat.id, user_id=event.from_user.id)
            if member.status == ChatMemberStatus.CREATOR:
                return True
            error_text = self.DENIED_TEXT
        except Exception as e:
            error_text = f"Ошибка: \n{formatting.Pre(e).as_html()}"

        if is_callback:
            await event.answer(text=self.DENIED_TEXT, show_alert=True)
        elif error_text == self.DENIED_TEXT:
            await event.reply(text=error_text)
        else:
            await event.answer(text=error_text)
        return False


@dataclasses.dataclass
class Filters:
    """A class that contains filters for the handlers."""

    platinum_check: CorrectPlatinumRecord
    from_private_chat: FromPrivateChat
    from_group_or_supergroup: FromGroupOrSuperGroup
    check_permissions: CheckPermissions


my_filters = Filters(
    platinum_check=CorrectPlatinumRecord(),
    from_private_chat=FromPrivateChat(),
    from_group_or_supergroup=FromGroupOrSuperGroup(),
    check_permissions=CheckPermissions(),
)
