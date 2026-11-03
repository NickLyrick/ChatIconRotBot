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
class Webhook:
    """Configuration for receiving updates over a webhook.

    Without ``base_url`` the bot falls back to long polling (local development).
    """

    base_url: str | None
    secret: str | None
    jobs_secret: str | None
    path: str = "/webhook"
    host: str = "0.0.0.0"
    port: int = 8080

    @property
    def enabled(self) -> bool:
        """Whether the bot runs as a webhook server."""

        return bool(self.base_url)

    @property
    def url(self) -> str:
        """The public URL Telegram posts updates to."""

        return self.base_url.rstrip("/") + self.path


@dataclass
class Settings:
    """Configuration for bot and DataBase"""

    bot: Bot
    db: DB
    webhook: Webhook


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
    webhook=Webhook(
        base_url=environ.get("WEBHOOK_BASE_URL"),
        secret=environ.get("WEBHOOK_SECRET"),
        jobs_secret=environ.get("JOBS_SECRET"),
        port=int(environ.get("PORT", "8080")),
    ),
)
