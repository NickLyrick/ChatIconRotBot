"""Set bot commands in all Scopes"""

# Import Chat Scopes
from aiogram.types import BotCommand

# TODO: Implement user_chat_commands

group_chat_commands = [
    BotCommand(command="start", description="Запуск бота в чате"),
    BotCommand(command="help", description="Вывод справочной информации"),
    BotCommand(command="show_queue", description="Отобразить очередь выбитых трофеев"),
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

chat_help_text = f"""
<b>У бота есть следующие команды</b>:

/{group_chat_commands[0].command} - запуск бота в чате
/{group_chat_commands[1].command} - вывод справочной информации
/{group_chat_commands[2].command} - отобразить очередь выбитых трофеев на данный момент
/{group_chat_commands[3].command} - показать историю выбитых трофеев. По умолчанию своих. Можно запросить историю любого пользователя.
/{group_chat_commands[4].command} - топ выбитых трофеев за всё время или за указанный промежуток.
/{group_chat_commands[5].command} - показать информацию (Wikipedia) об играх из очереди
"""

admin_help_text = f"""
<b>Для администраторов бота доступны следующие команды:</b>
/{bot_admin_commands[0].command} - Показать текущие настройки
/{bot_admin_commands[1].command} - Задать время ближайшей смены. Пример: /date 22/07/1941 04:00
/{bot_admin_commands[2].command} - Задать промежуток между сменами. Пример: /delta 3
"""
