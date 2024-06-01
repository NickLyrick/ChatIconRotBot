"""Configuration for bot"""

from dataclasses import dataclass
from os import environ

from src.bot import commands


@dataclass
class Bot:
    """Configuration for bot"""

    bot_token: str
    admin_ids: list[int]
    welcome_message: str
    chat_help_message: str
    bot_admin_help_message: str


@dataclass
class DB:
    """Configuration for DataBase"""

    database_url: str


@dataclass
class Settings:
    """Configuration for bot and DataBase"""

    bot: Bot
    db: DB


settings = Settings(
    bot=Bot(
        bot_token=environ["TOKEN"],
        # TODO: add admin_ids to environment variables
        admin_ids=[392087623],
        welcome_message="Я жажду платин!",
        chat_help_message=commands.CHAT_HELP_TEXT,
        bot_admin_help_message=commands.ADMIN_HELP_TEXT,
    ),
    db=DB(database_url=environ["DATABASE_URL"]),
)
