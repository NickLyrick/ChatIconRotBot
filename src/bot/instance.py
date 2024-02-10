from aiogram import Bot

from src.bot.settings import settings

bot = Bot(
    token=settings.bot.bot_token,
    parse_mode='HTML'
)
