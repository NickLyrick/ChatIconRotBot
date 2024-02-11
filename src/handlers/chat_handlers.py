from aiogram import Bot, Router, types
from aiogram.filters import Command, CommandObject
from datetime import datetime
from src.database.connect import Request

from src.utility.tools import table

chat_router = Router()


@chat_router.message(Command("show_queue"))
async def show_queue(message: types.Message, bot: Bot, request: Request) -> None:
    # TODO: decide what to do with users
    # await request.add_user_data(message.from_user.id, message.from_user.username)
    chat_id = message.chat.id

    data = await request.get_queue(chat_id)

    if len(data) == 0:
        await message.reply("Список пуст!")
    else:
        media = table(data, ["Nickname", "Game", "Platform"])
        media[0].caption = "Очередь трофеев"
        await bot.send_media_group(chat_id=chat_id, media=media)


@chat_router.message(Command("top"))
async def top(message: types.Message, bot: Bot, command: CommandObject, request: Request) -> None:
    # TODO: decide what to do with users
    # await request.add_user_data(message.from_user.id, message.from_user.username)
    chat_id = message.chat.id

    arguments = command.args
    date = datetime(1980, 1, 1)

    caption = "Топ за всё время"
    if arguments is not None:
        try:
            date = datetime.strptime(arguments, '%d.%m.%Y')
            caption = f"Топ от {arguments}"
        except ValueError:
            caption = "Топ за всё время"

    data = []
    try:
        data = await request.get_top(chat_id=chat_id, date=date)
        print(data)
    except Exception as e:
        await message.reply(text=f"Не удалось получить топ от {date}"
                                 f"Ошибка: {e}")

    if len(data) > 0:
        media = table(data, ["Nickname", "Trophies"])
        media[0].caption = caption
        await bot.send_media_group(chat_id=chat_id, media=media)
    else:
        await message.reply("Список пуст!")
