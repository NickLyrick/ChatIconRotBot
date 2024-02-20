"""Module with handlers for wiki."""

from aiogram import Router, types
from aiogram.filters import Command
import wikipedia
from wikipedia import exceptions as wikiexceptions

from src.database import Request

wiki_router = Router()


@wiki_router.message(Command('games_info'))
async def games_info(message: types.Message, reqest: Request):
    """Send information about games from the queue to the chat."""

    chat_id = message.chat.id

    data = await reqest.get_queue(chat_id)

    text = ""
    for i, record in enumerate(data, start=1):
        game = record[1]

        try:
            page = wikipedia.page(game)
            url = f"[{game}]({page.url})"
        except wikiexceptions.PageError:
            results = wikipedia.search(game)
            try:
                page = wikipedia.page(results[0])
                url = f"[{game}]({page.url} )"
            except wikiexceptions.PageError:
                url = "Информация не найдена"
        except wikiexceptions.DisambiguationError:
            url = "Информация не найдена"

        text += f"{i}) {url} \n"

    await message.reply(text, parse_mode="Markdown")
