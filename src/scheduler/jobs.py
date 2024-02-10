from aiogram import Bot
from src.utility.platinum_record import PlatinumRecord


async def change_avatar(chat_id, bot: Bot):
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

            text = f'Поздравляем @{record.hunter} с {trophy} в игре \"{record.game}\" !'
            cursor.execute('''DELETE FROM platinum WHERE chat_id=%s AND hunter=%s AND game=%s AND platform=%s''',
                           (chat_id, record.hunter, record.game, record.platform))
            db.commit()

            file_id = record.photo_id

    if file_id is not None:
        photo = await bot.download_file_by_id(file_id=file_id)
        await bot.set_chat_photo(chat_id, photo)

    await bot.send_message(chat_id, text)
