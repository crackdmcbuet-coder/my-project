"""Claude-powered reply generation using full chat history as context."""
import anthropic

from . import config, store

client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEM = f"""You are the personal assistant of {config.OWNER_NAME}. You read their chats on
WhatsApp, Telegram, Gmail and Messenger and write replies on their behalf.

About the owner: {config.OWNER_PROFILE}

Rules:
- Use the conversation history to understand full context, relationships and tone.
- Reply in the same language/script the other person used (Bangla, Banglish, English...).
- Sound like the owner: natural and brief. No AI disclaimers, no signatures unless it's an email.
- {{mode_rule}}
- Never commit to money, meetings, passwords, OTPs or promises; say the owner will confirm.
- If no reply is needed (e.g. "ok", a sticker, spam, newsletter), output exactly: NO_REPLY
- Output only the reply text."""

BUSY_RULE = ("The owner is BUSY now and this reply is sent automatically. Answer what you safely can, "
             "and politely mention they are busy and will get back soon.")
DRAFT_RULE = "The owner is available and will review this as a draft before sending. Write it as they would."


async def generate_reply(platform: str, chat_id: str, sender: str, busy: bool, extra: str = "") -> str | None:
    rows = store.history(platform, chat_id, config.HISTORY_LIMIT)
    transcript = "\n".join(
        f"[{'Me' if r['from_me'] else r['sender']}]: {r['text']}" for r in rows
    )
    prompt = (f"Platform: {platform}\nChat with: {sender}\n{extra}\n\n"
              f"Conversation history (oldest first):\n{transcript}\n\n"
              f"Write the owner's next reply to {sender}.")
    resp = await client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM.replace("{mode_rule}", BUSY_RULE if busy else DRAFT_RULE),
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return None if not text or text == "NO_REPLY" else text
