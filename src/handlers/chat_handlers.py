from aiogram import Bot, Router, types
from aiogram.filters import Command, CommandObject
from datetime import datetime
from src.database.connect import Request

from src.utility.tools import table

chat_router = Router()


@chat_router.message(Command("show_queue"))
async def show_queue(message: types.Message, request: Request) -> None:
    # TODO: decide what to do with users
    # await request.add_user_data(message.from_user.id, message.from_user.username)
    chat_id = message.chat.id

    data = []
    try:
        data = await request.get_queue(chat_id)
    except Exception as e:
        await message.reply(text=f"Не удалось получить очередь трофеев\n\n"
                                 f"Ошибка: \n"
                                 f"<pre>\n{e}</pre>")

    if len(data) > 0:
        await message.reply(text="Список пуст!")
    else:
        media = table(data, columns=["Nickname", "Game", "Platform"], caption="Очередь трофеев")
        if len(media) > 0:
            await message.reply_media_group(media=media)


@chat_router.message(Command("top"))
async def top(message: types.Message, command: CommandObject, request: Request) -> None:
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
        await message.reply(text=f"Не удалось получить топ от {date}\n\n"
                                 f"Ошибка: \n"
                                 f"<pre>\n{e}</pre>")

    if len(data) > 0:
        media = table(data, columns=["Nickname", "Trophies"], caption=caption)
        if len(media) > 0:
            await message.reply_media_group(media=media)
    else:
        await message.reply("Список пуст!")


@chat_router.message(Command('history'))
async def get_history(message: types.Message, command: CommandObject, request: Request):
    # TODO: decide what to do with users
    # await request.add_user_data(message.from_user.id, message.from_user.username)
    chat_id = message.chat.id
    arguments = command.args

    username = message.from_user.username

    if arguments is not None:
        username = arguments.replace("@", "")

    data = []
    try:
        data = await request.get_history(chat_id=chat_id, hunter=username)
    except Exception as e:
        await message.reply(text=f"Не удалось получить историю от @{username}\n\n"
                                 f"Ошибка: \n"
                                 f"<pre>\n{e}</pre>")

    if len(data) > 0:
        media = table(data, columns=["Game", "Date", "Platform"], caption=f"Список всех трофеев @{username}")
        if len(media) > 0:
            await message.reply_media_group(media=media)
    else:
        await message.reply("Список пуст!")
