"""Central flow: every incoming message from any platform comes here.

busy  -> reply is sent automatically
free  -> reply is saved as a draft and you get it in Telegram "Saved Messages" to approve/edit
"""
import logging
from typing import Awaitable, Callable

from . import brain, presence, store

log = logging.getLogger("router")

Sender = Callable[[str, str, str], Awaitable[None]]  # (chat_id, text, meta)
_senders: dict[str, Sender] = {}
_notify: Callable[[str], Awaitable[None]] | None = None


def register_sender(platform: str, fn: Sender) -> None:
    _senders[platform] = fn


def set_notifier(fn: Callable[[str], Awaitable[None]]) -> None:
    global _notify
    _notify = fn


async def notify(text: str) -> None:
    if _notify:
        await _notify(text)
    else:
        log.info("NOTIFY: %s", text)


async def send(platform: str, chat_id: str, text: str, meta: str = "") -> None:
    await _senders[platform](chat_id, text, meta)
    store.add_message(platform, chat_id, "Me", text, from_me=True)


async def handle_incoming(platform: str, chat_id: str, sender: str, text: str,
                          meta: str = "", extra: str = "") -> None:
    store.add_message(platform, chat_id, sender, text, from_me=False)
    busy = presence.is_busy()
    try:
        reply = await brain.generate_reply(platform, chat_id, sender, busy, extra)
    except Exception:
        log.exception("Claude call failed")
        return
    if not reply:
        return
    if busy:
        await send(platform, chat_id, reply, meta)
        await notify(f"🤖 Auto-replied on {platform} to {sender}:\n> {text[:300]}\n\n{reply}")
    else:
        did = store.save_draft(platform, chat_id, sender, text, reply, meta)
        await notify(
            f"📝 Draft #{did} — {platform} / {sender}\n> {text[:500]}\n\n{reply}\n\n"
            f"/send {did}  ·  /edit {did} <new text>  ·  /skip {did}"
        )


async def send_draft(draft_id: int, override: str | None = None) -> str:
    d = store.get_draft(draft_id)
    if not d:
        return f"Draft #{draft_id} not found."
    await send(d.platform, d.chat_id, override or d.draft, d.meta)
    store.close_draft(draft_id, "sent")
    return f"✅ Sent #{draft_id} to {d.sender} ({d.platform})."
