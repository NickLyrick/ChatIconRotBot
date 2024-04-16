"""This module contains the Request class, 
which is responsible for handling all the database queries."""

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete

from pytz import timezone as tz

from .schemas import Chat, Platinum, History

from src.bot.settings import settings
from src.utility.platinum_record import PlatinumRecord


# TODO: don't use raw SQL queries
class Request:
    """This class is responsible for handling all the database queries."""

    def __init__(self):
        """Initialize the Request class."""

        self.session: async_sessionmaker[AsyncSession] = None

    async def create_connection(self):
        """This function is used to get the connection to the database."""

        # connection_pool = AsyncConnectionPool(settings.db.database_url)
        engine = create_async_engine(settings.db.database_url)

        self.session = async_sessionmaker(engine, expire_on_commit=False)

    async def check_db_connection(self) -> bool:
        """This method is used to check the connection to the database."""

        try:
            async with self.session() as session:
                await session.execute(select(1))
        except Exception as e:
            logging.error(f"Has lost connection to database:\n {e}")
            logging.info("Try reconnect to database")
            try:
                await self.create_connection()
            except Exception as e:
                logging.exception(f"Connect to database failed:\n {e}")

    async def get_chats(self) -> dict:
        """This method is used to get all the chats from the database."""
        async with self.session() as session:
            stmt = select(Chat)

            return {
                chat.chat_id: {"date": chat.date, "delta": chat.delta}
                for chat in (await session.scalars(stmt)).all()
            }

    async def set_chat_date(self, chat_id, date) -> None:
        """This method is used to set the date of the chat in the database."""
        async with self.session() as session:
            stmt = select(Chat).where(Chat.chat_id == chat_id)
            chat = (await session.scalars(stmt)).one()
            chat.date = date

            await session.commit()

    async def set_chat_delta(self, chat_id, delta) -> None:
        """This method is used to set the delta of the chat in the database."""

        async with self.session() as session:
            stmt = select(Chat).where(Chat.chat_id == chat_id)
            chat = (await session.scalars(stmt)).one()
            chat.delta = delta

            await session.commit()

    async def get_chat_settings(self, chat_id) -> list:
        """This method is used to get the settings of the chats from the database."""

        async with self.session() as session:
            stmt_chat = select(Chat).where(Chat.chat_id == chat_id)
            stmt_default = select(Platinum).where(Platinum.chat_id == chat_id).\
                where(Platinum.hunter == '*Default*').where(Platinum.game == '*Default*')
            chat = (await session.scalars(stmt_chat)).one()
            default_avatar_record = (await session.scalars(stmt_default)).one()

            return [chat.date, chat.delta, default_avatar_record.photo_id]

    async def add_chat_data(self, chat_id, date, delta) -> None:
        """This method is used to add the chat data to the database."""

        async with self.session() as session:
            stmt = select(Chat).where(Chat.chat_id == chat_id)
            chat = (await session.scalars(stmt)).one_or_none()

            if chat is None:
                await session.add(Chat(chat_id=chat_id, date=date, delta=delta))
            else:
                chat.date = date
                chat.delta = delta

            await session.commit()

    async def add_user_data(self, user_id, user_name) -> None:
        """This method is used to add the user data to the database."""

        pass
        # TODO: decide what to do with user_id
        # query = f"INSERT INTO users (user_id, user_name) VALUES ({user_id}, '{user_name}')" \
        #         f"ON CONFLICT (user_id) DO UPDATE SET user_name = '{user_name}'"
        # await self.connector.execute(query)

    async def get_queue(self, chat_id):
        """This method is used to get the queue from the database."""

        async with self.session() as session:
            stmt = select(Platinum.hunter, Platinum.game, Platinum.platform).\
                where(Platinum.hunter != '*Default*').where(Platinum.chat_id==chat_id).order_by(Platinum.id)
            trophies = await session.execute(stmt)

            return trophies.all()

    async def get_avatar(self, chat_id):
        """This method is used to get the avatar file_id from the database."""

        async with self.session() as session:
            records = await self.get_queue(chat_id)

            if len(records) == 0:
                stmt_default = select(Platinum).where(Platinum.chat_id == chat_id).\
                    where(Platinum.hunter == '*Default*').where(Platinum.game == '*Default*')
                default_avatar_record = (await session.scalars(stmt_default)).one_or_none()

                if default_avatar_record is not None:
                    text = "Новых трофеев нет. Ставлю стандартный аватар :("
                    file_id = default_avatar_record.photo_id
                else:
                    text = "Стандартный аватар не задан. Оставляю всё как есть."
                    file_id = None
            else:
                record = records[0]

                trophy = "платиной"
                if record.platform == "Xbox":
                    trophy = "1000G"
                text = (
                    f'Поздравляем @{record.hunter} с {trophy} в игре "{record.game}" !'
                )
                file_id = record.photo_id

                await session.delete(record)

            await session.commit()

            return file_id, text

    async def get_top(self, chat_id, date: datetime):
        """This method is used to get the top from the database."""

        timezone = tz("Europe/Moscow")
        date = date.astimezone(tz=timezone)

        async with self.session() as session:
            stmt = select(History.hunter, func.count(History.id)).\
                where(History.chat_id == chat_id).where(History.date >= date).\
                    group_by(History.hunter).order_by(desc(func.count(History.id)))
            return (await session.execute(stmt)).all()

    async def get_history(self, chat_id, hunter: str):
        """This method is used to get the history from the database."""

        async with self.session() as session:
            stmt = select(History.game, History.date, History.platform).\
                where(History.chat_id == chat_id).\
                    where(History.hunter == hunter).order_by(History.date)
            data = []
            timezone = tz("Europe/Moscow")
            for record in (await session.execute(stmt)).all():
                game, date, platform = record
                date = date.astimezone(tz=timezone)
                date_str = date.strftime("%d.%m.%Y")
                data.append((game, date_str, platform))

            return data

    async def add_record(self, chat_id, record: PlatinumRecord) -> None:
        """This method is used to add the record to the database."""

        async with self.session() as session:
            stmt = select(Platinum).where(Platinum.chat_id == chat_id).\
                where(Platinum.hunter == record.hunter).\
                    where(Platinum.game == record.game).\
                    where(Platinum.platform == record.platform)

            existing_record = (await session.scalars(stmt)).one_or_none()

            if existing_record is None:
                # Query to insert a record into the 'platinum' table
                platinum = Platinum(chat_id=chat_id,
                                    hunter=record.hunter,
                                    game=record.game,
                                    photo_id=record.photo_id,
                                    platform=record.platform)
                # Query to insert a record into the 'history' table
                history = History(chat_id=chat_id,
                                    hunter=record.hunter,
                                    game=record.game,
                                    platform=record.platform)

                session.add_all([platinum, history])
            else:
                existing_record.photo_id = "Fuck"

            # Commit the changes to the database
            await session.commit()

    async def delete_record(self, chat_id, username) -> str:
        """This method is used to delete the record from the database."""

        async with self.session() as session:
            stmt = select(Platinum).where(Platinum.chat_id==chat_id).\
                where(Platinum.hunter==username).order_by(Platinum.id)

            records_user = (await session.scalars(stmt)).all()

            if len(records_user) == 0:
                text = f"Удалять у @{username} нечего. Поднажми!"
            else:
                record = records_user[-1]

                stmt_delete = delete(History).where(History.chat_id==chat_id).\
                    where(History.hunter==record.hunter).where(History.game==record.game)

                await session.delete(record)
                await session.execute(stmt_delete)

                text = f"Трофей в игре {record.game} игрока @{record.hunter} успешно удален"

                await session.commit()

        return text

    async def get_records_data(self, chat_id):
        """This method is used to get the records data from the database."""

        async with self.session() as session:
            stmt = select(Platinum.hunter, Platinum.game).where(Platinum.chat_id==chat_id).\
                where(Platinum.hunter!='*Default*').order_by(Platinum.id)

            return (await session.execute(stmt)).all()
