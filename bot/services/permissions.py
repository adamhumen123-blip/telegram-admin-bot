from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int | None = None) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat is None:
        return False
    target_id = user_id or (user.id if user else None)
    if target_id is None:
        return False
    member = await context.bot.get_chat_member(chat.id, target_id)
    return member.status in {"administrator", "creator"}
