from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    owner_ids: set[int]
    log_chat_id: int | None
    database_url: str
    default_warn_limit: int
    default_flood_seconds: int
    default_flood_messages: int


def _parse_int_set(value: str) -> set[int]:
    output: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if item:
            output.add(int(item))
    return output


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is missing. Add it to your .env file.")

    return Settings(
        bot_token=token,
        owner_ids=_parse_int_set(os.getenv("OWNER_IDS", "")),
        log_chat_id=int(os.getenv("LOG_CHAT_ID")) if os.getenv("LOG_CHAT_ID") else None,
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db"),
        default_warn_limit=int(os.getenv("DEFAULT_WARN_LIMIT", "3")),
        default_flood_seconds=int(os.getenv("DEFAULT_FLOOD_SECONDS", "8")),
        default_flood_messages=int(os.getenv("DEFAULT_FLOOD_MESSAGES", "5")),
    )
