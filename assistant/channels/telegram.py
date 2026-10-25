"""Telegram personal account (userbot via Telethon).

Also acts as the control panel: send commands to your own "Saved Messages":
  /busy  /free  /auto  /status  /drafts  /send <id>  /edit <id> <text>  /skip <id>
"""
import logging

from telethon import TelegramClient, events

from .. import config, presence, router, store

log = logging.getLogger("telegram")
client = TelegramClient("data/telegram", int(config.TG_API_ID or 0), config.TG_API_HASH)
PLATFORM = "telegram"
_me_id = None


async def _backfill(chat_id: int, sender: str) -> None:
    """First time we see a chat, import recent history so Claude has full context."""
    if store.has_history(PLATFORM, str(chat_id)):
        return
    msgs = await client.get_messages(chat_id, limit=config.HISTORY_LIMIT)
    for m in reversed(msgs[1:]):  # skip the newest (it is the incoming one)
        if m.text:
            store.add_message(PLATFORM, str(chat_id), "Me" if m.out else sender, m.text, m.out)


async def _send(chat_id: str, text: str, meta: str) -> None:
    await client.send_message(int(chat_id), text)


async def _notify(text: str) -> None:
    await client.send_message("me", text)


async def _command(text: str) -> str:
    parts = text.split(maxsplit=2)
    cmd = parts[0].lower()
    if cmd in ("/busy", "/free", "/auto"):
        presence.set_mode(cmd[1:])
        return f"Mode: {cmd[1:]} (busy now = {presence.is_busy()})"
    if cmd == "/status":
        return f"Mode: {presence.mode()} · busy now: {presence.is_busy()} · model: {config.CLAUDE_MODEL}"
    if cmd == "/drafts":
        rows = store.pending_drafts()
        return "\n\n".join(f"#{r['id']} {r['platform']}/{r['sender']}: {r['draft'][:200]}" for r in rows) or "No drafts."
    if cmd in ("/send", "/edit", "/skip") and len(parts) > 1 and parts[1].isdigit():
        did = int(parts[1])
        if cmd == "/skip":
            store.close_draft(did, "skipped")
            return f"Skipped #{did}."
        if cmd == "/edit" and len(parts) < 3:
            return "Usage: /edit <id> <new text>"
        return await router.send_draft(did, parts[2] if cmd == "/edit" else None)
    return "Commands: /busy /free /auto /status /drafts /send id /edit id text /skip id"


@client.on(events.NewMessage)
async def on_message(event) -> None:
    text = event.raw_text or ""
    # Control panel: messages you write in Saved Messages
    if event.chat_id == _me_id:
        if text.startswith("/"):
            await event.reply(await _command(text))
        return
    if not event.is_private or not text:
        return
    sender = await event.get_sender()
    if getattr(sender, "bot", False):
        return
    name = " ".join(filter(None, [getattr(sender, "first_name", ""), getattr(sender, "last_name", "")])) or "Unknown"
    if event.out:  # you replied yourself from your phone -> keep context
        store.add_message(PLATFORM, str(event.chat_id), "Me", text, from_me=True)
        return
    await _backfill(event.chat_id, name)
    await router.handle_incoming(PLATFORM, str(event.chat_id), name, text)


async def start() -> None:
    global _me_id
    await client.start(phone=config.TG_PHONE)
    _me_id = (await client.get_me()).id
    router.register_sender(PLATFORM, _send)
    router.set_notifier(_notify)
    log.info("Telegram connected")
    await client.run_until_disconnected()
