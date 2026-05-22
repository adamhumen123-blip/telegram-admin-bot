from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Settings
from bot.services.logging import log_action
from bot.services.moderation import add_warning, get_or_create_chat_settings, has_forbidden_content, is_flooding, mute_user, safe_delete, upsert_user
from bot.services.permissions import is_admin


async def auto_moderate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message or not chat or not user or user.is_bot:
        return

    await upsert_user(chat.id, user)

    if await is_admin(update, context, user.id):
        return

    chat_settings = await get_or_create_chat_settings(chat.id, chat.title)
    text = message.text or message.caption or ""
    reason = has_forbidden_content(text, chat_settings) if text else None

    if not reason and chat_settings.anti_flood and is_flooding(chat.id, user.id, chat_settings):
        reason = "message flooding"

    if not reason:
        return

    await safe_delete(message)
    count = await add_warning(chat.id, user)
    await log_action(context, settings, chat.id, "auto_warn", None, user.id, reason)

    if count >= chat_settings.warn_limit:
        await mute_user(context, chat.id, user.id, 60)
        await log_action(context, settings, chat.id, "auto_mute", None, user.id, "warning limit reached")
        await context.bot.send_message(chat.id, f"{user.first_name} was muted for 60 minutes after repeated violations.")
    else:
        await context.bot.send_message(chat.id, f"{user.first_name}, {reason}. Warning {count}/{chat_settings.warn_limit}.")
