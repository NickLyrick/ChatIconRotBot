""" Main script Bot  """

import os
import re
import random
import logging
from io import BytesIO
from pytz import utc, timezone as tzTimezone
from datetime import datetime, timezone, timedelta

from matplotlib import pyplot as plt
from matplotlib.transforms import Bbox

import psycopg2
from psycopg2 import sql

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ContentType

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import wikipedia
from wikipedia import exceptions as wikiexceptions

from answers import answers, help_text

DATABASE_URL = os.environ['DATABASE_URL']

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=os.environ["TOKEN"])
dp = Dispatcher(bot)

where_run = dict()

db = psycopg2.connect(DATABASE_URL, sslmode='require')

bot_username = ''

scheduler = AsyncIOScheduler(timezone=utc)


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


async def change_avatar(chat_id):
    with db.cursor() as cursor:
        cursor.execute("SELECT hunter, game, photo_id FROM platinum "
                       "WHERE chat_id=%s AND hunter!=%s ORDER BY id ASC",
                       (chat_id, "*Default*",))

        records = [PlatinumRecord(*row) for row in cursor.fetchall()]

        if len(records) == 0:
            cursor.execute('''SELECT photo_id FROM platinum WHERE chat_id=%s AND hunter=%s AND game=%s''',
                           (chat_id, "*Default*", "*Default*",))
            row = cursor.fetchone()
            if row is not None:
                text = "Новых платин нет. Ставлю стандартный аватар :("
                file_id = row[0]
            else:
                text = "Стандартный аватар не задан. Оставляю всё как есть."
                file_id = None

        else:
            record = records[0]

            text = "Поздравляем @{} с платиной в игре \"{}\" !".format(record.hunter,
                                                                       record.game)
            cursor.execute('''DELETE FROM platinum WHERE chat_id=%s AND hunter=%s AND game=%s''',
                           (chat_id, record.hunter, record.game))
            db.commit()

            file_id = record.photo_id

    if file_id is not None:
        photo = await bot.download_file_by_id(file_id=file_id)
        await bot.set_chat_photo(chat_id, photo)

    await bot.send_message(chat_id, text)


async def chat_job(chat_id, delta):
    await change_avatar(chat_id)

    tdelta = timedelta(days=delta)
    date = where_run[chat_id]['date'] + tdelta
    with db.cursor() as cursor:
        cursor.execute('''UPDATE chats SET date=%s WHERE chat_id=%s''',
                       (date, chat_id))
    db.commit()
    where_run[chat_id]['date'] = date


def add_job(chat_id, date, delta):
    job = scheduler.get_job(str(chat_id))
    if job is None:
        scheduler.add_job(chat_job, "interval", days=delta, start_date=date,
                          id=str(chat_id), args=[chat_id, delta])
    else:
        if date is None:
            date = where_run[chat_id]['date']
        if delta is None:
            delta = where_run[chat_id]['delta']

        job.reschedule(trigger='interval', days=delta, start_date=date)
        job.modify(args=[chat_id, delta])


async def on_startup(dispatcher):
    global bot_username
    global where_run

    bot_user = await bot.me
    bot_username = bot_user.username

    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM chats")
        where_run = {chat_id: {'date': date, 'delta': delta}
                     for chat_id, date, delta in cursor.fetchall()}

    for chat_id in where_run.keys():
        date = where_run[chat_id]['date']
        delta = where_run[chat_id]['delta']
        print(date)
        add_job(chat_id, date, delta)

    scheduler.print_jobs()
    scheduler.start()


async def check_permissions(message: types.Message):
    member = await message.chat.get_member(message.from_user.id)

    return member.can_change_info or member.is_chat_creator()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    chat_id = message.chat.id

    if chat_id not in where_run:
        date = datetime.now(timezone.utc)
        delta = 1
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO chats VALUES(%s,%s,%s)", (chat_id, date, delta))
        db.commit()
        where_run[chat_id] = {'date': date, 'delta': delta}
        add_job(chat_id, date, delta)

        await bot.send_message(chat_id, "Да начнётся охота!")


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    await message.reply(help_text.format(bot_username))


@dp.message_handler(commands=['showsettings'])
async def showsettings(message: types.Message):
    chat_id = message.chat.id

    with db.cursor() as cursor:
        cursor.execute("SELECT date, delta FROM chats WHERE chat_id=%s", (chat_id,))
        date, delta = cursor.fetchone()

        cursor.execute('''SELECT photo_id FROM platinum WHERE chat_id=%s AND hunter=%s''',
                       (chat_id, '*Default*'))
        row = cursor.fetchone()

    text = "Ближайшая дата смены: {}.\n" \
           "Промежуток между сменами: {}д.".format(date.strftime("%d.%m.%Y %H:%M"), delta)

    if row is not None:
        photo_id = row[0]
        await message.reply_photo(photo=photo_id, caption=text)
    else:
        await message.reply(text)


