"""Module providing a basic bot functionality."""

# TODO: Implement user chat commands
from aiogram import Bot, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeAllGroupChats,
)

from src.bot.commands import bot_admin_commands, group_chat_commands
from src.bot.settings import settings
from src.filters import my_filters

basic_router = Router()


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

    # await request.add_user_data(message.from_user.id, message.from_user.username)
    await message.answer(settings.bot.welcome_message)


@basic_router.message(Command("help"), my_filters.check_permissions)
async def help_admin_command(message: types.Message) -> None:
    """Send help message to admin when he uses /help command."""

    # TODO: decide how to add user_id
    # await request.add_data(message.from_user.id, message.from_user.username)
    if message.chat.type == "private":
        pass
        # await message.reply(text=settings.bot.user_help_message)
    else:
        await message.reply(
            text=settings.bot.chat_help_message + settings.bot.bot_admin_help_message
        )


@basic_router.message(Command("help"))
async def help_command(message: types.Message) -> None:
    """Send help message to user when he uses /help command."""

    # TODO: decide how to add user_id
    # await request.add_data(message.from_user.id, message.from_user.username)
    if message.chat.type == "private":
        pass
        # await message.reply(text=settings.bot.user_help_message)
    else:
        await message.reply(text=settings.bot.chat_help_message)
