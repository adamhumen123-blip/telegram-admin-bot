from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.moderation import get_or_create_chat_settings


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("Admin bot is online. Use /help to see commands.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Admin Bot Commands\n\n"
        "/rules - Show rules\n"
        "/setrules <text> - Set rules\n"
        "/setwelcome <text> - Set welcome message\n"
        "/welcomeon /welcomeoff - Toggle welcomes\n"
        "/warn, /warnings, /clearwarns\n"
        "/mute, /unmute, /ban, /unban, /kick\n"
        "/status - Show bot status\n\n"
        "Tip: Reply to a user's message when using moderation commands."
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    settings = await get_or_create_chat_settings(chat.id, chat.title if chat else None)
    await update.effective_message.reply_text(f"Group Rules:\n\n{settings.rules_text}")


async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    if not chat or not message or not message.new_chat_members:
        return

    settings = await get_or_create_chat_settings(chat.id, chat.title)
    if not settings.welcome_enabled:
        return

    for new_user in message.new_chat_members:
        text = settings.welcome_text.format(
            first_name=new_user.first_name or "there",
            username=f"@{new_user.username}" if new_user.username else "",
            user_id=new_user.id,
            chat_title=chat.title or "this chat",
        )
        await message.reply_text(text)
