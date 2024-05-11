"""This module contains the Scheduler class."""

from datetime import datetime, timedelta, timezone

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.bot.settings import settings
from src.database import Request
from src.scheduler.jobs import (
    change_avatar,
    check_db_connection,
    delete_message,
    finish_survey,
)


class Scheduler:
    """Scheduler class."""

    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
        self.where_run = {}

    async def start(self, bot: Bot, request: Request):
        """Start the scheduler."""

        self.scheduler.start()

        # Schedule checking connection to DB
        # Set max_lifetime in AsyncConnectionPool
        start_db_check = datetime.now(timezone.utc) + timedelta(minutes=1)
        self.scheduler.add_job(
            check_db_connection,
            "interval",
            minutes=1,
            start_date=start_db_check,
            kwargs={"bot": bot, "request": request},
        )

        # Get chats where the bot is running
        self.where_run = await request.get_chats()

        # Schedule change avatar job for each chat
        for chat_id in self.where_run:
            chat = await bot.get_chat(chat_id=chat_id)

            # Skip private chats
            if chat.type == "private":
                continue

            date = self.where_run[chat_id]["date"]
            delta = self.where_run[chat_id]["delta"]
            await self.add_change_avatar_job(bot, request, chat_id, date, delta)

            # Survey Results each 1st day of the month in 09:00 UTC
            self.scheduler.add_job(
                func=finish_survey,
                trigger=CronTrigger.from_crontab("7 22 6 * *"),
                id=f"{chat_id}_survey",
                kwargs={"bot": bot, "request": request, "chat_id": chat_id},
                replace_existing=True,
            )

    async def add_change_avatar_job(self, bot, request, chat_id, date, delta):
        """Add a job to the scheduler."""

        job = self.scheduler.get_job(str(chat_id))

        if job is None:
            self.scheduler.add_job(
                func=change_avatar,
                trigger="interval",
                days=1,
                start_date=date,
                id=str(chat_id),
                kwargs={
                    "bot": bot,
                    "request": request,
                    "chat_id": chat_id,
                    "where_run": self.where_run,
                    "scheduler": self.scheduler,
                },
            )
        else:
            if date is None:
                date = self.where_run[chat_id]["date"]
                self.where_run[chat_id]["delta"] = delta
            if delta is None:
                delta = self.where_run[chat_id]["delta"]
                self.where_run[chat_id]["date"] = date

            job.reschedule(trigger="interval", days=delta, start_date=date)

    def add_delete_message(self, bot: Bot, chat_id: int, message_id: int):
        """Add a job delete message to the scheduler"""

        date_delete = (
            datetime.now(timezone.utc)
            + settings.scheduler.auto_delete_message_from_private
            - timedelta(hours=1)
        )
        self.scheduler.add_job(
            func=delete_message,
            trigger="date",
            run_date=date_delete,
            kwargs={"bot": bot, "chat_id": chat_id, "message_id": message_id},
            replace_existing=True,
            id=f"{chat_id}_{message_id}",
        )
