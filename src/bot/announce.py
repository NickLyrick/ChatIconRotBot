"""Bot-wide setup announced to Telegram and to the admins.

With a webhook the process starts on every incoming update after a sleep, so
this runs once per deploy (see src/release.py) instead of on every start.
With long polling it still runs on start.
"""

from aiogram import Bot
from aiogram.types import BotCommandScopeAllChatAdministrators, BotCommandScopeAllGroupChats

from src.bot.commands import bot_admin_commands, group_chat_commands
from src.bot.settings import settings


async def announce_start(bot: Bot, text: str = "Бот запущен!") -> None:
    """Publish the command lists and tell the admins the bot is up."""

    await bot.set_my_commands(group_chat_commands, BotCommandScopeAllGroupChats())

    for admin_id in settings.bot.admin_ids:
        await bot.set_my_commands(
            group_chat_commands + bot_admin_commands,
            BotCommandScopeAllChatAdministrators(admin_id=admin_id),
        )
        await bot.send_message(admin_id, text=text)
