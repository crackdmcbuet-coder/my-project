"""Settings read from environment variables (see .env.example)."""

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NOT_FOUND_MESSAGE = "এই স্বপ্নের ব্যাখ্যা আমাদের বইয়ে পাওয়া যায়নি।"
UNAVAILABLE_MESSAGE = "এই মুহূর্তে সেবাটি চালু করা যাচ্ছে না। একটু পরে আবার চেষ্টা করুন।"
DISCLAIMER = "বইয়ে যা লেখা আছে হুবহু তা-ই দেখানো হয়েছে। বিস্তারিত জানতে আমাদের সাথে যোগাযোগ করুন।"


@dataclass(frozen=True)
class Settings:
    model: str
    dreams_path: Path
    shortlist_size: int
    min_score: float
    max_input_chars: int
    rate_limit_calls: int
    rate_limit_window_s: int
    trust_forwarded_for: bool
    allowed_origins: list[str]


def _default_dreams_path() -> Path:
    real = ROOT / "data" / "dreams.json"
    return real if real.exists() else ROOT / "data" / "dreams.sample.json"


def load_settings() -> Settings:
    env = os.environ.get
    return Settings(
        model=env("ANTHROPIC_MODEL", "claude-opus-5-5"),
        dreams_path=Path(env("DREAMS_PATH") or _default_dreams_path()),
        shortlist_size=int(env("SHORTLIST_SIZE", "10")),
        min_score=float(env("MIN_SCORE", "0.1")),
        max_input_chars=int(env("MAX_INPUT_CHARS", "1000")),
        rate_limit_calls=int(env("RATE_LIMIT_CALLS", "20")),
        rate_limit_window_s=int(env("RATE_LIMIT_WINDOW_S", "600")),
        trust_forwarded_for=env("TRUST_FORWARDED_FOR", "").lower() in {"1", "true", "yes"},
        allowed_origins=[o.strip() for o in env("ALLOWED_ORIGINS", "").split(",") if o.strip()],
    )
