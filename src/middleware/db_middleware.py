"""Middleware for working with the database."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.database import Request


class DBSession(BaseMiddleware):
    """Middleware for working with the database."""

    def __init__(self, request: Request):
        super().__init__()
        self.request = request

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["request"] = self.request
        return await handler(event, data)
