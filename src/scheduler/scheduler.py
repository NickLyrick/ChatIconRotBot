"""This module contains the Scheduler class."""

from datetime import datetime, timedelta, timezone

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.database import Request
from src.scheduler.jobs import change_avatar, check_db_connection, finish_survey


class Scheduler:
    """Scheduler class."""

    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
        self.where_run = {}

    async def start(self, bot: Bot, request: Request):
        """Start the scheduler."""

        self.scheduler.start()

        self.where_run = await request.get_chats()

        # Set max_lifetime in AsyncConnectionPool
        start_db_check = datetime.now(timezone.utc) + timedelta(minutes=1)
        self.scheduler.add_job(
            check_db_connection,
            "interval",
            minutes=1,
            start_date=start_db_check,
            args=[bot, request],
        )

        for chat_id in self.where_run:
            chat = await bot.get_chat(chat_id=chat_id)

            # Skip private chats
            if chat.type == "private":
                continue

            date = self.where_run[chat_id]["date"]
            delta = self.where_run[chat_id]["delta"]
            await self.add_change_avatar_job(bot, request, chat_id, date, delta)

            # Check if the last survey is finished
            await finish_survey(bot=bot, request=request, chat_id=chat_id)
            # Survey Results each 1st day of the month in 09:00 UTC
            self.scheduler.add_job(
                func=finish_survey,
                trigger=CronTrigger.from_crontab("7 22 6 * *"),
                id=f"{chat_id}_survey",
                args=[bot, request, chat_id],
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
                args=[bot, request, chat_id, self.where_run],
            )
        else:
            if date is None:
                date = self.where_run[chat_id]["date"]
                self.where_run[chat_id]["delta"] = delta
            if delta is None:
                delta = self.where_run[chat_id]["delta"]
                self.where_run[chat_id]["date"] = date

            job.reschedule(trigger="interval", days=delta, start_date=date)
            job.modify(args=[bot, request, chat_id, self.where_run])
