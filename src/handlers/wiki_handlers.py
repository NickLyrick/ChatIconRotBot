"""Module with handlers for wiki."""

import wikipedia
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils import formatting
from wikipedia import exceptions as wiki_exceptions

from src.database import Request

from . import error_handler

wiki_router = Router(name=__name__)


@wiki_router.message(Command("games_info"))
async def games_info(message: types.Message, request: Request):
    """Send information about games from the queue to the chat."""

    chat_id = message.chat.id

    try:
        data = await request.get_records_data(chat_id)
    except Exception as e:
        await message.reply(
            text=f"Не удалось получить информацию о играх\n\n"
            f"Ошибка: \n"
            f"{formatting.Pre(e).as_html()}"
        )
        return

    links_list = []
    for _, game in data:
        try:
            page = wikipedia.page(game + " video game")
            url = formatting.TextLink(game, url=page.url)
        except wiki_exceptions.PageError:
            results = wikipedia.search(game + " video game")
            if len(results) > 0:
                try:
                    page = wikipedia.page(results[0])
                    url = formatting.TextLink(game, url=page.url)
                except wiki_exceptions.PageError:
                    url = game
        except wiki_exceptions.DisambiguationError:
            url = game

        links_list.append(url)

    if len(links_list) == 0:
        return await message.reply("Информация не найдена")

    content = formatting.as_list(
        formatting.as_numbered_section(formatting.Bold("Список ссылок:"), *links_list)
    )

    await message.reply(**content.as_kwargs())


# Add error handler to the router
error_handler = wiki_router.error(error_handler)
