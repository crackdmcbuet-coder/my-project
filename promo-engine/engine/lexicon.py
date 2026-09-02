"""Bilingual (Bengali + English) cue lexicons.

These do NOT decide truth -- they only surface candidate moments for a human to
confirm. Nothing here invents content: every match points at a real spoken line.
Categories mirror the content-bank taxonomy.
"""
from __future__ import annotations

import re
import unicodedata

# ------------------------------------------------------------------ taxonomy

CATEGORIES = [
    "HOOK",
    "PROBLEM",
    "EMOTIONAL",
    "AUTHORITY",
    "INSIGHT",
    "TEACHING",
    "TRANSFORMATION",
    "OBJECTION",
    "CTA",
]

# Cue phrases per category. Bengali first, then English.
CUES: dict[str, list[str]] = {
    "PROBLEM": [
        "সমস্যা", "ভুল", "ভুলটা", "কষ্ট", "পারি না", "পারে না", "পারছি না", "আটকে",
        "হয় না", "হচ্ছে না", "ব্যর্থ", "কঠিন", "ঝামেলা", "অভাব", "ঘাটতি", "দুর্বল",
        "বাধা", "হতাশ", "সময় নষ্ট", "টাকা নষ্ট", "বেশিরভাগ মানুষ", "অনেকেই",
        "problem", "mistake", "struggle", "stuck", "fail", "failing", "hard",
        "difficult", "cannot", "can't", "waste", "confused", "most people",
    ],
    "EMOTIONAL": [
        "স্বপ্ন", "ভয়", "লজ্জা", "আফসোস", "অনুশোচনা", "কান্না", "ভালোবাসা", "গর্ব",
        "হতাশা", "একা", "পরিবার", "মা", "বাবা", "সন্তান", "জীবন বদলে", "আল্লাহ",
        "ইনশাআল্লাহ", "আলহামদুলিল্লাহ", "বিশ্বাস", "সাহস", "আশা",
        "dream", "fear", "afraid", "regret", "shame", "alone", "family",
        "believe", "courage", "hope", "changed my life",
    ],
    "AUTHORITY": [
        "বছর ধরে", "অভিজ্ঞতা", "আমি দেখেছি", "আমরা দেখেছি", "গবেষণা", "প্রমাণ",
        "কাজ করেছি", "শিখিয়েছি", "হাজার", "শত", "স্টুডেন্ট", "শিক্ষার্থী",
        "প্রফেশনাল", "ইন্ডাস্ট্রি", "সার্টিফাইড", "রেফারেন্স", "কিতাব", "দলিল",
        "years", "experience", "i have seen", "we have seen", "research",
        "proven", "worked with", "taught", "students", "industry", "certified",
        "reference", "evidence",
    ],
    "INSIGHT": [
        "আসলে", "মূল কারণ", "রহস্য", "গোপন", "কেউ বলে না", "কেউ বলেনি", "সত্যি হলো",
        "সত্য হলো", "মজার ব্যাপার", "লক্ষ্য করুন", "খেয়াল করুন", "বুঝতে হবে",
        "পার্থক্য", "কারণ হলো", "এখানেই", "চাবিকাঠি",
        "actually", "the real reason", "secret", "nobody tells you", "truth is",
        "here's the thing", "notice", "the difference", "the key",
    ],
    "TEACHING": [
        "প্রথম ধাপ", "দ্বিতীয়", "তৃতীয়", "উদাহরণ", "যেমন", "নিয়ম", "পদ্ধতি",
        "কৌশল", "টেকনিক", "শিখব", "শিখবেন", "দেখাচ্ছি", "দেখাবো", "করতে হবে",
        "step", "first", "second", "third", "example", "method", "technique",
        "rule", "formula", "framework", "let me show", "you will learn",
    ],
    "TRANSFORMATION": [
        "বদলে যাবে", "পারবেন", "পারবে", "সক্ষম", "উন্নতি", "ফলাফল", "সফল",
        "আত্মবিশ্বাস", "দক্ষ", "মাস্টার", "নিজেই", "স্বাধীন", "এরপর থেকে",
        "will change", "you will be able", "result", "success", "confident",
        "master", "on your own", "from now on", "transform",
    ],
    "OBJECTION": [
        "অনেকে বলে", "প্রশ্ন করে", "মনে হতে পারে", "ভাবতে পারেন", "কিন্তু যদি",
        "সময় নেই", "টাকা নেই", "বয়স", "দেরি হয়ে গেছে", "কঠিন মনে হয়",
        "you might think", "people ask", "what if", "no time", "too late",
        "too old", "seems hard", "but i don't",
    ],
    "CTA": [
        "ভর্তি", "যোগাযোগ", "রেজিস্ট্রেশন", "কোর্সে", "লিংক", "ইনবক্স",
        "বিস্তারিত", "জয়েন", "শুরু করুন", "নিচে",
        "enroll", "join", "register", "link", "inbox", "details", "sign up",
        "get started", "below",
    ],
}

