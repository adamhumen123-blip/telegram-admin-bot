from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from bot.config import load_settings
from bot.db import create_tables, init_engine
from bot.handlers import admin, moderation, user

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def post_init(application) -> None:
    await create_tables()
    logger.info("Database initialized.")


def build_application():
    settings = load_settings()
    init_engine(settings.database_url)

    app = ApplicationBuilder().token(settings.bot_token).post_init(post_init).concurrent_updates(True).build()
    app.bot_data["settings"] = settings

    app.add_handler(CommandHandler("start", user.start))
    app.add_handler(CommandHandler("help", user.help_command))
    app.add_handler(CommandHandler("rules", user.rules))
    app.add_handler(CommandHandler("setrules", admin.set_rules))
    app.add_handler(CommandHandler("setwelcome", admin.set_welcome))
    app.add_handler(CommandHandler("welcomeon", admin.welcome_on))
    app.add_handler(CommandHandler("welcomeoff", admin.welcome_off))
    app.add_handler(CommandHandler("warn", admin.warn))
    app.add_handler(CommandHandler("warnings", admin.warnings))
    app.add_handler(CommandHandler("clearwarns", admin.clearwarns))
    app.add_handler(CommandHandler("mute", admin.mute))
    app.add_handler(CommandHandler("unmute", admin.unmute))
    app.add_handler(CommandHandler("ban", admin.ban))
    app.add_handler(CommandHandler("unban", admin.unban))
    app.add_handler(CommandHandler("kick", admin.kick))
    app.add_handler(CommandHandler("status", admin.status))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, user.welcome_new_members))
    app.add_handler(MessageHandler(filters.TEXT | filters.CaptionRegex(".*"), moderation.auto_moderate))
    return app


def main() -> None:
    app = build_application()
    logger.info("Starting Telegram admin bot...")
    app.run_polling(allowed_updates=["message", "chat_member", "my_chat_member"])


if __name__ == "__main__":
    main()
