import psycopg_pool
from pytz import timezone as tz
from datetime import datetime


# TODO: don't use raw SQL queries
class Request:
    def __init__(self, connector: psycopg_pool.AsyncConnectionPool.connection):
        self.connector = connector

    async def get_chats(self):
        query = f"SELECT * FROM chats"
        async with self.connector.cursor() as cursor:
            await cursor.execute(query)

            return {chat_id: {'date': date, 'delta': delta}
                    for chat_id, date, delta in await cursor.fetchall()}

    async def add_chat_data(self, chat_id, date, delta) -> None:
        query = (f"INSERT INTO chats VALUES({chat_id},{date},{delta})"
                 f"ON CONFLICT (chat_id) DO UPDATE SET (date, delta) = ({date}, {delta})")
        async with self.connector.cursor() as cursor:
            await cursor.execute(query)
        await self.connector.commit()

    async def add_user_data(self, user_id, user_name) -> None:
        pass
        # TODO: decide what to do with user_id
        # query = f"INSERT INTO users (user_id, user_name) VALUES ({user_id}, '{user_name}')" \
        #         f"ON CONFLICT (user_id) DO UPDATE SET user_name = '{user_name}'"
        # await self.connector.execute(query)

    async def get_queue(self, chat_id):
        # TODO: replace by true chat id
        query = (f"SELECT hunter, game, platform FROM platinum"
                 f" WHERE chat_id=-1001356987990 AND hunter!='*Default*' AND game!='*Default*' ORDER BY id")

        async with self.connector.cursor() as cursor:
            await cursor.execute(query)
            return await cursor.fetchall()

    async def get_top(self, chat_id, date: datetime):
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
