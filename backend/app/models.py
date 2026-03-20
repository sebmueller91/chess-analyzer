from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    last_analyzed_at = Column(DateTime, nullable=True)
    games_analyzed = Column(Integer, default=0)
    time_control = Column(String, nullable=True)
    status = Column(String, default="idle")
    error_message = Column(String, nullable=True)

    games = relationship("Game", back_populates="player", cascade="all, delete-orphan")
    reports = relationship(
        "Report", back_populates="player", cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "ChatMessage", back_populates="player", cascade="all, delete-orphan"
    )


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    chess_com_id = Column(String, unique=True)
    pgn = Column(Text)
    time_control = Column(String)
    player_color = Column(String)
    result = Column(String)
    opponent = Column(String)
    date_played = Column(DateTime)
    opening_name = Column(String, nullable=True)
    eco_code = Column(String, nullable=True)

    player = relationship("Player", back_populates="games")
    analysis_result = relationship(
        "AnalysisResult", back_populates="game", uselist=False, cascade="all, delete-orphan"
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    mistakes = Column(JSON)
    opening_accuracy = Column(Float)
    middlegame_accuracy = Column(Float)
    endgame_accuracy = Column(Float)
    total_blunders = Column(Integer)
    total_mistakes = Column(Integer)
    total_inaccuracies = Column(Integer)

    game = relationship("Game", back_populates="analysis_result")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    report_data = Column(JSON)
    coaching_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    player = relationship("Player", back_populates="reports")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    player = relationship("Player", back_populates="chat_messages")
