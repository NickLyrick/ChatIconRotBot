""" Main script Bot  """

import os
import re
import sys
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

db = psycopg2.connect(DATABASE_URL)

bot_username = ''

scheduler = AsyncIOScheduler(timezone=utc)


class PlatinumRecord:
    """PlatinumRecord is class for record of platinum"""

    def __init__(self, hunter, game, photo_id, platform):
        super(PlatinumRecord, self).__init__()
        self.hunter = hunter
        self.game = game
        self.photo_id = photo_id
        self.platform = platform

    def __str__(self):
        return "{} {} {}".format(self.hunter, self.game, self.platform)

    def __repr__(self):
        return "PlatinumRecord({}, {}, {}, {})".format(self.hunter, 
                                                       self.game, 
                                                       self.photo_id,
                                                       self.platform)

    def __eq__(self, other):
        return (self.hunter == other.hunter) and (self.game == other.game) and (self.platform == other.platform)


async def change_avatar(chat_id):
    with db.cursor() as cursor:
        cursor.execute("SELECT hunter, game, photo_id, platform FROM platinum "
                       "WHERE chat_id=%s AND hunter!=%s ORDER BY id ASC",
                       (chat_id, "*Default*",))

        records = [PlatinumRecord(*row) for row in cursor.fetchall()]

        if len(records) == 0:
            cursor.execute('''SELECT photo_id FROM platinum WHERE chat_id=%s AND hunter=%s AND game=%s''',
                           (chat_id, "*Default*", "*Default*",))
            row = cursor.fetchone()
            if row is not None:
                text = "Новых трофеев нет. Ставлю стандартный аватар :("
                file_id = row[0]
            else:
                text = "Стандартный аватар не задан. Оставляю всё как есть."
                file_id = None

        else:
            record = records[0]

            trophy = "платиной"
            if record.platform == "Xbox":
                trophy = "1000G"

            text = "Поздравляем @{} с {} в игре \"{}\" !".format(record.hunter,
                                                                 trophy,
                                                                 record.game)
            cursor.execute('''DELETE FROM platinum WHERE chat_id=%s AND hunter=%s AND game=%s AND platform=%s''',
                           (chat_id, record.hunter, record.game, record.platform))
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

def table(data, columns, caption: str = None):
    rows = [[*data[i:i+20]] for i in range(0, len(data), 20)]
    if len(rows) > 1 and len(rows[-1]) < 5:
        rows[-2].extend(rows[-1])
        del rows[-1]

    media = types.MediaGroup()
    for i, row in enumerate(rows):
        table = plt.table(cellText=row, colLabels=columns, cellLoc='center',
                              loc='center', colColours=['silver'] * len(columns))
        plt.axis('off')
        plt.grid('off')
        table.auto_set_font_size(False)
        table.set_fontsize(18)
        table.scale(1, len(columns))
        table.auto_set_column_width(col=list(range(len(columns))))

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

        if i == 0 and caption is not None:
            media.attach_photo(img, caption)
        else:
            media.attach_photo(img)

    return media

def history_date(chat_id, date: datetime):
    date = date.astimezone(tz=tzTimezone('Europe/Moscow'))

    with db.cursor() as cursor:
        cursor.execute("SELECT hunter, COUNT(id) FROM history "
                       "WHERE chat_id=%s AND date>=%s "
                       "GROUP BY hunter "
                       "ORDER BY COUNT(id) DESC",
                       (chat_id, date))
        data = [(i, *record) for i, record in enumerate(cursor.fetchall(), start=1)]

    if len(data) > 0:
        img = table(data, ["№", "Nickname", "Trophies"])

        return img
    else:
        return None

async def db_connection_check():
    global db
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT 1")
    except psycopg2.Error:
        logging.error("Has lost connection to database")
        logging.info("Try reconnect to database")

        try:
            db = psycopg2.connect(DATABASE_URL)
        except psycopg2.Error:
            logging.exception("Connect to database failed: ")


async def on_startup(dispatcher):
    global bot_username
    global where_run

    bot_user = await bot.me
    bot_username = bot_user.username

    scheduler.add_job(db_connection_check, "interval", minutes=1)

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
    text = "Очередь трофеев"
    with db.cursor() as cursor:
        cursor.execute("SELECT hunter, game, platform FROM platinum "
                       "WHERE chat_id=%s AND hunter!=%s AND game!=%s ORDER BY id ASC",
                       (chat_id, "*Default*", "*Default*"))

        data = [(i, *record) for i, record in enumerate(cursor.fetchall(), start=1)]

    if len(data) == 0:
        await message.reply("Список пуст!")
    else:
        media = table(data, ["№", "Nickname", "Game", "Platform"], text)

        await message.reply_media_group(media=media)


