from dataclasses import dataclass

chat_help_text = """У бота есть следующие команды:

\\start - запуск бота в чате

\\help - вывод справочной информации

\\show_queue - отобразить очередь выбитых трофеев на данный момент

\\history - показать выбитые трофеи. По умолчанию свои. Можно запросить трофеи любого пользователя.

\\top - топ выбитых трофеев за всё время или за указанный промежуток.

\\games_info - показать информацию (Wikipedia) об играх из очереди
"""

user_help_text = ("\"Для добавления фото в очередь нужно боту фото с описанием следующего вида:\n"
                  "название игры платформа\n"
                  "\n"
                  "Если платформа не указана, от будет выставлена платформа по умолчанию.\n"
                  "По умолчанию платформа - Playstation.\n"
                  "\n"
                  "Картинку необходимо подготовить таким образом, чтобы желаемая область была в центре. \n"
                  "В идеале обрезать ее в пропорциях 1:1 оставив желаемую область.\n"
                  "\n"
                  "У бота есть следующие команды:\n"
                  "\\start - запуск бота в чате\n"
                  "\\help - вывод справочной информации\n"
                  "\\delete_game - удалить последний добавленный тобой трофей\n"
                  "")


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
print(settings)
