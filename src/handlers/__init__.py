"""This module represent handlers library"""

from aiogram import Bot
from aiogram.types import error_event
from aiogram.utils import formatting

from src.bot.settings import settings


async def error_handler(event: error_event.ErrorEvent, bot: Bot) -> None:
    """Handle errors."""

    content = formatting.as_list(
        formatting.Text(f"Ошибка в {__name__}:"),
        formatting.Pre(event.exception),
    )
    for admin_id in settings.bot.admin_ids:
        await bot.send_message(admin_id, text=content.as_html())
