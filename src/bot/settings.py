from dataclasses import dataclass

chat_help_text = """
<b>У бота есть следующие команды</b>:

<code>\\start</code> - запуск бота в чате
<code>\\help</code> - вывод справочной информации
<code>\\show_queue</code> - отобразить очередь выбитых трофеев на данный момент
<code>\\history</code> - показать выбитые трофеи. По умолчанию свои. Можно запросить трофеи любого пользователя.
<code>\\top</code> - топ выбитых трофеев за всё время или за указанный промежуток.
<code>\\games_info</code> - показать информацию (Wikipedia) об играх из очереди
"""

user_help_text = """
Для добавления фото в очередь нужно отправить боту фото с подписью следующего вида:
<b><code>&lt;название игры&gt;</code></b> <b><code>&lt;платформа&gt;</code></b>

<i>Если <b><code>&lt;платформа&gt;</code></b> не указана, то будет 
выставлено значение по-умолчанию - Playstation.</i>

Картинку необходимо подготовить таким образом, чтобы желаемая область была в центре.
В идеале обрезать ее в пропорциях 1:1 оставив желаемую область.

<b>У бота есть следующие команды:</b>
<code>\\start</code> - запуск бота в чате
<code>\\help</code> - вывод справочной информации
<code>\\delete_game</code> - удалить последний добавленный тобой трофей
"""


@dataclass
class Bot:
    """Configuration for bot"""

    bot_token: str
    admin_ids: list[int]
    wellcome_message: str
    chat_help_message: str
    user_help_message: str


@dataclass
class Settings:
    bot: Bot


def get_settings() -> Settings:
    return Settings(
        bot=Bot(
            bot_token="6731907326:AAHNXMHa_tIWIXGpjeElHG4tc39PDO95jz0",
            admin_ids=[
                392087623
            ],
            wellcome_message="Да начнется охота!",
            chat_help_message=chat_help_text,
            user_help_message=user_help_text
        )
    )


settings = get_settings()