@dp.message_handler(commands=['showqueue'])
async def showqueue(message: types.Message):
    chat_id = message.chat.id
    text = "Очередь платин"
    with db.cursor() as cursor:
        cursor.execute("SELECT hunter, game, photo_id FROM platinum "
                       "WHERE chat_id=%s AND hunter!=%s AND game!=%s ORDER BY id ASC",
                       (chat_id, "*Default*", "*Default*"))

        data = [(i, *record[0:2]) for i, record in enumerate(cursor.fetchall(), start=1)]

    if len(data) == 0:
        await message.reply("Список пуст!")
    else:
        table = plt.table(cellText=data, colLabels=["№", "Nickname", "Game"], cellLoc='center',
                          loc='center', colColours=['silver'] * 3)
        plt.axis('off')
        plt.grid('off')
        table.auto_set_font_size(False)
        table.set_fontsize(18)
        table.scale(1, 3)
        table.auto_set_column_width(col=[0, 1, 2])

        for _, cell in table.get_celld().items():
            cell.set_linewidth(2)

        # prepare for saving:
        # draw canvas once
        plt.gcf().canvas.draw()
        # get bounding box of table
        points = table.get_window_extent(plt.gcf()._cachedRenderer).get_points()
        # add 3 pixel spacing
        points[0, :] -= 3
        points[1, :] += 3
        # get new bounding box in inches
        nbbox = Bbox.from_extents(points / plt.gcf().dpi)

        img = BytesIO()
        plt.savefig(img, format='png', dpi=300, transparent=True, bbox_inches=nbbox)
        img.seek(0)

        await message.reply_photo(photo=img, caption=text)


@dp.message_handler(commands=['deletegame'])
async def deletegame(message: types.Message):
    chat_id = message.chat.id
    username = message.from_user.username

    with db.cursor() as cursor:
        cursor.execute("SELECT hunter, game, photo_id FROM platinum "
                       "WHERE chat_id=%s AND hunter=%s ORDER BY id ASC",
                       (chat_id, username))
        records_user = [PlatinumRecord(*row) for row in cursor.fetchall()]

        if len(records_user) == 0:
            text = "Удалять у {} нечего. Поднажми!".format(username)
        else:
            record = records_user[-1]
            cursor.execute('''DELETE FROM platinum WHERE chat_id=%s AND hunter=%s AND game=%s''',
                           (chat_id, record.hunter, record.game))
            cursor.execute('''DELETE FROM history WHERE chat_id=%s AND hunter=%s AND game=%s''',
                           (chat_id, record.hunter, record.game))
            text = "Платина в игре {} игрока {} успешно удалена".format(record.game, record.hunter)

            db.commit()

    await message.reply(text)


@dp.message_handler(lambda message: message.caption.startswith(f"@{bot_username}"),
                    content_types=ContentType.PHOTO)
async def add_record(message: types.Message):
    chat_id = message.chat.id
    username = message.from_user.username
    game = message.caption.replace("@{}".format(bot_username), "").strip()
    file_id = message.photo[-1].file_id

    if game == "*Default*":
        if await check_permissions(message):
            username = "*Default*"
            text = "Стандартный аватар установлен"
        else:
            username = None
            text = "У вас нет прав для изменения информации группы!"
    else:
        text = random.choice(answers['photo'])

    if username is not None:
        record = PlatinumRecord(username, game, file_id)
        with db.cursor() as cursor:
            query = sql.SQL('''SELECT * FROM platinum
                            WHERE chat_id=%s AND hunter={} AND game={}''').format(sql.Literal(record.hunter),
                                                                                  sql.Literal(record.game))
            cursor.execute(query, (chat_id,))
            if cursor.fetchone() is None:
                query = sql.SQL("INSERT INTO platinum VALUES (%s, {}, {}, %s)").format(sql.Literal(record.hunter),
                                                                                       sql.Literal(record.game))
                cursor.execute(query, (chat_id, record.photo_id))

                query = sql.SQL("INSERT INTO history(chat_id, hunter, game) VALUES (%s, {}, {})").format(sql.Literal(record.hunter),
                    sql.Literal(record.game))

                cursor.execute(query, (chat_id))
            else:
                query = sql.SQL("UPDATE platinum SET photo_id=%s "
                                "WHERE chat_id=%s AND hunter={} AND game={}").format(sql.Literal(record.hunter),
                                                                                     sql.Literal(record.game))
                cursor.execute(query, (record.photo_id, chat_id,))
        db.commit()

    await message.reply(text)


@dp.message_handler(
    lambda message: re.match(r'^((?!\*Date\*|\*Delta\*|\*History\*).)*@{}((?!\*Date\*|\*Delta\*|\*History\*).)*$'.format(bot_username),
                             message.text))
async def reply_by_text(message: types.Message):
    await message.reply(random.choice(answers['text']))


@dp.message_handler(lambda message: message.text.startswith(f'@{bot_username} *Delta*'),
                    content_types=ContentType.TEXT)
