"""Module providing a basic bot functionality."""

from aiogram import Bot
from aiogram import Router, types
from aiogram.filters import CommandStart, Command

from src.bot.settings import settings
from src.filters import my_filters

basic = Router()


@basic.startup()
async def bot_started(bot: Bot) -> None:
    '''Send message to all admins when bot is started.'''

    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text="Бот запущен!")


@basic.shutdown()
async def bot_stopped(bot: Bot) -> None:
    '''Send message to all admins when bot is stopped.'''

    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text="Бот остановлен!")


@basic.message(CommandStart(), my_filters.from_private_chat)
async def command_start(message: types.Message) -> None:
    '''Send wellcome message to user when he starts chat with bot.'''

    # await request.add_user_data(message.from_user.id, message.from_user.username)
    await message.answer(settings.bot.wellcome_message)


@basic.message(Command("help"))
async def help_command(message: types.Message) -> None:
    '''Send help message to user when he uses /help command.'''

    # TODO: decide how to add user_id
    # await request.add_data(message.from_user.id, message.from_user.username)
    if message.chat.type == 'private':
        await message.reply(text=settings.bot.user_help_message)
    else:
        await message.reply(text=settings.bot.chat_help_message)
