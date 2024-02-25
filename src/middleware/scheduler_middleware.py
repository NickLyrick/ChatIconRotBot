"""Middleware for the scheduler."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.scheduler.scheduler import Scheduler


class SchedulerMW(BaseMiddleware):
    """Middleware for the scheduler."""

    def __init__(self, scheduler: Scheduler):
        super().__init__()
        self.scheduler = scheduler

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["scheduler"] = self.scheduler
        return await handler(event, data)
