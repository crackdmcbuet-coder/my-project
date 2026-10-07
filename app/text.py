"""Bengali-aware text helpers shared by retrieval and ingestion."""

import unicodedata

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"))

# Words that carry no dream-specific meaning. Applied to queries and book titles alike.
STOPWORDS = frozenset(
    "আমি আমার আমাকে আমরা একটি একটা এক দেখলাম দেখছি দেখি স্বপ্নে স্বপ্ন যেন মনে "
    "হচ্ছে করছি করলাম ছিল হলো এবং ও এ যে এই সেই".split()
)


def clean(text: str) -> str:
    """NFC-normalise, drop zero-width characters and collapse whitespace."""
    text = unicodedata.normalize("NFC", text).translate(_ZERO_WIDTH)
    return " ".join(text.split())


def normalize(text: str) -> str:
    """`clean` plus punctuation removed.

    Letters (L), combining marks (M: Bengali vowel signs and the virama) and
    digits (N) are kept. `str.isalnum` / `\\w` would wrongly drop the marks.
    """
    kept = "".join(
        ch if unicodedata.category(ch)[0] in "LMN" else " "
        for ch in unicodedata.normalize("NFC", text).translate(_ZERO_WIDTH)
    )
    return " ".join(kept.lower().split())


def tokens(text: str) -> list[str]:
    return [t for t in normalize(text).split() if t not in STOPWORDS]


def char_ngrams(token: str, n: int = 3) -> list[str]:
    """Boundary-padded character n-grams, so 'সাপ' and 'সাপে' share most grams."""
    padded = f"^{token}$"
    if len(padded) <= n:
        return [padded]
    return [padded[i : i + n] for i in range(len(padded) - n + 1)]


def ngram_bag(text: str) -> list[str]:
    return [g for t in tokens(text) for g in char_ngrams(t)]
