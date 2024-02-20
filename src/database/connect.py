"""This module contains the Request class, 
which is responsible for handling all the database queries."""

from datetime import datetime
import psycopg_pool

from psycopg_pool import AsyncConnectionPool
from pytz import timezone as tz

from src.bot.settings import settings
from src.utility.platinum_record import PlatinumRecord


async def get_pool():
    """This function is used to get the connection pool to the database."""

    return AsyncConnectionPool(settings.db.database_url)


# TODO: don't use raw SQL queries
class Request:
    """This class is responsible for handling all the database queries."""

    def __init__(self, connector: psycopg_pool.AsyncConnectionPool.connection):
        self.connector = connector

    async def get_chats(self) -> dict:
        """This method is used to get all the chats from the database."""

        query = "SELECT * FROM chats"
        async with self.connector.cursor() as cursor:
            await cursor.execute(query)

            return {chat_id: {'date': date, 'delta': delta}
                    for chat_id, date, delta in await cursor.fetchall()}

    async def set_chat_date(self, chat_id, date) -> None:
        """This method is used to set the date of the chat in the database."""

        query = f"UPDATE chats SET date='{date}' WHERE chat_id={chat_id}"
        async with self.connector.cursor() as cursor:
            await cursor.execute(query)

        await self.connector.commit()

    async def set_chat_delta(self, chat_id, delta) -> None:
        """This method is used to set the delta of the chat in the database."""

        query = f"UPDATE chats SET delta={delta} WHERE chat_id={chat_id}"
        async with self.connector.cursor() as cursor:
            await cursor.execute(query)
            await self.connector.commit()

    async def get_chat_settings(self, chat_id) -> list:
        """This method is used to get the settings of the chats from the database."""

        async with self.connector.cursor() as cursor:
            get_chat_settings_query = f"SELECT date, delta FROM chats WHERE chat_id={
                chat_id}"
            get_chat_default_avatar_query = (f"SELECT photo_id FROM platinum "
                                             f"WHERE chat_id={chat_id} AND hunter='*Default*'")

            await cursor.execute(get_chat_settings_query)
            date, delta = await cursor.fetchone()

            await cursor.execute(get_chat_default_avatar_query)
            default_avatar_record = await cursor.fetchone()

            return [date, delta, default_avatar_record]

    async def add_chat_data(self, chat_id, date, delta) -> None:
        """This method is used to add the chat data to the database."""

        query = (f"INSERT INTO chats VALUES({chat_id},{date},{delta})"
                 f"ON CONFLICT (chat_id) DO UPDATE SET (date, delta) = ({date}, {delta})")
        async with self.connector.cursor() as cursor:
            await cursor.execute(query)
        await self.connector.commit()

    async def add_user_data(self, user_id, user_name) -> None:
        """This method is used to add the user data to the database."""

        pass
        # TODO: decide what to do with user_id
        # query = f"INSERT INTO users (user_id, user_name) VALUES ({user_id}, '{user_name}')" \
        #         f"ON CONFLICT (user_id) DO UPDATE SET user_name = '{user_name}'"
        # await self.connector.execute(query)

    async def get_queue(self, chat_id):
        """This method is used to get the queue from the database."""

        # TODO: replace by true chat id
        query = (f"SELECT hunter, game, platform FROM platinum "
                 f"WHERE chat_id=-1001356987990 AND hunter!='*Default*' AND game!='*Default*' ORDER BY id")

        async with self.connector.cursor() as cursor:
            await cursor.execute(query)
            return await cursor.fetchall()

    async def get_avatar(self, chat_id):
        """This method is used to get the avatar file_id from the database."""

        query = (f"SELECT hunter, game, photo_id, platform FROM platinum "
                 f"WHERE chat_id={chat_id} AND hunter!='*Default*' ORDER BY id")

        async with self.connector.cursor() as cursor:
            await cursor.execute(query)

            records = [PlatinumRecord(*row) for row in await cursor.fetchall()]

            if len(records) == 0:
                query_default_avatar = (
                    f"SELECT photo_id FROM platinum "
                    f"WHERE chat_id={chat_id} AND hunter='*Default*' AND game='*Default*'")
                await cursor.execute(query_default_avatar)
                row = await cursor.fetchone()
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
                text = f'Поздравляем @{record.hunter} с {
                    trophy} в игре \"{record.game}\" !'
                file_id = record.photo_id

                query_delete_avatar = (
                    f"DELETE FROM platinum "
                    f"WHERE chat_id={chat_id} AND hunter='{record.hunter}' "
                    f"AND game='{record.game}' AND platform='{record.platform}'")
                await cursor.execute(query_delete_avatar)

            await self.connector.commit()

            return file_id, text

    async def get_top(self, chat_id, date: datetime):
        """This method is used to get the top from the database."""

        timezone = tz("Europe/Moscow")
        date = date.astimezone(tz=timezone)
        print(date)
        # TODO: replace by true chat id
        query = (f"SELECT hunter, COUNT(id) FROM history "
                 f"WHERE chat_id=-1001356987990 AND date>='{date}' "
                 f"GROUP BY hunter "
                 f"ORDER BY COUNT(id) DESC")

        async with self.connector.cursor() as cursor:
            await cursor.execute(query)
            return await cursor.fetchall()

    async def get_history(self, chat_id, hunter: str):
        """This method is used to get the history from the database."""

        # TODO: replace by true chat id
        query = (f"SELECT game, date, platform FROM history "
                 f"WHERE chat_id=-1001356987990 AND hunter='{hunter}' ORDER BY date")
        async with self.connector.cursor() as cursor:
            await cursor.execute(query)
            data = []
            timezone = tz("Europe/Moscow")
            for record in await cursor.fetchall():
                game, date, platform = record
                date = date.astimezone(tz=timezone)
                date_str = date.strftime("%d.%m.%Y")
                data.append((game, date_str, platform))

            return data

    async def add_record(self, chat_id, record: PlatinumRecord) -> None:
        """This method is used to add the record to the database."""

        async with self.connector.cursor() as cursor:
            select_query = (
                "SELECT * FROM platinum "
                "WHERE chat_id = %s AND hunter = %s AND game = %s AND platform = %s"
            )

            await cursor.execute(select_query, (chat_id, record.hunter, record.game, record.platform))
            existing_record = await cursor.fetchone()

            if existing_record is None:
                # Query to insert a record into the 'platinum' table
                insert_platinum_query = (
                    "INSERT INTO platinum(chat_id, hunter, game, photo_id, platform) "
                    "VALUES (%s, %s, %s, %s, %s) "
                )
                # Query to insert a record into the 'history' table
                insert_history_query = (
                    "INSERT INTO history(chat_id, hunter, game, platform) "
                    "VALUES (%s, %s, %s, %s) "
                )

                # Execute the platinum insertion query
                await cursor.execute(insert_platinum_query,
                                     (chat_id, record.hunter, record.game, record.photo_id, record.platform))
                # Execute the history insertion query
                await cursor.execute(insert_history_query, (chat_id, record.hunter, record.game, record.platform))
            else:
                update_photo_id_query = ("UPDATE platinum SET photo_id = %s "
                                         "WHERE chat_id = %s AND hunter = %s AND game = %s AND platform = %s")
                await cursor.execute(update_photo_id_query, (record.photo_id, chat_id, record.hunter, record.game,
                                                             record.platform))

            # Commit the changes to the database
            await self.connector.commit()

    async def delete_record(self, chat_id, username) -> str:
        """This method is used to delete the record from the database."""

        async with self.connector.cursor() as cursor:
            query = (f"SELECT hunter, game, photo_id, platform FROM platinum "
                     f"WHERE chat_id={chat_id} AND hunter='{username}' ORDER BY id")
            await cursor.execute(query)
            records_user = [PlatinumRecord(*row) for row in await cursor.fetchall()]

            if len(records_user) == 0:
                text = f"Удалять у @{username} нечего. Поднажми!"
            else:
                record = records_user[-1]
                delete_platinum_query = (f"DELETE FROM platinum "
                                         f"WHERE chat_id={chat_id} "
                                         f"AND hunter='{record.hunter}' AND game='{record.game}'")
                delete_history_query = (f"DELETE FROM history "
                                        f"WHERE chat_id={chat_id} "
                                        f"AND hunter='{record.hunter}' AND game='{record.game}'")

                await cursor.execute(delete_platinum_query)
                await cursor.execute(delete_history_query)
                text = f"Трофей в игре {
                    record.game} игрока @{record.hunter} успешно удален"

                self.connector.commit()

        return text
