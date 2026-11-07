"""Set bot commands in all Scopes"""

# Import Chat Scopes
from aiogram.types import BotCommand
from aiogram.utils import formatting

group_chat_commands = [
    BotCommand(command="start", description="Запуск бота в чате"),
    BotCommand(command="help", description="Вывод справочной информации"),
    BotCommand(command="show_queue", description="Отобразить очередь выбитых трофеев"),
    BotCommand(
        command="delete_game",
        description="Удалить последний добавленный пользователем трофей",
    ),
    BotCommand(
        command="history",
        description="Показать твои выбитые трофеев. Можно запросить трофеи любого пользователя",
    ),
    BotCommand(
        command="top",
        description="Топ выбитых трофеев за всё время или за указанный промежуток",
    ),
    BotCommand(
        command="games_info",
        description="Показать информацию (Wikipedia) об играх из очереди",
    ),
]

bot_admin_commands = [
    BotCommand(command="show_settings", description="Показать текущие настройки"),
    BotCommand(
        command="set_date",
        description="Задать время ближайшей смены по МСК: /set_date ДД/ММ/ГГГГ ЧЧ:ММ",
    ),
    BotCommand(
        command="set_delta",
        description="Задать промежуток между сменами в днях (1–365). Пример: /set_delta 3",
    ),
]

CHAT_HELP_TEXT = formatting.Bold("У бота есть следующие команды:").as_html() + "\n"
for command in group_chat_commands:
    CHAT_HELP_TEXT += f"\n/{command.command} - {command.description}"

ADMIN_HELP_TEXT = (
    formatting.Bold("Для администраторов бота доступны следующие команды:").as_html()
    + "\n"
)
for command in bot_admin_commands:
    ADMIN_HELP_TEXT += f"\n/{command.command} - {command.description}"
