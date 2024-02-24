"""This module contains the bot instance."""

from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode

from src.bot.settings import settings

bot = Bot(token=settings.bot.bot_token, parse_mode=ParseMode.HTML)
