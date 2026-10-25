"""Gmail: polls unread inbox mail, uses the whole thread as context.

busy -> reply sent in-thread. free -> also saved as a real Gmail draft (and in /drafts).
"""
import asyncio
import base64
import json
import logging
import os
from email.mime.text import MIMEText
from email.utils import parseaddr

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .. import config, presence, router, store

log = logging.getLogger("gmail")
PLATFORM = "gmail"
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN = "data/gmail_token.json"
PROCESSED_LABEL = "AI-Processed"


def _service():
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES) if os.path.exists(TOKEN) else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = InstalledAppFlow.from_client_secrets_file(config.GMAIL_CREDENTIALS, SCOPES).run_local_server(port=0)
        with open(TOKEN, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


svc = None


def _header(msg, name):
    return next((h["value"] for h in msg["payload"]["headers"] if h["name"].lower() == name.lower()), "")


def _body(payload) -> str:
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", "ignore")
    for part in payload.get("parts", []) or []:
        text = _body(part)
        if text:
            return text
    return ""


def _label_id() -> str:
    labels = svc.users().labels().list(userId="me").execute()["labels"]
    for l in labels:
        if l["name"] == PROCESSED_LABEL:
            return l["id"]
    return svc.users().labels().create(userId="me", body={"name": PROCESSED_LABEL}).execute()["id"]


def _raw_reply(meta: dict, text: str) -> dict:
    mime = MIMEText(text)
    mime["To"] = meta["to"]
    mime["Subject"] = meta["subject"] if meta["subject"].lower().startswith("re:") else "Re: " + meta["subject"]
    mime["In-Reply-To"] = meta["msgid"]
    mime["References"] = meta["msgid"]
    return {"raw": base64.urlsafe_b64encode(mime.as_bytes()).decode(), "threadId": meta["thread"]}


async def _send(chat_id: str, text: str, meta: str) -> None:
    body = _raw_reply(json.loads(meta), text)
    await asyncio.to_thread(lambda: svc.users().messages().send(userId="me", body=body).execute())


def _poll_once(label_id: str, my_email: str) -> list[tuple]:
    res = svc.users().messages().list(
        userId="me", q=f"is:unread in:inbox -label:{PROCESSED_LABEL} -category:promotions -category:social",
        maxResults=10).execute()
    out = []
    for ref in res.get("messages", []):
        thread = svc.users().threads().get(userId="me", id=ref["threadId"], format="full").execute()
        msgs = thread["messages"]
        last = msgs[-1]
        frm = _header(last, "From")
        if my_email in frm.lower():
            continue
        if not store.has_history(PLATFORM, thread["id"]):
            for m in msgs[:-1]:
                mine = my_email in _header(m, "From").lower()
                store.add_message(PLATFORM, thread["id"], "Me" if mine else _header(m, "From"), _body(m["payload"])[:4000], mine)
        meta = {"to": frm, "subject": _header(last, "Subject"), "msgid": _header(last, "Message-ID"), "thread": thread["id"]}
        svc.users().messages().modify(userId="me", id=ref["id"], body={"addLabelIds": [label_id]}).execute()
        out.append((thread["id"], parseaddr(frm)[0] or frm, _body(last["payload"])[:6000], meta))
    return out


async def start() -> None:
    global svc
    svc = await asyncio.to_thread(_service)
    my_email = (await asyncio.to_thread(lambda: svc.users().getProfile(userId="me").execute()))["emailAddress"].lower()
    label_id = await asyncio.to_thread(_label_id)
    router.register_sender(PLATFORM, _send)
    log.info("Gmail connected as %s", my_email)
    while True:
        try:
            for thread_id, sender, text, meta in await asyncio.to_thread(_poll_once, label_id, my_email):
                extra = f"Subject: {meta['subject']}\nThis is an email: write a proper email reply body."
                await router.handle_incoming(PLATFORM, thread_id, sender, text, json.dumps(meta), extra)
                if not presence.is_busy():  # mirror the draft into Gmail itself
                    d = store.pending_drafts()
                    if d and d[-1]["chat_id"] == thread_id:
                        body = {"message": _raw_reply(meta, d[-1]["draft"])}
                        await asyncio.to_thread(lambda: svc.users().drafts().create(userId="me", body=body).execute())
        except Exception:
            log.exception("Gmail poll failed")
        await asyncio.sleep(config.GMAIL_POLL_SECONDS)
