"""Decides whether the owner is busy: manual override (/busy, /free, /auto) or BUSY_HOURS schedule."""
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config, store


def set_mode(mode: str) -> None:
    store.set_state("mode", mode)  # "busy" | "free" | "auto"


def mode() -> str:
    return store.get_state("mode", "auto")


def is_busy() -> bool:
    m = mode()
    if m != "auto":
        return m == "busy"
    if not config.BUSY_HOURS:
        return False
    start, end = config.BUSY_HOURS.split("-")
    now = datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%H:%M")
    return start <= now < end if start <= end else (now >= start or now < end)