async def set_delta(message: types.Message):
    chat_id = message.chat.id

    if await check_permissions(message):
        delta_str = message.text.replace("@{} *Delta*".format(bot_username), "").strip()
        try:
            delta = int(delta_str)
            if delta > 0:
                with db.cursor() as cursor:
                    cursor.execute("UPDATE chats SET delta=%s WHERE chat_id=%s",
                                   (delta, chat_id))
                db.commit()
                where_run[chat_id]['delta'] = delta
                add_job(chat_id=chat_id, date=None, delta=delta)
                text = "Промежуток между сменами фото чата успешно установлен."
            else:
                text = "Промежуток между сменами фото должен быть больше нуля и целым числом"
        except ValueError:
            text = "Промежуток задан не верно. Пример: @{} *Delta* 3".format(bot_username)
    else:
        text = "У вас нет прав для изменения информации группы!"

    await message.reply(text)


@dp.message_handler(lambda message: message.text.startswith(f'@{bot_username} *Date*'),
                    content_types=ContentType.TEXT)
async def set_date(message: types.Message):
    chat_id = message.chat.id

    if await check_permissions(message):
        date_str = message.text.replace("@{} *Date*".format(bot_username), "").strip()
        try:
            date = datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            date = date.replace(tzinfo=utc)
            if date > datetime.now(timezone.utc):
                with db.cursor() as cursor:
                    cursor.execute("UPDATE chats SET date=%s WHERE chat_id=%s", (date, chat_id))
                db.commit()
                add_job(chat_id=chat_id, date=date, delta=None)
                where_run[chat_id]['date'] = date
                text = "Ближайшая дата смены фото чата успешно установлена."
            else:
                text = "Ближайшая дата смены оказалась в прошлом. Я не могу изменить прошлое!"
        except ValueError:
            text = "Дата введена неверна. Пример: " \
                   "@{} *Date* 22/07/1941 04:00".format(bot_username)
    else:
        text = "У вас нет прав для изменения информации группы!"

    await message.reply(text)

@dp.message_handler(lambda message: message.text.startswith(f'@{bot_username} *History*'),
                    content_types=ContentType.TEXT)
async def set_date(message: types.Message):
    chat_id = message.chat.id

    username = message.text.replace("@{} *History*".format(bot_username), "").strip()

    if username == "":
        username = message.from_user.username
    else:
        username = username.replace("@", "")

    with db.cursor() as cursor:
        cursor.execute("SELECT game, date FROM history "
                       "WHERE chat_id=%s AND hunter=%s ORDER BY date ASC",
                       (chat_id, username))
        data = []
        for i, record in enumerate(cursor.fetchall(), start=1):
            game, date = record
            date = date.astimezone(tz=tzTimezone('Europe/Moscow'))
            date_str = date.strftime("%d.%m.%Y")
            data.append((i, game, date_str))


    if len(data) == 0:
        await message.reply("Список пуст!")
    else:
        text = f"Список всех платин {username}"
        table = plt.table(cellText=data, colLabels=["№", "Game", "Date"], cellLoc='center',
                          loc='center', colColours=['silver'] * 3)
        plt.axis('off')
        plt.grid('off')
        table.auto_set_font_size(False)
        table.set_fontsize(18)
        table.scale(1, 3)
        table.auto_set_column_width(col=[0, 1, 2])

        for _, cell in table.get_celld().items():
            cell.set_linewidth(2)

        # prepare for saving:
        # draw canvas once
        plt.gcf().canvas.draw()
        # get bounding box of table
        points = table.get_window_extent(plt.gcf()._cachedRenderer).get_points()
        # add 3 pixel spacing
        points[0, :] -= 3
        points[1, :] += 3
        # get new bounding box in inches
        nbbox = Bbox.from_extents(points / plt.gcf().dpi)

        img = BytesIO()
        plt.savefig(img, format='png', dpi=300, transparent=True, bbox_inches=nbbox)
        img.seek(0)

        await message.reply_photo(photo=img, caption=text)



@dp.message_handler(commands=['gamesinfo'])
async def games_info(message: types.Message):
    chat_id = message.chat.id

    with db.cursor() as cursor:
        cursor.execute("SELECT hunter, game FROM platinum "
                       "WHERE chat_id=%s AND hunter!=%s AND game!=%s ORDER BY id ASC",
                       (chat_id, "*Default*", "*Default*"))

        data = [record for record in cursor.fetchall()]

    text = ""
    for i, record in enumerate(data, start=1):
        game = record[1]
        try:
            page = wikipedia.page(game)
            url = f"[{game}]({page.url})"
        except wikiexceptions.PageError:
            results = wikipedia.search(game)
            try:
                page = wikipedia.page(results[0])
                url = f"[{game}]({page.url} )"
            except wikiexceptions.PageError:
                url = "Информация не найдена"
        except wikiexceptions.DisambiguationError:
            url = "Информация не найдена"

        text += f"{i}) {url} \n"

    await message.reply(text, parse_mode="Markdown")


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
