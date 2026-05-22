# Telegram Admin Bot

A fast, secure Python Telegram admin bot for managing Telegram groups and channels.

## Features

- Admin commands
- Auto moderation
- Welcome messages
- Spam and flood protection
- Link and invite filtering
- Bad-word filtering
- Mute, unmute, ban, unban, kick
- Warning system
- Moderation logs
- User tracking
- SQLite database with SQLAlchemy async
- Docker-ready deployment

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m bot.main
```

Edit `.env` first:

```env
BOT_TOKEN=123456:your-token
OWNER_IDS=123456789
LOG_CHAT_ID=
DATABASE_URL=sqlite+aiosqlite:///./bot.db
```

## Docker

```bash
docker compose up --build -d
```

## Required Telegram Permissions

Add the bot as an admin in your group/channel and allow:

- Delete messages
- Ban users
- Restrict users
- Manage messages

## Commands

| Command | Description |
|---|---|
| `/start` | Bot status |
| `/help` | Command list |
| `/rules` | Show group rules |
| `/setrules <text>` | Set group rules |
| `/setwelcome <text>` | Set welcome message |
| `/welcomeon` | Enable welcomes |
| `/welcomeoff` | Disable welcomes |
| `/warn` | Warn replied user |
| `/warnings` | Show replied user's warnings |
| `/clearwarns` | Clear replied user's warnings |
| `/mute 30m` | Mute replied user |
| `/unmute` | Unmute replied user |
| `/ban` | Ban replied user |
| `/unban <user_id>` | Unban user |
| `/kick` | Kick replied user |
| `/status` | Bot/group status |

## Security Notes

- Never commit `.env`.
- Keep `BOT_TOKEN` private.
- Use `OWNER_IDS` for owner-level control.
- Give the bot only required permissions.
- Use PostgreSQL for high-traffic production groups.

## GitHub/Codex Prompt

Use this with Codex:

```text
Review this Telegram admin bot repository and make it production-ready. Improve admin permission checks, moderation reliability, tests, Docker deployment, documentation, and security.
```
