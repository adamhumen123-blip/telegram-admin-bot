from __future__ import annotations

from sqlalchemy import insert
from telegram.ext import ContextTypes

from bot.config import Settings
from bot.db import get_sessionmaker
from bot.models import ModerationLog


async def log_action(
    context: ContextTypes.DEFAULT_TYPE,
    settings: Settings,
    chat_id: int,
    action: str,
    actor_id: int | None = None,
    target_id: int | None = None,
    reason: str | None = None,
) -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        await session.execute(
            insert(ModerationLog).values(
                chat_id=chat_id,
                actor_id=actor_id,
                target_id=target_id,
                action=action,
                reason=reason,
            )
        )
        await session.commit()

    if settings.log_chat_id:
        text = (
            f"Moderation Log\n"
            f"Action: {action}\n"
            f"Chat: {chat_id}\n"
            f"Actor: {actor_id or '-'}\n"
            f"Target: {target_id or '-'}\n"
            f"Reason: {reason or '-'}"
        )
        try:
            await context.bot.send_message(settings.log_chat_id, text)
        except Exception:
            pass
