"""
This module contains describes database schemas.
"""

from sqlalchemy import (
    REAL,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Chat(Base):
    """This class is the represent declare table chats"""

    __tablename__ = "chats"
    __table_args__ = {
        "comment": "Chat table where the bot is running",
    }

    chat_id = Column(BigInteger, primary_key=True)
    date = Column(DateTime(timezone=True), nullable=False)
    delta = Column(Integer, nullable=False)


class History(Base):
    """This class is the represent declare table history"""

    __tablename__ = "history"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        server_default=Identity(
            always=True,
            start=1,
            increment=1,
            minvalue=1,
            maxvalue=9223372036854775807,
            cycle=False,
            cache=1,
        ),
    )
    chat_id = Column(BigInteger, nullable=False)
    hunter = Column(Text, nullable=False)
    game = Column(Text, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    platform = Column(Text, default="Playstation")
    user_id = Column(BigInteger)
    avatar_date = Column(DateTime(timezone=True))


class Platinum(Base):
    """This class is the represent declare table platinum"""

    __tablename__ = "platinum"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        server_default=Identity(
            always=True,
            start=1,
            increment=1,
            minvalue=1,
            maxvalue=9223372036854775807,
            cycle=False,
            cache=1,
        ),
        comment="Unique ID",
    )
    chat_id = Column(BigInteger, nullable=False)
    hunter = Column(Text, nullable=False)
    game = Column(Text, nullable=False)
    platform = Column(Text, default="Playstation")
    photo_id = Column(Text, nullable=False)
    user_id = Column(BigInteger)


class Scores(Base):
    """This class is the represent declare table scores"""

    __tablename__ = "scores"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        server_default=Identity(
            always=True,
            start=1,
            increment=1,
            minvalue=1,
            maxvalue=9223372036854775807,
            cycle=False,
            cache=1,
        ),
    )
    trophy_id = Column(BigInteger, ForeignKey(History.id), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    picture = Column(Integer)
    game = Column(Integer)
    difficulty = Column(Integer)


class Surveys(Base):
    """This class is the represent declare table surveys"""

    __tablename__ = "surveys"

    trophy_id = Column(
        BigInteger, ForeignKey(History.id), nullable=False, primary_key=True
    )
    picture = Column(REAL)
    game = Column(REAL)
    difficulty = Column(REAL)
