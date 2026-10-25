import asyncio
import logging
import os

from . import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("main")


async def _forever(name, start):
    """Keep each channel alive 24/7: restart on crash."""
    while True:
        try:
            await start()
        except Exception:
            log.exception("%s crashed, restarting in 15s", name)
        await asyncio.sleep(15)


async def main() -> None:
    os.makedirs("data", exist_ok=True)
    tasks = []
    if config.TG_API_ID:
        from .channels import telegram
        tasks.append(_forever("telegram", telegram.start))
    if config.GMAIL_ENABLED and os.path.exists(config.GMAIL_CREDENTIALS):
        from .channels import gmail
        tasks.append(_forever("gmail", gmail.start))
    if config.WHATSAPP_TOKEN or config.MESSENGER_PAGE_TOKEN:
        from .channels import meta
        tasks.append(_forever("meta", meta.start))
    if not tasks:
        raise SystemExit("No channel configured. Fill in .env (see .env.example).")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