# Openers that make terrible hooks (STEP 7). Matched at the START of a segment.
GREETING_OPENERS = [
    "আসসালামু আলাইকুম", "আসসালামুয়ালাইকুম", "সালাম", "ওয়ালাইকুম",
    "স্বাগতম", "আমার নাম", "আজকে আমরা", "আজ আমরা", "আজকের ক্লাসে",
    "আজকের ভিডিওতে", "শুরু করা যাক", "কেমন আছেন",
    "assalamu alaikum", "salam", "welcome", "hello everyone", "hi everyone",
    "my name is", "today we are going to", "today we will", "in this video",
    "let's get started", "how are you",
]

# Verbal filler. High density = low clarity.
FILLERS = [
    "আচ্ছা", "মানে", "তো", "একটু", "ইয়ে", "এই যে", "কি বলব", "বুঝলেন",
    "um", "uh", "erm", "like", "you know", "i mean", "sort of", "kind of",
]

# Curiosity / question markers.
QUESTION_CUES = [
    "কেন", "কীভাবে", "কিভাবে", "কি করে", "কোনটা", "কোন", "কখন", "কে",
    "why", "how", "what if", "which", "when", "who",
]

# Contrast markers -- a thought is turning, which is a natural cut point.
CONTRAST_CUES = [
    "কিন্তু", "তবে", "যদিও", "অথচ", "আসলে", "বরং", "উল্টো",
    "but", "however", "although", "actually", "instead", "yet",
]

# Second person -- relatability.
SECOND_PERSON = [
    "আপনি", "আপনার", "আপনাকে", "আপনারা", "তুমি", "তোমার", "তোমাকে",
    "you", "your", "yours",
]

# Words never emphasised on screen even if they score high (function words).
STOPWORDS_EMPHASIS = {
    "এই", "সেই", "একটা", "একটি", "এবং", "বা", "যে", "তা", "না", "ও", "আর",
    "the", "a", "an", "and", "or", "of", "to", "is", "are", "in", "on", "it",
    "that", "this", "for", "but", "so", "we", "i",
}

BENGALI_DIGITS = "০১২৩৪৫৬৭৮৯"

_WORD_RE = re.compile(r"[^\s।॥.,!?;:\"'()\[\]—–-]+", re.UNICODE)


def normalize(text: str) -> str:
    """NFC-normalise and lowercase. Bengali is unaffected by lowercasing; English is not."""
    return unicodedata.normalize("NFC", text or "").lower().strip()


def words(text: str) -> list[str]:
    """Tokenise, keeping Bengali danda and Latin punctuation out of the tokens."""
    return _WORD_RE.findall(normalize(text))


def count_cues(text: str, cues: list[str]) -> int:
    """Count cue occurrences.

    Multi-word cues match as substrings. Single-word cues match against tokens:
    a stem of 3+ chars may prefix-match (Bengali is agglutinative, so 'ভুল' must
    also catch 'ভুলটা' / 'ভুলগুলো'), while 1-2 char cues require an exact token so
    that 'মা' does not fire inside 'মানুষ'.
    """
    t = normalize(text)
    toks = words(t)
    n = 0
    for raw in cues:
        c = normalize(raw)
        if not c:
            continue
        if " " in c:
            n += t.count(c)
        elif len(c) >= 3:
            n += sum(1 for w in toks if w == c or w.startswith(c))
        else:
            n += sum(1 for w in toks if w == c)
    return n


def has_digit(text: str) -> bool:
    return any(ch.isdigit() or ch in BENGALI_DIGITS for ch in text or "")


def starts_with_greeting(text: str) -> bool:
    t = normalize(text)
    return any(t.startswith(normalize(g)) for g in GREETING_OPENERS)


def is_question(text: str) -> bool:
    t = normalize(text)
    if "?" in t:
        return True
    head = " ".join(words(t)[:6])
    return any(normalize(q) in head for q in QUESTION_CUES)


def category_hits(text: str) -> dict[str, int]:
    return {cat: count_cues(text, cues) for cat, cues in CUES.items()}


def script_of(text: str) -> str:
    """'bn' if the segment is predominantly Bengali script, else 'en'."""
    bn = sum(1 for ch in text or "" if "ঀ" <= ch <= "৿")
    la = sum(1 for ch in text or "" if "a" <= ch.lower() <= "z")
    return "bn" if bn >= la else "en"
