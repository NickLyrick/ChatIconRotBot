from aiogram import Bot, Router, types
from aiogram.filters import Command

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
