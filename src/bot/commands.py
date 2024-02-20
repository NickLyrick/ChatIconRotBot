"""Set bot commands in all Scopes"""

from aiogram import Bot
from aiogram.types import BotCommand

# Import Chat Scopes
from aiogram.types import BotCommandScopeAllGroupChats
from aiogram.types import BotCommandScopeAllPrivateChats
from aiogram.types import BotCommandScopeAllChatAdministrators

from src.bot.settings import settings

group_chat_commands = [
    BotCommand(
        command="start",
        description="Запуск бота в чате"
    ),
    BotCommand(
        command="help",
        description="Вывод справочной информации"
    ),
    BotCommand(
        command="show_queue",
        description="Отобразить очередь выбитых трофеев"
    ),
    BotCommand(
        command="history",
        description="Показать твои выбитые трофеев. Можно запросить трофеи любого пользователя"
    ),
    BotCommand(
        command="top",
        description="Топ выбитых трофеев за всё время или за указанный промежуток"
    ),
    BotCommand(
        command="games_info",
        description="Показать информацию (Wikipedia) об играх из очереди"
    )
]

user_chat_commands = [
    BotCommand(
        command="start",
        description="Запуск бота в чате"
    ),
    BotCommand(
        command="help",
        description="Вывод справочной информации"
    ),
    BotCommand(
        command="delete_game",
        description="Удалить последний добавленный тобой трофей"
    )
]

bot_admin_commands = [
    BotCommand(
        command="show_settings",
        description="Показать текущие настройки"
    ),
    BotCommand(
        command="set_date",
        description="Задать время ближайшей смены. Пример: \\date 22/07/1941 04:00"
    ),
    BotCommand(
        command="set_delta",
        description="Задать промежуток между сменами. Пример: \\delta 3"
    )

]


async def set_bot_commands(bot: Bot) -> None:
    """Set bot commands in all Scopes"""

    await bot.set_my_commands(group_chat_commands, BotCommandScopeAllGroupChats())
    await bot.set_my_commands(user_chat_commands, BotCommandScopeAllPrivateChats())

    for admin_id in settings.bot.admin_ids:
        await bot.set_my_commands(group_chat_commands + bot_admin_commands,
                                  BotCommandScopeAllChatAdministrators(admin_id=admin_id))
