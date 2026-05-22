from __future__ import annotations

from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from bot.db import Base


class ChatSettings(Base):
    __tablename__ = "chat_settings"
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255))
    welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    welcome_text: Mapped[str] = mapped_column(Text, default="Welcome {first_name} to {chat_title}! Please read /rules.")
    rules_text: Mapped[str] = mapped_column(Text, default="Be respectful. No spam. Follow admin instructions.")
    warn_limit: Mapped[int] = mapped_column(Integer, default=3)
    anti_links: Mapped[bool] = mapped_column(Boolean, default=True)
    anti_invites: Mapped[bool] = mapped_column(Boolean, default=True)
    anti_flood: Mapped[bool] = mapped_column(Boolean, default=True)
    flood_seconds: Mapped[int] = mapped_column(Integer, default=8)
    flood_messages: Mapped[int] = mapped_column(Integer, default=5)
    bad_words: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserRecord(Base):
    __tablename__ = "user_records"
    __table_args__ = (UniqueConstraint("chat_id", "user_id", name="uq_user_chat"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    warnings: Mapped[int] = mapped_column(Integer, default=0)
    messages_seen: Mapped[int] = mapped_column(Integer, default=0)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ModerationLog(Base):
    __tablename__ = "moderation_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    actor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
