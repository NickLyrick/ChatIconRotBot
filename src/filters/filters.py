import dataclasses

from aiogram.enums import ChatMemberStatus
from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram import Bot


class CorrectPlatinumRecord(BaseFilter):
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
                await message.answer(text="Платина не добавлена - Не указано название игры")
                return False

            return message.photo is not None
        except Exception as e:
            await message.answer(text=f"Не удалось добавить платину:\n\n"
                                      f"Ошибка: \n"
                                      f"<pre>\n{e}</pre>")
            return False


class FromPrivateChat(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        try:
            return message.chat.type == 'private'
        except Exception as e:
            await message.answer(text=f"Ошибка: \n"
                                      f"<pre>\n{e}</pre>")
            return False


class FromGroupOrSuperGroup(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        try:
            return message.chat.type == 'group' or message.chat.type == 'supergroup'
        except Exception as e:
            await message.answer(text=f"Ошибка: \n"
                                      f"<pre>\n{e}</pre>")
            return False


class CheckPermissions(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        try:
            member = await message.chat.get_member(message.from_user.id)
            if member.status == ChatMemberStatus.CREATOR or member.can_change_info:
                return True
            else:
                await message.reply(text="У вас нет прав для изменения настроек бота для данного чата")
                return False
        except Exception as e:
            await message.answer(text=f"Ошибка: \n"
                                      f"<pre>\n{e}</pre>")
            return False


@dataclasses.dataclass
class Filters:
    platinum_check: CorrectPlatinumRecord
    from_private_chat: FromPrivateChat
    from_group_or_supergroup: FromGroupOrSuperGroup
    check_permissions: CheckPermissions


def get_filters() -> Filters:
    return Filters(
        platinum_check=CorrectPlatinumRecord(),
        from_private_chat=FromPrivateChat(),
        from_group_or_supergroup=FromGroupOrSuperGroup(),
        check_permissions=CheckPermissions()
    )


my_filters = get_filters()