"""This module contains the Scheduler class."""

from typing import Callable
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.database import Request


class Scheduler:
    """Scheduler class."""

    def __init__(self, scheduler: AsyncIOScheduler, bot: Bot, request: Request):
        self.scheduler = scheduler
        self.where_run = {}
        self.bot = bot
        self.request = request

    async def start(self, avatar_func: Callable[[Bot, Request, int, dict], None]):
        """Start the scheduler."""

        self.scheduler.start()

        self.where_run = await self.request.get_chats()

        for chat_id in self.where_run:
            chat = await self.bot.get_chat(chat_id=chat_id)
            if chat.type == 'private':
                continue
            date = self.where_run[chat_id]["date"]
            delta = self.where_run[chat_id]["delta"]
            await self.add_change_avatar_job(chat_id=chat_id,
                                             date=date,
                                             delta=delta,
                                             func=avatar_func)

    async def add_check_db(self, func: Callable[[Bot, Request], None]):
        """Check connection to DB"""
        start_db_check = datetime.now(timezone.utc) + timedelta(minutes=1)
        self.scheduler.add_job(
            func,
            "interval",
            minutes=1,
            start_date=start_db_check,
            args=[self.bot, self.request],
        )

    async def add_change_avatar_job(self,
                                    func: Callable[[Bot, Request, int, dict], None],
                                    chat_id: int,
                                    date: datetime,
                                    delta: timedelta):
        """Add a job to the scheduler."""

        job = self.scheduler.get_job(str(chat_id))

        if job is None:
            self.scheduler.add_job(
                func=func,
                trigger="interval",
                days=1,
                start_date=date,
                id=str(chat_id),
                args=[self.bot, self.request, chat_id, self.where_run],
            )
        else:
            if date is None:
                date = self.where_run[chat_id]["date"]
                self.where_run[chat_id]["delta"] = delta
            if delta is None:
                delta = self.where_run[chat_id]["delta"]
                self.where_run[chat_id]["date"] = date

            job.reschedule(trigger="interval", days=delta, start_date=date)
            job.modify(args=[self.bot, self.request, chat_id, self.where_run])
