"""Set bot commands in all Scopes"""

# Import Chat Scopes
from aiogram.types import BotCommand
from aiogram.utils import formatting

# TODO: Implement user_chat_commands

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
        description="Задать время ближайшей смены. Пример: /date 22/07/1941 04:00",
    ),
    BotCommand(
        command="set_delta",
        description="Задать промежуток между сменами. Пример: /delta 3",
    ),
]

chat_help_text = formatting.Bold("У бота есть следующие команды:").as_html() + "\n"
for command in group_chat_commands:
    chat_help_text += f"\n/{command.command} - {command.description}"

admin_help_text = (
    formatting.Bold("Для администраторов бота доступны следующие команды:").as_html()
    + "\n"
)
for command in bot_admin_commands:
    admin_help_text += f"\n/{command.command} - {command.description}"
