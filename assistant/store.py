"""SQLite storage: full chat history, pending drafts and busy state."""
import os
import sqlite3
import time
from dataclasses import dataclass

from . import config

os.makedirs(os.path.dirname(config.DB_PATH) or ".", exist_ok=True)
_db = sqlite3.connect(config.DB_PATH, check_same_thread=False)
_db.row_factory = sqlite3.Row
_db.executescript(
    """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY, platform TEXT, chat_id TEXT, sender TEXT,
        from_me INTEGER, text TEXT, ts REAL);
    CREATE INDEX IF NOT EXISTS idx_chat ON messages(platform, chat_id, ts);
    CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY, platform TEXT, chat_id TEXT, sender TEXT,
        incoming TEXT, draft TEXT, meta TEXT, status TEXT DEFAULT 'pending', ts REAL);
    CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT);
    """
)
_db.commit()


@dataclass
class Draft:
    id: int
    platform: str
    chat_id: str
    sender: str
    incoming: str
    draft: str
    meta: str


def add_message(platform: str, chat_id: str, sender: str, text: str, from_me: bool) -> None:
    _db.execute(
        "INSERT INTO messages(platform, chat_id, sender, from_me, text, ts) VALUES (?,?,?,?,?,?)",
        (platform, str(chat_id), sender, int(from_me), text, time.time()),
    )
    _db.commit()


def history(platform: str, chat_id: str, limit: int) -> list[sqlite3.Row]:
    rows = _db.execute(
        "SELECT * FROM messages WHERE platform=? AND chat_id=? ORDER BY ts DESC LIMIT ?",
        (platform, str(chat_id), limit),
    ).fetchall()
    return list(reversed(rows))


def has_history(platform: str, chat_id: str) -> bool:
    return _db.execute(
        "SELECT 1 FROM messages WHERE platform=? AND chat_id=? LIMIT 1", (platform, str(chat_id))
    ).fetchone() is not None


def save_draft(platform: str, chat_id: str, sender: str, incoming: str, draft: str, meta: str = "") -> int:
    cur = _db.execute(
        "INSERT INTO drafts(platform, chat_id, sender, incoming, draft, meta, ts) VALUES (?,?,?,?,?,?,?)",
        (platform, str(chat_id), sender, incoming, draft, meta, time.time()),
    )
    _db.commit()
    return cur.lastrowid


def get_draft(draft_id: int) -> Draft | None:
    r = _db.execute(
        "SELECT * FROM drafts WHERE id=? AND status='pending'", (draft_id,)
    ).fetchone()
    return Draft(r["id"], r["platform"], r["chat_id"], r["sender"], r["incoming"], r["draft"], r["meta"]) if r else None


def pending_drafts() -> list[sqlite3.Row]:
    return _db.execute("SELECT * FROM drafts WHERE status='pending' ORDER BY ts").fetchall()


def close_draft(draft_id: int, status: str) -> None:
    _db.execute("UPDATE drafts SET status=? WHERE id=?", (status, draft_id))
    _db.commit()


def get_state(key: str, default: str = "") -> str:
    r = _db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
    return r["value"] if r else default


def set_state(key: str, value: str) -> None:
    _db.execute("INSERT OR REPLACE INTO state(key, value) VALUES (?,?)", (key, value))
    _db.commit()
