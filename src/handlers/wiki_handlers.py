"""Module with handlers for wiki."""

import wikipedia
from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.types import error_event
from aiogram.utils import formatting
from wikipedia import exceptions as wiki_exceptions

from src.bot.settings import settings
from src.database import Request

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


@wiki_router.error()
async def error_handler(event: error_event.ErrorEvent, bot: Bot) -> None:
    """Handle errors in wiki router."""

    content = formatting.as_list(
        formatting.Text(f"Ошибка в {__name__}:"),
        formatting.Pre(event.exception),
    )
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text=content.as_html())
