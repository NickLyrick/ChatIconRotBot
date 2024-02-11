from aiogram import Bot
from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from datetime import datetime, timezone
from aiogram import F

from src.bot.settings import settings
from src.filters.platinum import CorrectPlatinumRecord
from src.database.connect import Request

basic = Router()


@basic.startup()
async def bot_started(bot: Bot) -> None:
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text="Бот запущен!")


@basic.shutdown()
async def bot_stopped(bot: Bot) -> None:
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text="Бот остановлен!")


@basic.message(CommandStart())
async def command_start(message: types.Message, bot: Bot, request: Request) -> None:
    await request.add_user_data(message.from_user.id, message.from_user.username)

    # TODO: add filter for private non-private
    if message.chat.type == 'private':
        await message.answer(settings.bot.wellcome_message)
    else:
        chat_id = message.chat.id
        where_run = await request.get_chats()

        if chat_id not in where_run:
            await request.add_chat_data(chat_id, datetime.now(timezone.utc), 1)
            where_run = await request.get_chats()
            # TODO: add job
            # add_job(chat_id, date, delta)

            await bot.send_message(chat_id, "Да начнётся охота!")


@basic.message(Command("help"))
async def help_command(message: types.Message) -> None:
    # TODO: decide how to add user_id
    # await request.add_data(message.from_user.id, message.from_user.username)
    if message.chat.type == 'private':
        await message.reply(text=settings.bot.user_help_message)
    else:
        await message.reply(text=settings.bot.chat_help_message)


@basic.message(F.photo, CorrectPlatinumRecord())
async def add_platinum_record(message: types.Message) -> None:
    await message.answer(text="Платина добавлена корректно")
