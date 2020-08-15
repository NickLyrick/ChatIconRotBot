#! /bin/env/python

""" Main script Bot  """
import sys
import json
import random
import sqlite3

from datetime import datetime, timezone, timedelta

import requests

from bot import BotHandler
from answers import answers


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

    def __init__(self, bot, date, delta):
        super(Worker, self).__init__()
        self.bot = bot
        self.offset = 0
        self.update_id = 0
        self.upd_date = date
        self.delta = delta
        self.message = dict()
        self.commands = {'/help': self.help_command, '/start': self.start_command,
                         '/showqueue': self.showqueue_command,
                         '/deletegame': self.deletegame_command}

        self.conn = sqlite3.connect(
            'platinum.db', detect_types=sqlite3.PARSE_DECLTYPES)

    def start(self):
        while True:
            self.bot.get_updates(self.offset)

            last_update = self.bot.get_last_update()

            self.update_id = last_update['update_id']
            if 'message' in last_update:
                self.message = last_update['message']
                last_chat_id = str(self.message['chat']['id'])

                self.process_commands()

                if last_chat_id in self.where_run:
                    self.process_message()

            self.offset = self.update_id

            now = datetime.now(timezone.utc)
            if now == self.upd_date:
                self.change_avatar()
                self.upd_date = now + self.delta

    def process_message(self):
        last_chat_id = str(self.message['chat']['id'])
        last_message_id = self.message['message_id']

        if 'photo' in self.message:
            isBotWasMentioned = self.botWasMentioned(self.message.get('caption_entities', list()),
                                                     self.message.get('caption'))

            if self.update_id > self.offset:
                if isBotWasMentioned:
                    photo_sizes = self.message['photo']
                    file_id = photo_sizes[-1]['file_id']
                    username = self.message['from']['username']
                    game = self.get_game_name(self.message['caption'],
                                              self.message['caption_entities'][0])

                    if game == "*Default*":
                        username = "*Default*"
                        text = "Стандартный аватар установлен"
                    else:
                        text = random.choice(answers['photo'])

                    record = PlatinumRecord(username, game, file_id)
                    self.add_recrod(record)
                    self.bot.send_message(last_chat_id, text, last_message_id)

        if 'text' in self.message:
            last_message_text = self.message.get('text')

            isBotWasMentioned = self.botWasMentioned(self.message.get('entities', list()),
                                                     last_message_text)

            if self.update_id > self.offset:
                if isBotWasMentioned:
                    self.bot.send_message(last_chat_id, random.choice(answers['text']),
                                          last_message_id)

    def process_commands(self):
        chat_id = str(self.message['chat']['id'])

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
        chat_id = str(self.message['chat']['id'])

        cursor = self.conn.cursor()

        cursor.execute("SELECT * FROM platinum WHERE chat_id=? AND hunter=? AND game=?",
                       (chat_id, record.hunter, record.game))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO platinum VALUES (?, ?, ?, ?)",
                           (chat_id, record.hunter, record.game, record.photo_id))

        else:
            cursor.execute("UPDATE platinum SET photo_id=? WHERE chat_id=? AND hunter=? AND game=?",
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

    def download_file(self, url):
        resp = requests.get(url)
        return resp.content

    def change_avatar(self):
        cursor = self.conn.cursor()
        chat_ids = set(row[0] for row in cursor.execute(
            "SELECT chat_id FROM platinum"))

        for chat_id in chat_ids:
            rows = cursor.execute('''SELECT hunter, game, photo_id FROM platinum
                                  WHERE chat_id=? AND hunter!=?''', (chat_id, "*Default*",))
            records = [PlatinumRecord(*row) for row in rows]

            if len(records) == 0:
                cursor.execute('''SELECT photo_id
                                FROM platinum
                                WHERE chat_id=? AND hunter=? AND game=?''',
                               (chat_id, "*Default*", "*Default*", ))

                if not cursor.fetchone() is None:
                    text = "Новых платин нет. Ставлю стандартный аватар :("
                    file_id = cursor.fetchone()[0]
                else:
                    continue

            else:
                record = records[0]

                text = "Поздравляем @{} с платиной в игре \"{}\" !".format(
                    record.hunter, record.game)
                cursor.execute("DELETE FROM platinum WHERE chat_id=? AND hunter=? AND game=?",
                               (chat_id, record.hunter, record.game))

                file_id = record.photo_id

            photo_url = self.bot.get_file_url(file_id)
            photo = self.download_file(photo_url)
            self.bot.set_chat_photo(chat_id, photo)

            self.bot.send_message(chat_id, text)

        self.conn.commit()

        return True

    def start_command(self):
        chat_id = str(self.message['chat']['id'])

        if not chat_id in self.where_run:
            self.where_run.append(chat_id)
            self.bot.send_message(chat_id, "Да начнётся охота!")

    def help_command(self):
        text = """Для добавления фото в очередь нужно отправить в чат фото с комментарием следующего вида:

@{} <название игры>

Картинку необходимо подготовить таким образом, чтобы желаемая область была в центре. В идеале обрезать ее в пропорциях 1:1 оставив желаемую область.

У бота есть следующие команды:

\\start - запуск бота в чате

\\help - вывод справочной информации

\\showqueue - отобразить очередь выбитых платин на данный момент

\\deletegame - удалить последнюю добавленную тобой платину""".format(self.bot.name)

        chat_id = self.message['chat']['id']
        reply_to_message_id = self.message['message_id']

        return self.bot.send_message(chat_id, text, reply_to_message_id)

    def showqueue_command(self):
        chat_id = str(self.message['chat']['id'])
        reply_to_message_id = self.message['message_id']

        text = "Очередь платин:\n"
        cursor = self.conn.cursor()
        rows = cursor.execute('''SELECT hunter, game, photo_id FROM platinum
                                WHERE chat_id=? AND hunter!=? AND game!=?''',
                              (chat_id, "*Default*", "*Default*"))

        platinum_chat = [PlatinumRecord(*row) for row in rows]

        text_record = "\n".join(str(record) for record in platinum_chat)

        return self.bot.send_message(chat_id, text+text_record, reply_to_message_id)

    def deletegame_command(self):
        chat_id = str(self.message['chat']['id'])
        reply_to_message_id = self.message['message_id']
        username = self.message['from']['username']

        cursor = self.conn.cursor()
        rows = cursor.execute('''SELECT hunter, game, photo_id FROM platinum
                                WHERE chat_id=? AND hunter=?''', (chat_id, username))
        records_user = [PlatinumRecord(*row) for row in rows]

        if len(records_user) == 0:
            text = "Удалять у {} нечего. Поднажми!".format(username)
        else:
            record = records_user[-1]
            cursor.execute('''DELETE FROM platinum
                            WHERE chat_id=? AND hunter=? AND game=?''',
                           (chat_id, record.hunter, record.game))
            text = "Платина в игре {} игрока {} успешно удалена".format(
                record.game, record.hunter)

            self.conn.commit()

        return self.bot.send_message(chat_id, text, reply_to_message_id)


def get_date(data, hour):
    day, month, year = map(int, data.split('.'))

    return datetime(day=day, month=month,
                    year=year, hour=int(hour),
                    tzinfo=timezone.utc)


def main():
    with open('config.json') as cfg:
        config = json.load(cfg)

    date = get_date(config['date'], config['hour'])
    delta = timedelta(days=int(config['delta']))

    token = config['API_TOKEN']
    bot = BotHandler(token)
    worker = Worker(bot, date, delta)
    print("{}".format(bot.api_url))

    worker.start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
