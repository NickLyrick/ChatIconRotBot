"""Configuration for bot"""

from dataclasses import dataclass
from datetime import timedelta
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
class Scheduler:
    """Configuration for Scheduler"""

    # TODO: replace by right values after testing
    auto_delete_message_from_groups: timedelta = timedelta(minutes=1)
    auto_delete_message_from_private: timedelta = timedelta(minutes=1)


@dataclass
class Settings:
    """Configuration for bot and DataBase"""

    bot: Bot
    db: DB
    scheduler: Scheduler


settings = Settings(
    bot=Bot(
        bot_token=environ["TOKEN"],
        # TODO: add admin_ids to environment variables
        admin_ids=[392087623],
        welcome_message="Я жажду платин!",
        chat_help_message=commands.chat_help_text,
        bot_admin_help_message=commands.admin_help_text,
    ),
    db=DB(database_url=environ["DATABASE_URL"]),
)
