#! /bin/env/python

""" Main script Bot  """
import os
import sys
import json
import random
import psycopg2
from psycopg2 import sql

DATABASE_URL = os.environ['DATABASE_URL']


from datetime import datetime, timezone, timedelta

import requests

from bot import BotHandler
from answers import answers

def download_file(url):
    resp = requests.get(url)
    return resp.content

class PlatinumRecord:
    """PlatinumRecord is class for record of platinum"""

    def __init__(self, hunter, game, photo_id):
        super(PlatinumRecord, self).__init__()
        self.hunter = hunter
        self.game = game
        self.photo_id = photo_id

    def __str__(self):
        return "{} {}".format(self.hunter, self.game)

    def __repr__(self):
        return "PlatinumRecord({}, {}, {})".format(self.hunter, self.game, self.photo_id)

    def __eq__(self, other):
        return (self.hunter == other.hunter) and (self.game == other.game)


class Worker:
    """Worker is class for run bot"""

    def __init__(self, bot):
        super(Worker, self).__init__()
        self.bot = bot
        self.offset = 0
        self.update_id = 0
        self.message = dict()
        self.where_run = dict()
        self.commands = {'/help': self.help_command, '/start': self.start_command,
                         '/showqueue': self.showqueue_command,
                         '/deletegame': self.deletegame_command,
                         '/showsettings': self.showsettings_command}

        self.keywords = {'*Date*': self.set_date_chat,
                         '*Delta*': self.set_delta_chat}

        self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')

    def start(self):
        self.get_where_run()
        while True:
            self.bot.get_updates(self.offset)

            last_update = self.bot.get_last_update()

            self.update_id = last_update['update_id']
            if 'message' in last_update:
                self.message = last_update['message']
                last_chat_id = self.message['chat']['id']

                self.process_commands()

                if last_chat_id in self.where_run:
                    self.process_message()

            self.offset = self.update_id

            self.update_avatar()

    def update_avatar(self):
        now = datetime.now()

        for chat_id in self.where_run.keys():
            date = self.where_run[chat_id]['date']
            if date.date() == now.date() and date.hour == now.hour and date.minute == now.minute:
                self.change_avatar(chat_id)
                delta = timedelta(days=int(self.where_run[chat_id]['delta']))
                with self.conn.cursor() as cursor:
                    cursor.execute('''UPDATE chats
                                      SET date=%s
                                      WHERE chat_id=%s''',
                                   (date + delta, chat_id))
                self.conn.commit()
                self.where_run[chat_id]['date'] = date + delta


    def get_where_run(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM chats")
            self.where_run = {chat_id:{'date':date, 'delta':delta}
                              for chat_id, date, delta in cursor.fetchall()}
            print(self.where_run)

    def process_message(self):
        last_chat_id = self.message['chat']['id']
        last_message_id = self.message['message_id']

        if self.update_id > self.offset:
            if 'photo' in self.message:
                caption_entities = self.message.get('caption_entities', list())
                isBotWasMentioned = self.botWasMentioned(caption_entities,
                                                         self.message.get('caption'))

                if isBotWasMentioned:
                    photo_sizes = self.message['photo']
                    file_id = photo_sizes[-1]['file_id']
                    username = self.message['from']['username']
                    game = self.get_game_name(self.message['caption'],
                                              self.message['caption_entities'][0])

                    if game == "*Default*":
                        user_id = self.message['from']['id']
                        if self.check_user_permissions(last_chat_id, user_id):
                            username = "*Default*"
                            text = "Стандартный аватар установлен"
                        else:
                            username = None
                            text = "У вас нет прав для изменения информации группы!"
                    else:
                        text = random.choice(answers['photo'])

                    if not username is None:
                        record = PlatinumRecord(username, game, file_id)
                        self.add_recrod(record)
                    self.bot.send_message(last_chat_id, text, last_message_id)

            if 'text' in self.message:
                last_message_text = self.message.get('text')
                entities = self.message.get('entities', list())
                isBotWasMentioned = self.botWasMentioned(entities, last_message_text)
                username = self.message['from']['username']
                if isBotWasMentioned and username != self.bot.name:
                    self.process_keywords(last_message_text)

    def set_delta_chat(self, delta_str):
        chat_id = self.message['chat']['id']
        user_id = self.message['from']['id']
        if self.check_user_permissions(chat_id, user_id):
            try:
                delta = int(delta_str)
                if delta > 0:
                    with self.conn.cursor() as cursor:
                        cursor.execute("UPDATE chats SET delta=%s WHERE chat_id=%s",
                            (delta, chat_id))
                    self.conn.commit()
                    self.where_run[chat_id]['delta'] = delta
                    text = "Промежуток между сменами фото чата успешно установлен."
                else:
                    text = "Промежуток между сменами фото должен быть больше нуля и целым числом"
            except ValueError:
                text = "Промежуток задан не верно. Пример: @{} *Delta* 3".format(self.bot.name)
        else:
            text = "У вас нет прав для изменения информации группы!"

        self.bot.send_message(chat_id, text, self.message['message_id'])

    def set_date_chat(self, date_str):
        chat_id = self.message['chat']['id']
        user_id = self.message['from']['id']
        if self.check_user_permissions(chat_id, user_id):
            try:
                date = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
                if date > datetime.now():
                    cursor = self.conn.cursor()
                    cursor.execute("UPDATE chats SET date=%s WHERE chat_id=%s", (date, chat_id))
                    self.conn.commit()
                    self.where_run[chat_id]['date'] = date
                    text = "Ближайшая дата смены фото чата успешно установлена."
                else:
                    text = "Ближайшая дата смены оказалась в прошлом. Я не могу изменить прошлое!"
            except ValueError:
                text = "Дата введена неверна. Пример: " \
                       "@{} *Date* 22.07.1941 04:00".format(self.bot.name)
        else:
            text = "У вас нет прав для изменения информации группы!"

        self.bot.send_message(chat_id, text, self.message['message_id'])

    def check_user_permissions(self, chat_id, user_id):
        admins = self.bot.get_chat_admins(chat_id)
        for admin in admins:
            if admin['user']['id'] == user_id:
                if admin['status'] == 'creator':
                    return True
                else:
                    if admin['can_change_info'] == 'true':
                        return True
                    else:
                        return False

    def process_keywords(self, text):
        words = text.split()

        if len(words) >= 2:
            if words[1] in self.keywords:
                self.keywords[words[1]](" ".join(words[2:]))
        else:
            self.bot.send_message(str(self.message['chat']['id']),
                                  random.choice(answers['text']),
                                  self.message['message_id'])


    def process_commands(self):
        chat_id = self.message['chat']['id']

        if 'text' in self.message:
            last_message_text = self.message.get('text')

            command = self.parse_commands(
                last_message_text, self.message.get('entities', list()))
            if self.update_id > self.offset:
                if command in self.commands:
                    if command == "/start":
                        self.commands[command]()
                    elif chat_id in self.where_run:
                        self.commands[command]()

    def add_recrod(self, record):
        chat_id = self.message['chat']['id']

        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM platinum WHERE chat_id=%s AND hunter=%s AND game=%s",
                       (chat_id, record.hunter, record.game))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO platinum VALUES (%s, %s, %s, %s)",
                           (chat_id, record.hunter, record.game, record.photo_id))

        else:
            cursor.execute('''UPDATE platinum
                              SET photo_id=%s
                              WHERE chat_id=%s AND hunter=%s AND game=%s''',
                           (record.photo_id, chat_id, record.hunter, record.game))

        self.conn.commit()

    def get_game_name(self, text, entity):
        offset_mention = int(entity['offset'])
        len_mention = int(entity['length'])

        if offset_mention > 0:
            game = text[0: offset_mention-1]
        else:
            len_text = len(text)
            game = text[offset_mention+len_mention+1:len_text]

        return game

    def botWasMentioned(self, entities, text):
        bot_name = "@" + self.bot.name
        for entity in entities:
            if entity['type'] == 'mention':
                offset_mention = int(entity['offset'])
                len_mention = int(entity['length'])

                if text[offset_mention:offset_mention+len_mention] == bot_name:
                    return True

        return False

    def parse_commands(self, text, entities):
        for entity in entities:
            if entity['type'] == 'bot_command':
                try:
                    text.index("@")
                    words = text.split("@")
                    if words[1] == self.bot.name:
                        return words[0]
                except ValueError:
                    return text
        return ""

    def change_avatar(self, chat_id):
        cursor = self.conn.cursor()

        cursor.execute('''SELECT hunter, game, photo_id
                                 FROM platinum
                                 WHERE chat_id=%s AND hunter!=%s''',
                              (chat_id, "*Default*",))

        records = [PlatinumRecord(*row) for row in cursor.fetchall()]

        if len(records) == 0:
            cursor.execute('''SELECT photo_id
                              FROM platinum
                              WHERE chat_id=%s AND hunter=%s AND game=%s''',
                           (chat_id, "*Default*", "*Default*", ))

            if not cursor.fetchone() is None:
                text = "Новых платин нет. Ставлю стандартный аватар :("
                file_id = cursor.fetchone()[0]
            else:
                text = "Стандартный аватар не задан. Оставляю всё как есть."
                file_id = None

        else:
            record = records[0]

            text = "Поздравляем @{} с платиной в игре \"{}\" !".format(record.hunter,
                                                                       record.game)
            cursor.execute('''DELETE FROM platinum
                              WHERE chat_id=%s AND hunter=%s AND game=%s''',
                           (chat_id, record.hunter, record.game))
            self.conn.commit()

            file_id = record.photo_id

        if not file_id is None:
            photo_url = self.bot.get_file_url(file_id)
            photo = download_file(photo_url)
            self.bot.set_chat_photo(chat_id, photo)

        self.bot.send_message(chat_id, text)

        return True

    def start_command(self):
        chat_id = self.message['chat']['id']

        if chat_id not in self.where_run:
            cursor = self.conn.cursor()
            date = datetime.now(timezone.utc)
            delta = 1
            cursor.execute("INSERT INTO chats VALUES(%s,%s,%s)", (chat_id, date, delta))
            self.conn.commit()
            self.where_run[chat_id] = {'date': date, 'delta': delta}
            self.bot.send_message(chat_id, "Да начнётся охота!")

    def help_command(self):
        text = """Для добавления фото в очередь нужно отправить в чат фото с комментарием следующего вида:

@{0} <название игры>

Картинку необходимо подготовить таким образом, чтобы желаемая область была в центре. В идеале обрезать ее в пропорциях 1:1 оставив желаемую область.

У бота есть следующие команды:

\\start - запуск бота в чате

\\help - вывод справочной информации

\\showqueue - отобразить очередь выбитых платин на данный момент

\\deletegame - удалить последнюю добавленную тобой платину

\\showsettings - показать текущие настройки

У бота есть следующие ключевые слова:

*Date* - задать время ближайщей смены. Пример: @{0} *Date* 22.07.1941 04:00

*Delta* - задать промежуток между сменами. Пример: @{0} *Delta* 3

*Default* - задать фото чата по умолчанию. При отправке фото, вместо названия игры, пишем *Default*

Операции с ключевыми словами доступны только для админов и владельца чата. """.format(self.bot.name)

        chat_id = self.message['chat']['id']
        reply_to_message_id = self.message['message_id']

        self.bot.send_message(chat_id, text, reply_to_message_id)

    def showqueue_command(self):
        chat_id = self.message['chat']['id']
        reply_to_message_id = self.message['message_id']

        text = "Очередь платин:\n"
        cursor = self.conn.cursor()
        cursor.execute('''SELECT hunter, game, photo_id FROM platinum
                                WHERE chat_id=%s AND hunter!=%s AND game!=%s''',
                              (chat_id, "*Default*", "*Default*"))

        platinum_chat = [PlatinumRecord(*row) for row in cursor.fetchall()]

        text_record = "\n".join(str(record) for record in platinum_chat)

        self.bot.send_message(chat_id, text+text_record, reply_to_message_id)

    def deletegame_command(self):
        chat_id = self.message['chat']['id']
        reply_to_message_id = self.message['message_id']
        username = self.message['from']['username']

        cursor = self.conn.cursor()
        cursor.execute('''SELECT hunter, game, photo_id FROM platinum
                                WHERE chat_id=%s AND hunter=%s''', (chat_id, username))
        records_user = [PlatinumRecord(*row) for row in cursor.fetchall()]

        if len(records_user) == 0:
            text = "Удалять у {} нечего. Поднажми!".format(username)
        else:
            record = records_user[-1]
            cursor.execute('''DELETE FROM platinum
                            WHERE chat_id=%s AND hunter=%s AND game=%s''',
                           (chat_id, record.hunter, record.game))
            text = "Платина в игре {} игрока {} успешно удалена".format(
                record.game, record.hunter)

            self.conn.commit()

        self.bot.send_message(chat_id, text, reply_to_message_id)

    def showsettings_command(self):
        chat_id = self.message['chat']['id']
        reply_to_message_id = self.message['message_id']

        cursor = self.conn.cursor()
        cursor.execute("SELECT date, delta FROM chats WHERE chat_id=%s", (chat_id,))
        date, delta = cursor.fetchone()
        text = "Ближайшая дата смены: {}.\n" \
               "Промежуток между сменами: {}д.".format(date.strftime("%d.%m.%Y %H:%M"), delta)

        cursor.execute('''SELECT photo_id
                          FROM platinum
                          WHERE chat_id=%s AND hunter=%s''',
                       (chat_id, '*Default*'))
        row = cursor.fetchone()
        if not row is None:
            photo_id = row[0]
            self.bot.send_photo(chat_id, photo_id, text, reply_to_message_id)
        else:
            self.bot.send_message(chat_id, text, reply_to_message_id)



def get_date(data, hour):
    day, month, year = map(int, data.split('.'))

    return datetime(day=day, month=month,
                    year=year, hour=int(hour),
                    tzinfo=timezone.utc)


def main():
    token = os.environ["TOKEN"]
    bot = BotHandler(token)
    worker = Worker(bot)
    print("{}".format(bot.api_url))

    worker.start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
