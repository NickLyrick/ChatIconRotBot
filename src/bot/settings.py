"""Configuration for bot"""

from dataclasses import dataclass

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
        # TODO: remove TOKEN and ID's
        bot_token="6731907326:AAHNXMHa_tIWIXGpjeElHG4tc39PDO95jz0",
        admin_ids=[392087623],
        welcome_message="Я жажду платин!",
        chat_help_message=commands.chat_help_text,
        bot_admin_help_message=commands.admin_help_text,
    ),
    db=DB(
        # TODO: insert DATABASE_URL
        database_url="host=127.0.0.1 port=5432 dbname=platinum user=postgres password=210294alexander_I4"
    ),
)
