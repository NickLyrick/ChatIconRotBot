"""Module providing a basic bot functionality."""

# TODO: Implement user chat commands
from aiogram import Bot, Router, types
from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeAllGroupChats,
    error_event,
)
from aiogram.utils import formatting

from src.bot.commands import bot_admin_commands, group_chat_commands
from src.bot.settings import settings
from src.filters import my_filters

basic_router = Router(name=__name__)


@basic_router.startup()
async def bot_started(bot: Bot) -> None:
    """Send message to all admins when bot is started."""

    await bot.set_my_commands(group_chat_commands, BotCommandScopeAllGroupChats())

    for admin_id in settings.bot.admin_ids:
        await bot.set_my_commands(
            group_chat_commands + bot_admin_commands,
            BotCommandScopeAllChatAdministrators(admin_id=admin_id),
        )
        await bot.send_message(admin_id, text="Бот запущен!")


@basic_router.shutdown()
async def bot_stopped(bot: Bot) -> None:
    """Send message to all admins when bot is stopped."""

    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text="Бот остановлен!")


@basic_router.message(CommandStart(), my_filters.from_private_chat)
async def command_start(message: types.Message) -> None:
    """Send welcome message to user when he starts chat with bot."""

    await message.answer(settings.bot.welcome_message)


@basic_router.message(Command("help"))
async def help_admin_command(message: types.Message) -> None:
    """Send help message to admin when he uses /help command."""

    member = await message.chat.get_member(message.from_user.id)
    if (
        member.status == ChatMemberStatus.CREATOR
        or member.user.id in settings.bot.admin_ids
    ):
        await message.reply(
            text=settings.bot.chat_help_message
            + "\n\n"
            + settings.bot.bot_admin_help_message
        )
    else:
        await message.reply(text=settings.bot.chat_help_message)


@basic_router.error()
async def error_handler(event: error_event.ErrorEvent, bot: Bot) -> None:
    """Handle errors."""

    content = formatting.as_list(
        formatting.Text(f"Ошибка в {__name__}:"),
        formatting.Pre(event.exception),
    )
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text=content.as_html())
