from __future__ import annotations

import re
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Settings
from bot.db import get_sessionmaker
from bot.models import ChatSettings
from bot.services.logging import log_action
from bot.services.moderation import add_warning, clear_warnings, get_or_create_chat_settings, get_warnings, mute_user, unmute_user
from bot.services.permissions import is_admin

DURATION_RE = re.compile(r"^(\d+)(m|h|d)?$")


def _parse_duration(value: str) -> int:
    match = DURATION_RE.match(value.strip().lower())
    if not match:
        return 30
    amount = int(match.group(1))
    unit = match.group(2) or "m"
    if unit == "h":
        return amount * 60
    if unit == "d":
        return amount * 24 * 60
    return amount


async def _require_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not await is_admin(update, context):
        await update.effective_message.reply_text("Admins only.")
        return False
    return True


def _target_from_reply(update: Update):
    message = update.effective_message
    if message and message.reply_to_message:
        return message.reply_to_message.from_user
    return None


async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    text = " ".join(context.args).strip()
    if not text:
        await update.effective_message.reply_text("Usage: /setrules Be respectful...")
        return
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        settings = await session.get(ChatSettings, chat.id)
        if settings is None:
            settings = ChatSettings(chat_id=chat.id, title=chat.title)
            session.add(settings)
        settings.rules_text = text
        settings.updated_at = datetime.utcnow()
        await session.commit()
    await update.effective_message.reply_text("Rules updated.")


async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    text = " ".join(context.args).strip()
    if not text:
        await update.effective_message.reply_text("Usage: /setwelcome Welcome {first_name} to {chat_title}!")
        return
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        settings = await session.get(ChatSettings, chat.id)
        if settings is None:
            settings = ChatSettings(chat_id=chat.id, title=chat.title)
            session.add(settings)
        settings.welcome_text = text
        settings.updated_at = datetime.utcnow()
        await session.commit()
    await update.effective_message.reply_text("Welcome message updated.")


async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE, enabled: bool) -> None:
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        settings = await session.get(ChatSettings, chat.id)
        if settings is None:
            settings = ChatSettings(chat_id=chat.id, title=chat.title)
            session.add(settings)
        settings.welcome_enabled = enabled
        await session.commit()
    await update.effective_message.reply_text("Welcome messages enabled." if enabled else "Welcome messages disabled.")


async def welcome_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await toggle_welcome(update, context, True)


async def welcome_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await toggle_welcome(update, context, False)


async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    actor = update.effective_user
    target = _target_from_reply(update)
    if not target:
        await update.effective_message.reply_text("Reply to a user's message with /warn [reason].")
        return
    chat_settings = await get_or_create_chat_settings(chat.id, chat.title)
    count = await add_warning(chat.id, target)
    reason = " ".join(context.args).strip() or "No reason provided"
    await log_action(context, settings, chat.id, "warn", actor.id if actor else None, target.id, reason)
    if count >= chat_settings.warn_limit:
        await mute_user(context, chat.id, target.id, 60)
        await update.effective_message.reply_text(f"{target.first_name} reached {count}/{chat_settings.warn_limit} warnings and was muted for 60 minutes.")
    else:
        await update.effective_message.reply_text(f"Warning added: {target.first_name} now has {count}/{chat_settings.warn_limit} warnings.")


async def warnings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    target = _target_from_reply(update)
    if not target:
        await update.effective_message.reply_text("Reply to a user's message with /warnings.")
        return
    count = await get_warnings(chat.id, target.id)
    await update.effective_message.reply_text(f"{target.first_name} has {count} warning(s).")


async def clearwarns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    target = _target_from_reply(update)
    if not target:
        await update.effective_message.reply_text("Reply to a user's message with /clearwarns.")
        return
    await clear_warnings(chat.id, target.id)
    await update.effective_message.reply_text("Warnings cleared.")


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    actor = update.effective_user
    target = _target_from_reply(update)
    if not target:
        await update.effective_message.reply_text("Reply to a user's message with /mute 30m [reason].")
        return
    duration = _parse_duration(context.args[0]) if context.args else 30
    reason = " ".join(context.args[1:]).strip() if len(context.args) > 1 else "Muted by admin"
    await mute_user(context, chat.id, target.id, duration)
    await log_action(context, settings, chat.id, "mute", actor.id if actor else None, target.id, reason)
    await update.effective_message.reply_text(f"Muted {target.first_name} for {duration} minutes.")


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    actor = update.effective_user
    target = _target_from_reply(update)
    if not target:
        await update.effective_message.reply_text("Reply to a user's message with /unmute.")
        return
    await unmute_user(context, chat.id, target.id)
    await log_action(context, settings, chat.id, "unmute", actor.id if actor else None, target.id)
    await update.effective_message.reply_text(f"Unmuted {target.first_name}.")


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    actor = update.effective_user
    target = _target_from_reply(update)
    if not target:
        await update.effective_message.reply_text("Reply to a user's message with /ban [reason].")
        return
    reason = " ".join(context.args).strip() or "Banned by admin"
    await context.bot.ban_chat_member(chat.id, target.id)
    await log_action(context, settings, chat.id, "ban", actor.id if actor else None, target.id, reason)
    await update.effective_message.reply_text(f"Banned {target.first_name}.")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    actor = update.effective_user
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Usage: /unban <user_id>")
        return
    user_id = int(context.args[0])
    await context.bot.unban_chat_member(chat.id, user_id)
    await log_action(context, settings, chat.id, "unban", actor.id if actor else None, user_id)
    await update.effective_message.reply_text("User unbanned.")


async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not await _require_admin(update, context):
        return
    chat = update.effective_chat
    actor = update.effective_user
    target = _target_from_reply(update)
    if not target:
        await update.effective_message.reply_text("Reply to a user's message with /kick [reason].")
        return
    reason = " ".join(context.args).strip() or "Kicked by admin"
    await context.bot.ban_chat_member(chat.id, target.id)
    await context.bot.unban_chat_member(chat.id, target.id)
    await log_action(context, settings, chat.id, "kick", actor.id if actor else None, target.id, reason)
    await update.effective_message.reply_text(f"Kicked {target.first_name}.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    settings = await get_or_create_chat_settings(chat.id, chat.title)
    await update.effective_message.reply_text(
        "Bot Status\n\n"
        f"Chat: {chat.title or chat.id}\n"
        f"Welcome: {'on' if settings.welcome_enabled else 'off'}\n"
        f"Anti-links: {'on' if settings.anti_links else 'off'}\n"
        f"Anti-invites: {'on' if settings.anti_invites else 'off'}\n"
        f"Anti-flood: {'on' if settings.anti_flood else 'off'}\n"
        f"Warn limit: {settings.warn_limit}"
    )
