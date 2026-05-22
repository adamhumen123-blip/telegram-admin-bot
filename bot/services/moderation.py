from __future__ import annotations

import re
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from telegram import ChatPermissions, Message, User
from telegram.ext import ContextTypes

from bot.db import get_sessionmaker
from bot.models import ChatSettings, UserRecord

URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
INVITE_RE = re.compile(r"(t\.me/joinchat|t\.me/\+|telegram\.me/joinchat)", re.IGNORECASE)
_flood_cache: dict[tuple[int, int], deque[datetime]] = defaultdict(deque)


async def get_or_create_chat_settings(chat_id: int, title: str | None = None) -> ChatSettings:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(select(ChatSettings).where(ChatSettings.chat_id == chat_id))
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = ChatSettings(chat_id=chat_id, title=title)
            session.add(settings)
            await session.commit()
            await session.refresh(settings)
        return settings


async def upsert_user(chat_id: int, user: User) -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(select(UserRecord).where(UserRecord.chat_id == chat_id, UserRecord.user_id == user.id))
        record = result.scalar_one_or_none()
        if record is None:
            record = UserRecord(chat_id=chat_id, user_id=user.id, username=user.username, first_name=user.first_name, messages_seen=1, last_seen=datetime.utcnow())
            session.add(record)
        else:
            record.username = user.username
            record.first_name = user.first_name
            record.messages_seen += 1
            record.last_seen = datetime.utcnow()
        await session.commit()


async def add_warning(chat_id: int, user: User) -> int:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(select(UserRecord).where(UserRecord.chat_id == chat_id, UserRecord.user_id == user.id))
        record = result.scalar_one_or_none()
        if record is None:
            record = UserRecord(chat_id=chat_id, user_id=user.id, username=user.username, first_name=user.first_name)
            session.add(record)
            await session.flush()
        record.warnings += 1
        warnings = record.warnings
        await session.commit()
        return warnings


async def clear_warnings(chat_id: int, user_id: int) -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(select(UserRecord).where(UserRecord.chat_id == chat_id, UserRecord.user_id == user_id))
        record = result.scalar_one_or_none()
        if record:
            record.warnings = 0
            await session.commit()


async def get_warnings(chat_id: int, user_id: int) -> int:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(select(UserRecord).where(UserRecord.chat_id == chat_id, UserRecord.user_id == user_id))
        record = result.scalar_one_or_none()
        return record.warnings if record else 0


def has_forbidden_content(text: str, settings: ChatSettings) -> str | None:
    if settings.anti_links and URL_RE.search(text):
        return "links are not allowed"
    if settings.anti_invites and INVITE_RE.search(text):
        return "Telegram invite links are not allowed"
    bad_words = [w.strip().lower() for w in settings.bad_words.split(",") if w.strip()]
    lowered = text.lower()
    for word in bad_words:
        if word in lowered:
            return "forbidden language"
    return None


def is_flooding(chat_id: int, user_id: int, settings: ChatSettings) -> bool:
    key = (chat_id, user_id)
    now = datetime.now(timezone.utc)
    queue = _flood_cache[key]
    window_start = now - timedelta(seconds=settings.flood_seconds)
    while queue and queue[0] < window_start:
        queue.popleft()
    queue.append(now)
    return len(queue) > settings.flood_messages


async def mute_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, minutes: int) -> None:
    until_date = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    permissions = ChatPermissions(can_send_messages=False)
    await context.bot.restrict_chat_member(chat_id, user_id, permissions=permissions, until_date=until_date)


async def unmute_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> None:
    permissions = ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True, can_send_photos=True, can_send_videos=True, can_send_video_notes=True, can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True)
    await context.bot.restrict_chat_member(chat_id, user_id, permissions=permissions)


async def safe_delete(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        pass
