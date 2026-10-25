"""Broadcast bot: admin-এর পাঠানো যেকোনো পোস্ট (লেখা, PDF, ছবি, ভিডিও, অ্যালবাম)
নিবন্ধিত সব গ্রুপ/চ্যানেলে কপি করে দেয়।"""
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatType
from telegram.error import TelegramError
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_IDS = {int(x) for x in os.environ["ADMIN_IDS"].split(",") if x.strip()}
CHATS_FILE = Path(__file__).with_name("chats.json")
ALBUM_WAIT = 2  # সেকেন্ড: অ্যালবামের সব ফাইল আসার জন্য অপেক্ষা

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def load_chats() -> dict[str, str]:
    return json.loads(CHATS_FILE.read_text()) if CHATS_FILE.exists() else {}


def save_chats(chats: dict[str, str]) -> None:
    CHATS_FILE.write_text(json.dumps(chats, ensure_ascii=False, indent=2))


def is_admin(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id in ADMIN_IDS


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "নির্দেশনা:\n"
        "১. বটকে গ্রুপ/চ্যানেলে অ্যাডমিন করুন\n"
        "২. গ্রুপে /add লিখুন (চ্যানেলের জন্য এখানে /add <chat_id বা @username>)\n"
        "৩. এরপর এখানে যা পাঠাবেন সব জায়গায় পোস্ট হবে\n\n"
        "/list – তালিকা দেখুন\n/remove <chat_id> – বাদ দিন\n/myid – আপনার ID"
    )


async def myid(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"User ID: {update.effective_user.id}\nChat ID: {update.effective_chat.id}")


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    if context.args:
        try:
            chat = await context.bot.get_chat(context.args[0])
        except TelegramError as e:
            await update.effective_message.reply_text(f"চ্যাট পাওয়া যায়নি: {e}")
            return
    else:
        chat = update.effective_chat
        if chat.type == ChatType.PRIVATE:
            await update.message.reply_text("গ্রুপে গিয়ে /add দিন, অথবা /add <chat_id>")
            return
    chats = load_chats()
    chats[str(chat.id)] = chat.title or chat.username or str(chat.id)
    save_chats(chats)
    await update.effective_message.reply_text(f"✅ যুক্ত হয়েছে: {chats[str(chat.id)]}")


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    chats = load_chats()
    key = context.args[0] if context.args else str(update.effective_chat.id)
    if chats.pop(key, None) is None:
        await update.effective_message.reply_text("এই ID তালিকায় নেই।")
        return
    save_chats(chats)
    await update.effective_message.reply_text("🗑 বাদ দেওয়া হয়েছে।")


async def list_chats(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    chats = load_chats()
    text = "\n".join(f"• {name} (`{cid}`)" for cid, name in chats.items())
    await update.message.reply_text(text or "কোনো গ্রুপ/চ্যানেল যুক্ত নেই।", parse_mode="Markdown")


async def broadcast(context: ContextTypes.DEFAULT_TYPE, from_chat: int, msg_ids: list[int]) -> None:
    chats = load_chats()
    ok, failed = 0, []
    for cid, name in chats.items():
        try:
            if len(msg_ids) == 1:
                await context.bot.copy_message(cid, from_chat, msg_ids[0])
            else:
                await context.bot.copy_messages(cid, from_chat, msg_ids)
            ok += 1
        except TelegramError as e:
            log.warning("Failed for %s: %s", cid, e)
            failed.append(f"{name}: {e.message}")
    report = f"📤 পোস্ট হয়েছে {ok}/{len(chats)} জায়গায়।"
    if failed:
        report += "\n❌ ব্যর্থ:\n" + "\n".join(failed)
    await context.bot.send_message(from_chat, report)


async def flush_album(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    await broadcast(context, data["chat"], sorted(data["ids"]))


async def on_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        await update.message.reply_text("আপনি এই বট ব্যবহারের অনুমতিপ্রাপ্ত নন।")
        return
    msg = update.message
    if not load_chats():
        await msg.reply_text("আগে /add দিয়ে গ্রুপ/চ্যানেল যুক্ত করুন।")
        return
    if msg.media_group_id:  # অ্যালবাম: একসাথে পাঠাতে কিছুক্ষণ জমা রাখি
        name = f"album-{msg.media_group_id}"
        jobs = context.job_queue.get_jobs_by_name(name)
        if jobs:
            jobs[0].data["ids"].append(msg.message_id)
        else:
            context.job_queue.run_once(flush_album, ALBUM_WAIT, name=name,
                                       data={"chat": msg.chat_id, "ids": [msg.message_id]})
        return
    await broadcast(context, msg.chat_id, [msg.message_id])


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("list", list_chats))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, on_post))
    log.info("Bot চালু হয়েছে")
    app.run_polling()


if __name__ == "__main__":
    main()
