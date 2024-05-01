"""
This module contains describes database schemas.
"""

from sqlalchemy import DateTime, Text, BigInteger, Column, func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

class Base(DeclarativeBase):
    pass

class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(BigInteger, primary_key=True)
    date = Column(DateTime(timezone=True))
    delta: Mapped[int]

class History(Base):
    __tablename__= "history"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id = Column(BigInteger)
    hunter = Column(Text)
    game = Column(Text)
    date = Column(DateTime(timezone=True), server_default=func.now())
    platform = Column(Text, default="Playstation")
    user_id = Column(BigInteger)

class Platinum(Base):
    __tablename__ = "platinum"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id = Column(BigInteger)
    hunter = Column(Text)
    game = Column(Text)
    platform = Column(Text, default="Playstation")
    photo_id = Column(Text)
    user_id = Column(BigInteger)

class Scores(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    trophie_id: Mapped[int]
    user_id = Column(BigInteger)
    picture: Mapped[int]
    game: Mapped[int]
    difficulty: Mapped[int]