@dp.message_handler(commands=['deletegame'])
async def deletegame(message: types.Message):
    chat_id = message.chat.id
    username = message.from_user.username

    with db.cursor() as cursor:
        cursor.execute("SELECT hunter, game, photo_id, platform FROM platinum "
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
            text = "Трофей в игре {} игрока {} успешно удален".format(record.game, record.hunter)

            db.commit()

    await message.reply(text)

@dp.message_handler(commands=['top'])
async def top(message: types.Message):
    chat_id = message.chat.id

    arguments = message.get_args()
    date = datetime(1970, 1, 1)
    if len(arguments) == 0:
        text = "Топ за всё время"
    else:
        try:
            date = datetime.strptime(arguments, '%d.%m.%Y')

            text = "Топ за указанный промежуток"

        except ValueError:
            text = "Топ за всё время"

    media = history_date(chat_id=chat_id, date=date)

    if media is None:
        await message.reply("Список пуст!")
    else:
        await message.reply_media_group(media=media)

@dp.message_handler(commands=['history'])
async def history(message: types.Message):
    chat_id = message.chat.id

    arguments =  message.get_args()
    if len(arguments) == 0:
        username = message.from_user.username
    else:
        username = arguments.replace("@", "")

    with db.cursor() as cursor:
        cursor.execute("SELECT game, date, platform FROM history "
                       "WHERE chat_id=%s AND hunter=%s ORDER BY date ASC",
                       (chat_id, username))
        data = []
        for i, record in enumerate(cursor.fetchall(), start=1):
            game, date, platform = record
            date = date.astimezone(tz=tzTimezone('Europe/Moscow'))
            date_str = date.strftime("%d.%m.%Y")
            data.append((i, game, date_str, platform))


    if len(data) == 0:
        await message.reply("Список пуст!")
    else:
        text = f"Список всех трофеев {username}"

        media = table(data, ["№", "Game", "Date", "Platform"], text)

        await message.reply_media_group(media=media)



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

@dp.message_handler(commands=['delta'])
async def set_delta(message: types.Message):
    chat_id = message.chat.id

    if await check_permissions(message):
        try:
            delta = int(message.get_args())
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
            text = "Промежуток задан не верно. Пример: /delta@{} 3".format(bot_username)
    else:
        text = "У вас нет прав для изменения информации группы!"

    await message.reply(text)


@dp.message_handler(commands=['date'])
async def set_date(message: types.Message):
    chat_id = message.chat.id

    if await check_permissions(message):
        try:
            date = datetime.strptime(message.get_args(), "%d/%m/%Y %H:%M")
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
                   "/date@{} 22/07/1941 04:00".format(bot_username)
    else:
        text = "У вас нет прав для изменения информации группы!"

    await message.reply(text)

@dp.message_handler(lambda message: message.caption.startswith(f"@{bot_username}") if message.caption else False,
                    content_types=ContentType.PHOTO)
async def add_record(message: types.Message):
    chat_id = message.chat.id
    username = message.from_user.username
    game = message.caption.replace("@{}".format(bot_username), "").replace("Xbox", "").replace("Playstation", "").strip()
    platform = "Playstation"
    if message.caption.find("Xbox") != -1:
        platform = "Xbox"

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
        record = PlatinumRecord(username, game, file_id, platform)
        with db.cursor() as cursor:
            query = sql.SQL('''SELECT * FROM platinum
                            WHERE chat_id=%s AND hunter={} AND game={} AND platform={}''').format(sql.Literal(record.hunter),
                                                                                                  sql.Literal(record.game),
                                                                                                  sql.Literal(record.platform))
            cursor.execute(query, (chat_id,))
            if cursor.fetchone() is None:
                query = sql.SQL("INSERT INTO platinum(chat_id, hunter, game, photo_id, platform) "
                                "VALUES (%s, {}, {}, %s, {})").format(sql.Literal(record.hunter),
                                                                      sql.Literal(record.game),
                                                                      sql.Literal(record.platform))
                cursor.execute(query, (chat_id, record.photo_id))

                query = sql.SQL("INSERT INTO history(chat_id, hunter, game, platform) "
                                "VALUES (%s, {}, {}, {})").format(sql.Literal(record.hunter),
                                                                  sql.Literal(record.game),
                                                                  sql.Literal(record.platform))

                cursor.execute(query, (chat_id,))
            else:
                query = sql.SQL("UPDATE platinum SET photo_id=%s "
                                "WHERE chat_id=%s AND hunter={} AND game={} AND platform={}").format(sql.Literal(record.hunter),
                                                                                                     sql.Literal(record.game),
                                                                                                     sql.Literal(record.platform))
                cursor.execute(query, (record.photo_id, chat_id,))
        db.commit()

    await message.reply(text)

@dp.message_handler(lambda message: f' @{bot_username} ' in f' {message.text} ',
    content_types=ContentType.TEXT)
async def reply_by_text(message: types.Message):
    await message.reply(random.choice(answers['text']))

if __name__ == '__main__':
    try:
        executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
    except:
        sys.exit("Error! Shutdown bot")
