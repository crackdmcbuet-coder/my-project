import os
from dotenv import load_dotenv

load_dotenv()


def env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
CLAUDE_MODEL = env("CLAUDE_MODEL", "claude-sonnet-5-5")
OWNER_NAME = env("OWNER_NAME", "the owner")
OWNER_PROFILE = env("OWNER_PROFILE")
HISTORY_LIMIT = int(env("HISTORY_LIMIT", "40"))
BUSY_HOURS = env("BUSY_HOURS")
TIMEZONE = env("TIMEZONE", "Asia/Dhaka")

TG_API_ID = env("TG_API_ID")
TG_API_HASH = env("TG_API_HASH")
TG_PHONE = env("TG_PHONE")

GMAIL_ENABLED = env("GMAIL_ENABLED", "true").lower() == "true"
GMAIL_CREDENTIALS = env("GMAIL_CREDENTIALS", "credentials.json")
GMAIL_POLL_SECONDS = int(env("GMAIL_POLL_SECONDS", "60"))

META_VERIFY_TOKEN = env("META_VERIFY_TOKEN")
WHATSAPP_TOKEN = env("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID")
MESSENGER_PAGE_TOKEN = env("MESSENGER_PAGE_TOKEN")
WEBHOOK_PORT = int(env("WEBHOOK_PORT", "8000"))

DB_PATH = env("DB_PATH", "data/assistant.db")
