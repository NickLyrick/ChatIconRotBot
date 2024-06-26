"""This module contains the Request class, 
which is responsible for handling all the database queries."""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from pytz import timezone as tz
from sqlalchemy import between, bindparam, delete, desc, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.bot.settings import settings
from src.utility.platinum_record import PlatinumRecord

from .schemas import Chat, History, Platinum, Scores, Surveys


class Request:
    """This class is responsible for handling all the database queries."""

    def __init__(self):
        """Initialize the Request class."""

        self.session: async_sessionmaker[AsyncSession] = None

    async def create_connection(self):
        """This function is used to get the connection to the database."""

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
            statement = select(Chat)

            return {
                chat.chat_id: {"date": chat.date, "delta": chat.delta}
                for chat in (await session.scalars(statement)).all()
            }

    async def set_chat_date(self, chat_id, date) -> None:
        """This method is used to set the date of the chat in the database."""

        async with self.session() as session:
            statement = select(Chat).where(Chat.chat_id == chat_id)
            chat = (await session.scalars(statement)).one()
            chat.date = date

            await session.commit()

    async def set_chat_delta(self, chat_id, delta) -> None:
        """This method is used to set the delta of the chat in the database."""

        async with self.session() as session:
            statement = select(Chat).where(Chat.chat_id == chat_id)
            chat = (await session.scalars(statement)).one()
            chat.delta = delta

            await session.commit()

    async def get_chat_settings(self, chat_id) -> list:
        """This method is used to get the settings of the chats from the database."""

        async with self.session() as session:
            statement_chat = select(Chat).where(Chat.chat_id == chat_id)
            statement_default = (
                select(Platinum)
                .where(Platinum.chat_id == chat_id)
                .where(Platinum.hunter == "*Default*")
                .where(Platinum.game == "*Default*")
            )
            chat = (await session.scalars(statement_chat)).one()
            default_avatar_record = (await session.scalars(statement_default)).one()

            photo_id = None
            if default_avatar_record is not None:
                photo_id = default_avatar_record.photo_id

            return [chat.date, chat.delta, photo_id]

    async def add_chat_data(self, chat_id, date, delta) -> None:
        """This method is used to add the chat data to the database."""

        async with self.session() as session:
            statement = select(Chat).where(Chat.chat_id == chat_id)
            chat = (await session.scalars(statement)).one_or_none()

            if chat is None:
                session.add(Chat(chat_id=chat_id, date=date, delta=delta))
            else:
                chat.date = date
                chat.delta = delta

            await session.commit()

    async def get_queue(self, chat_id):
        """This method is used to get the queue from the database."""

        async with self.session() as session:
            statement = (
                select(Platinum.hunter, Platinum.game, Platinum.platform)
                .where(Platinum.hunter != "*Default*")
                .where(Platinum.chat_id == chat_id)
                .order_by(Platinum.id)
            )
            trophies = await session.execute(statement)

            return trophies.all()

    async def get_avatar(self, chat_id) -> tuple[str, int, str, str, str]:
        """This method is used to get the avatar file_id from the database."""

        async with self.session() as session:
            records = (
                await session.scalars(
                    select(Platinum)
                    .where(Platinum.chat_id == chat_id)
                    .where(Platinum.hunter != "*Default*")
                    .where(Platinum.game != "*Default*")
                    .order_by(Platinum.id)
                )
            ).all()

            if len(records) == 0:
                statement_default = (
                    select(Platinum)
                    .where(Platinum.chat_id == chat_id)
                    .where(Platinum.hunter == "*Default*")
                    .where(Platinum.game == "*Default*")
                )
                default_avatar_record = (
                    await session.scalars(statement_default)
                ).one_or_none()

                if default_avatar_record is not None:
                    text = "Новых трофеев нет. Ставлю стандартный аватар :("
                    file_id = default_avatar_record.photo_id
                else:
                    text = "Стандартный аватар не задан. Оставляю всё как есть."
                    file_id = None

                hunter_id = None
                game = None
                platform = None
            else:
                record = records[0]

                trophy = "платиной"
                if record.platform == "Xbox":
                    trophy = "1000G"
                text = (
                    f'Поздравляем @{record.hunter} с {trophy} в игре "{record.game}" !'
                )
                file_id = record.photo_id
                hunter_id = record.user_id
                game = record.game
                platform = record.platform

                await session.delete(record)

            await session.commit()

            return file_id, hunter_id, game, platform, text

    async def get_top(self, chat_id, date: datetime):
        """This method is used to get the top from the database."""

        timezone = tz("Europe/Moscow")
        date = date.astimezone(tz=timezone)

        async with self.session() as session:
            statement = (
                select(History.hunter, func.count(History.id))
                .where(History.chat_id == chat_id)
                .where(History.date >= date)
                .group_by(History.hunter)
                .order_by(desc(func.count(History.id)))
            )
            return (await session.execute(statement)).all()

    async def get_history(self, chat_id: int, user_id: int, username: str = None):
        """This method is used to get the history from the database."""

        async with self.session() as session:
            if username is None:
                statement = (
                    select(History.game, History.date, History.platform)
                    .where(History.chat_id == chat_id)
                    .where(History.user_id == user_id)
                    .where(History.game != "*Default*")
                    .order_by(History.date)
                )
            else:
                statement = (
                    select(History.game, History.date, History.platform)
                    .where(History.chat_id == chat_id)
                    .where(History.hunter == username)
                    .where(History.game != "*Default*")
                    .order_by(History.date)
                )

            data = []
            timezone = tz("Europe/Moscow")
            for record in (await session.execute(statement)).all():
                game, date, platform = record
                date = date.astimezone(tz=timezone)
                date_str = date.strftime("%d.%m.%Y")
                data.append((game, date_str, platform))

            return data

    async def set_default_avatar_for_chat(self, chat_id: int, record: PlatinumRecord):
        """This method is used to add the record with default avatar to the database."""

        async with self.session() as session:
            statement = (
                select(Platinum)
                .where(Platinum.chat_id == chat_id)
                .where(Platinum.hunter == "*Default*")
                .where(Platinum.game == "*Default*")
            )

            existing_record = (await session.scalars(statement)).one_or_none()

            if existing_record is None:
                # Query to insert a record into the 'platinum' table
                default_avatar = Platinum(
                    chat_id=chat_id,
                    hunter=record.hunter,
                    game=record.game,
                    photo_id=record.photo_id,
                    platform=record.platform,
                    user_id=None,
                )
                session.add(default_avatar)
            else:
                existing_record.photo_id = record.photo_id

            # Commit the changes to the database
            await session.commit()

    async def add_record(self, chat_id: int, record: PlatinumRecord) -> None:
        """This method is used to add the record to the database."""

        # In case of Default avatar
        if record.hunter == "*Default*" and record.game == "*Default*":
            await self.set_default_avatar_for_chat(chat_id=chat_id, record=record)
            return

        async with self.session() as session:
            statement = (
                select(Platinum)
                .where(Platinum.chat_id == chat_id)
                .where(Platinum.user_id == record.user_id)
                .where(Platinum.game == record.game)
                .where(Platinum.platform == record.platform)
            )

            existing_record = (await session.scalars(statement)).one_or_none()

            if existing_record is None:
                # Query to insert a record into the 'platinum' table
                platinum = Platinum(
                    chat_id=chat_id,
                    hunter=record.hunter,
                    game=record.game,
                    photo_id=record.photo_id,
                    platform=record.platform,
                    user_id=record.user_id,
                )
                session.add(platinum)

                # Query to insert a record into the 'history' table
                history = History(
                    chat_id=chat_id,
                    hunter=record.hunter,
                    game=record.game,
                    platform=record.platform,
                    user_id=record.user_id,
                )
                session.add(history)
            else:
                existing_record.photo_id = record.photo_id

            # Commit the changes to the database
            await session.commit()

    async def delete_record(self, chat_id, username, user_id) -> str:
        """This method is used to delete the record from the database."""

        async with self.session() as session:
            statement = (
                select(Platinum)
                .where(Platinum.chat_id == chat_id)
                .where(Platinum.user_id == user_id)
                .order_by(Platinum.id)
            )

            records_user = (await session.scalars(statement)).all()

            if len(records_user) == 0:
                text = f"Удалять у @{username} нечего. Поднажми!"
            else:
                record = records_user[-1]

                statement_delete = (
                    delete(History)
                    .where(History.chat_id == chat_id)
                    .where(History.user_id == record.user_id)
                    .where(History.game == record.game)
                )

                await session.delete(record)
                await session.execute(statement_delete)

                text = f"Трофей в игре {record.game} игрока @{record.hunter} успешно удален"

                await session.commit()

        return text

    async def get_records_data(self, chat_id):
        """This method is used to get the records data from the database."""

        async with self.session() as session:
            statement = (
                select(Platinum.hunter, Platinum.game)
                .where(Platinum.chat_id == chat_id)
                .where(Platinum.hunter != "*Default*")
                .order_by(Platinum.id)
            )

            return (await session.execute(statement)).all()

    async def get_history_id(
        self, chat_id: int, user_id: int, game: str, platform: str
    ) -> Optional[int]:
        """This method is used to get ID History from the database."""

        async with self.session() as session:
            statement = (
                select(History.id)
                .where(History.chat_id == chat_id)
                .where(History.user_id == user_id)
                .where(History.game == game)
                .where(History.platform == platform)
            )

            history_id = (await session.execute(statement)).one_or_none()

            if history_id is None:
                return None

            return history_id[0]

    async def add_survey(
        self,
        game_score: int,
        picture_score: int,
        difficulty_score: int,
        user_id: int,
        trophy_id: int,
    ) -> None:
        """This method is used to add the survey to the database."""

        async with self.session() as session:
            statement = (
                select(Scores)
                .where(Scores.user_id == user_id)
                .where(Scores.trophy_id == trophy_id)
            )

            existing_record = (await session.scalars(statement)).one_or_none()
            if existing_record is None:
                scores = Scores(
                    game=game_score,
                    picture=picture_score,
                    difficulty=difficulty_score,
                    user_id=user_id,
                    trophy_id=trophy_id,
                )

                session.add(scores)
            else:
                existing_record.game = game_score
                existing_record.picture = picture_score
                existing_record.difficulty = difficulty_score

            await session.commit()

    async def add_avatar_date(self, history_id: int, date: datetime):
        """This method is used to add avatar date to the history table."""

        async with self.session() as session:
            statement = (
                update(History).where(History.id == history_id).values(avatar_date=date)
            )

            await session.execute(statement)
            await session.commit()

    async def get_survey_results(
        self, chat_id: int, field, from_date: datetime, to_date: datetime
    ) -> List[Tuple[int, str, str, float]]:
        """This method is used to get the survey results."""

        async with self.session() as session:
            score_avg = func.round(func.avg(field), 2)
            statement = (
                select(Scores.trophy_id, History.hunter, History.game, score_avg)
                .join(History, History.id == Scores.trophy_id)
                .where(History.chat_id == chat_id)
                .where(between(History.avatar_date, from_date, to_date))
                .group_by(Scores.trophy_id, History.hunter, History.game)
                .order_by(desc(score_avg))
            )

            results_score = await session.execute(statement)

        return results_score.all()

    async def add_survey_history(self, score_type: str, data: List[Tuple[int, float]]):
        """This method is used to add results surveys to surveys history"""
        async with self.session() as session:
            statement = (
                insert(Surveys)
                .values(
                    **{"trophy_id": bindparam("id"), score_type: bindparam("score")}
                )
                .on_conflict_do_update(
                    index_elements=["trophy_id"], set_={score_type: bindparam("score")}
                )
            )

            await session.execute(
                statement, [{"id": row[0], "score": row[1]} for row in data]
            )
            await session.commit()

    async def delete_scores(self, trophy_ids: List[int]):
        """This method is used to delete scores"""

        async with self.session() as session:
            statement_delete = delete(Scores).where(Scores.trophy_id.in_(trophy_ids))

            await session.execute(statement_delete)
            await session.commit()
