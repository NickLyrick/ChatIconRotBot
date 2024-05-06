"""
This module contains describes database schemas.
"""

from sqlalchemy import BigInteger, Integer, Double, Column, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Chat(Base):
    """This class is the represente declare table chats"""
    __tablename__ = "chats"

    chat_id = Column(BigInteger, primary_key=True)
    date = Column(DateTime(timezone=True))
    delta = Column(Integer)


class History(Base):
    """This class is the represente declare table history"""
    __tablename__ = "history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger)
    hunter = Column(Text)
    game = Column(Text)
    date = Column(DateTime(timezone=True), server_default=func.now())
    platform = Column(Text, default="Playstation")
    user_id = Column(BigInteger)
    avatar_date = Column(DateTime(timezone=True))


class Platinum(Base):
    """This class is the represente declare table platinum"""
    __tablename__ = "platinum"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger)
    hunter = Column(Text)
    game = Column(Text)
    platform = Column(Text, default="Playstation")
    photo_id = Column(Text)
    user_id = Column(BigInteger)


class Scores(Base):
    """This class is the represente declare table scores"""
    __tablename__ = "scores"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trophy_id = Column(BigInteger, ForeignKey(History.id), nullable=False)
    user_id = Column(BigInteger)
    picture = Column(Integer)
    game = Column(Integer)
    difficulty = Column(Integer)

class Surveys(Base):
    """This class is the represente declare table surveys"""
    __tablename__ = "surveys"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trophy_id = Column(BigInteger, ForeignKey(History.id), nullable=False)
    picture = Column(Double, nullable=False)
    game = Column(Double, nullable=False)
    difficulty = Column(Double, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
