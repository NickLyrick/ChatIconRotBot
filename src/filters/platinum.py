from aiogram.filters import BaseFilter
from aiogram.types import Message


class CorrectPlatinumRecord(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        try:
            return message.caption is not None and message.photo is not None
        except:
            return False
