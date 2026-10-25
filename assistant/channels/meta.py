"""WhatsApp (Cloud API) + Facebook Messenger (Page) via one Meta webhook server."""
import logging

import httpx
from fastapi import FastAPI, Request, Response

from .. import config, router

log = logging.getLogger("meta")
app = FastAPI()
GRAPH = "https://graph.facebook.com/v21.0"


@app.get("/webhook")
async def verify(request: Request):
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and p.get("hub.verify_token") == config.META_VERIFY_TOKEN:
        return Response(p.get("hub.challenge", ""))
    return Response(status_code=403)


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    obj = data.get("object")
    for entry in data.get("entry", []):
        if obj == "whatsapp_business_account":
            for change in entry.get("changes", []):
                value = change.get("value", {})
                names = {c["wa_id"]: c["profile"]["name"] for c in value.get("contacts", [])}
                for m in value.get("messages", []):
                    if m.get("type") == "text":
                        await router.handle_incoming("whatsapp", m["from"], names.get(m["from"], m["from"]), m["text"]["body"])
        elif obj == "page":
            for ev in entry.get("messaging", []):
                msg = ev.get("message", {})
                if msg.get("text") and not msg.get("is_echo"):
                    psid = ev["sender"]["id"]
                    await router.handle_incoming("messenger", psid, f"Messenger user {psid}", msg["text"])
    return {"ok": True}


async def _send_whatsapp(chat_id: str, text: str, meta: str) -> None:
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{GRAPH}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages",
                         headers={"Authorization": f"Bearer {config.WHATSAPP_TOKEN}"},
                         json={"messaging_product": "whatsapp", "to": chat_id, "type": "text", "text": {"body": text}})
        r.raise_for_status()


async def _send_messenger(chat_id: str, text: str, meta: str) -> None:
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{GRAPH}/me/messages", params={"access_token": config.MESSENGER_PAGE_TOKEN},
                         json={"recipient": {"id": chat_id}, "messaging_type": "RESPONSE", "message": {"text": text}})
        r.raise_for_status()


async def start() -> None:
    import uvicorn

    router.register_sender("whatsapp", _send_whatsapp)
    router.register_sender("messenger", _send_messenger)
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=config.WEBHOOK_PORT, log_level="warning"))
    log.info("Meta webhook on :%s/webhook", config.WEBHOOK_PORT)
    await server.serve()
