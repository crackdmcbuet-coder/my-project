# -*- coding: utf-8 -*-
import json, re, unicodedata
import content as C

BN_DIG = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
AR_DIG = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
def bn(n): return str(n).translate(BN_DIG)
def ar(n): return str(n).translate(AR_DIG)

HARAKAT = "ًٌٍَُِْ"
SHADDA = "ّ"
SUKUN = "ْ"; JAZM = "ۡ"
FATHA, DAMMA, KASRA = "َ", "ُ", "ِ"
AR_LETTER = "[ء-غف-يٱ]"

def _norm(s):
    return re.sub("([" + HARAKAT + "])" + SHADDA, SHADDA + r"\1", s)

WORD_FIX = [("هَذَا", "هٰذَا"), ("هَذِهِ", "هٰذِهِ"), ("ذَلِكَ", "ذٰلِكَ"),
            ("الرَّحْمَنِ", "الرَّحْمٰنِ"), ("السَّمَاوَاتِ", "السَّمٰوٰتِ"),
            ("الْعَالَمِينَ", "الْعٰلَمِيْنَ"), ("مَلَائِكَتَكَ", "مَلٰٓئِكَتَكَ"),
            ("الْخَبَائِثِ", "الْخَبٰٓئِثِ"), ("التَّوْرَاةِ", "التَّوْرٰىةِ"), ("إِلَهَ", "اِلٰهَ")]
NEXT_NOT_WASL = r"(?=\s+[^ا\s])"          # পরের শব্দ হামযাতুল ওয়াসল দিয়ে শুরু নয়
WORD_END_THEN_WASL = r"(?=\s+ا)"

def indopak(s):
    """প্রচলিত হরকতযুক্ত আরবিকে ইন্দো-পাক রীতিতে রূপান্তর (নিরাপদ নিয়মগুলো মাত্র)।"""
    s = _norm(s)
    for a, b in WORD_FIX:
        s = s.replace(_norm(a), _norm(b))
    # আল্লাহ: (ا/لِ/بِا)للَّه -> للّٰه
    s = re.sub("ل(" + KASRA + "?)ل" + SHADDA + FATHA + "ه", "ل\\1ل" + SHADDA + "\u0670ه", s)
    END = r"(?=[\s،.:(]|$)"
    # সর্বনাম হা দীর্ঘ: শব্দের শেষে হ্রস্ব হরকতের পর هُ/هِ (পরের শব্দ ওয়াসলি না হলে)
    LONG = r"(?=\s*[،.:]|\s*$|\s+[^ا\s])"
    s = re.sub("(?<=[" + FATHA + DAMMA + KASRA + "])ه" + DAMMA + LONG, "ه\u0657", s)
    s = re.sub("(?<=[" + FATHA + DAMMA + KASRA + "])ه" + KASRA + LONG, "ه\u0656", s)
    # শেষের ইয়া/ওয়াও মদ্দ: فِي -> فِىۡ (ওয়াসলের আগে জযম ছাড়া)
    s = re.sub(KASRA + "ي" + WORD_END_THEN_WASL, KASRA + "ى", s)
    s = re.sub(KASRA + "ي" + END, KASRA + "ى" + JAZM, s)
    s = re.sub(DAMMA + "و" + LONG.replace("[^ا\\s]", "[^ا\\s]"), DAMMA + "و" + JAZM, s)
    # আলিফ মাকসূরা: عَلَى -> عَلٰى
    s = re.sub(FATHA + "ى" + r"(?=[،.:(]|$|\s+[^ا\s])", "\u0670ى", s)
    # শব্দের শুরুতে (বা এক-অক্ষরের উপসর্গ / আল-এর পরে) হামযাযুক্ত আলিফ -> সাধারণ আলিফ
    s = re.sub(r"(^|[\s،(]|[وفبلك][" + FATHA + KASRA + r"]|ال" + SUKUN + r")[أإ]", r"\1ا", s)
    # মদ্দের ওয়াও/ইয়া (শব্দের মাঝে) -> জযম
    s = re.sub("(" + DAMMA + "و)(?=" + AR_LETTER + ")", r"\1" + JAZM, s)
    s = re.sub("(" + KASRA + "ي)(?=" + AR_LETTER + ")", r"\1" + JAZM, s)
    s = s.replace(SUKUN, JAZM)
    return s

SURAH_BN = {1: "সূরা আল-ফাতিহা", 2: "সূরা আল-বাকারা", 3: "সূরা আলে ইমরান", 32: "সূরা আস-সাজদা",
            43: "সূরা আয-যুখরুফ", 67: "সূরা আল-মুলক", 109: "সূরা আল-কাফিরূন",
            112: "সূরা আল-ইখলাস", 113: "সূরা আল-ফালাক", 114: "সূরা আন-নাস"}

Q = json.load(open("quran_raw.json"))
def clean_ar(t):
    t = t.replace("‏", "").replace("​", " ")
    return re.sub(r"\s+", " ", t).strip()
def clean_bn(t):
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"\s*\[\s*[০-৯0-9]+\s*\]", "", t)
    t = re.sub(r"\s+([,।;:?!])", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()
def verses(s, a1, a2):
    ar_ = {v["key"]: v for v in Q[f"213:{s}"]}
    out = []
    for n in range(a1, a2 + 1):
        v = ar_[f"{s}:{n}"]
        out.append({"n": n, "nar": ar(n), "nbn": bn(n), "ar": clean_ar(v["ar"]), "bn": clean_bn(v["bn"])})
    return out
BISMILLAH = clean_ar(Q["213:1"][0]["ar"]).rstrip("ۚ ").strip()

def make_item(d, no):
    it = {"t": "item", "no": bn(no), "title": d["title"], "when": d.get("when", ""), "count": d.get("count", ""),
          "grade": d.get("grade", "sahih"), "grade_label": C.GRADES[d.get("grade", "sahih")],
          "grade_note": d.get("grade_note", ""), "ref": d.get("ref", ""), "fadl": d.get("fadl", []),
          "note": d.get("note", ""), "bn": d.get("bn", ""), "bn_eve": d.get("bn_eve", ""),
          "text_only": d.get("text_only", False), "ar": [], "quran": []}
    if d.get("ar"):
        it["ar"].append({"label": "সকালে পড়বে:" if d.get("ar_eve") else "", "text": indopak(d["ar"])})
    if d.get("ar_eve"):
        it["ar"].append({"label": "সন্ধ্যায় পড়বে:", "text": indopak(d["ar_eve"])})
    for s, a1, a2 in d.get("quran", []):
        name = SURAH_BN[s] + (f", আয়াত {bn(a1)}" + (f"–{bn(a2)}" if a2 != a1 else "") if s in (2, 3) else "")
        it["quran"].append({"name": name, "bismillah": BISMILLAH if d.get("bismillah") else "", "verses": verses(s, a1, a2)})
    return it

def build():
    B = [{"t": "cover", "title": C.TITLE, "sub": C.SUBTITLE, "sub2": C.SUBTITLE2, "sub3": C.SUBTITLE3,
          "bismillah": BISMILLAH, "author": C.AUTHOR, "org": C.ORG}]
    toc = [("ভূমিকা", "intro"),
           ("অংশ ১: সকাল-সন্ধ্যার মাসনূন যিকির (সহীহ ও হাসান)", "p1"),
           ("অংশ ২: সকাল-সন্ধ্যার আরও কিছু যিকির (সনদে মতভেদপূর্ণ) ও সতর্কতা", "p2"),
           ("অংশ ৩: রাতের ও ঘুমের আগের সূরা", "p3"),
           ("অংশ ৪: ঘুমের আদব, দুআ ও রাতের আমল", "p4"),
           ("অংশ ৫: সারাদিনের আমলের তালিকা", "p5"),
           ("অংশ ৬: দৈনন্দিন জরুরি দুআ ও বিতর", "p6"),
           ("অংশ ৭: সাপ্তাহিক ও মাসিক আমল, আমল-ট্র্যাকার", "p7"),
           ("তথ্যসূত্র ও কৃতজ্ঞতা", "src")]
    B.append({"t": "toc", "rows": toc})
    B.append({"t": "h1", "text": "ভূমিকা", "id": "intro"})
    for kind, val in C.INTRO:
        B.append({"t": {"h": "h2", "p": "p", "ul": "ul"}[kind], ("items" if kind == "ul" else "text"): val})
    B.append({"t": "h1", "text": toc[1][0], "id": "p1",
              "lead": "নিচের প্রতিটি যিকির সকাল ও সন্ধ্যা দুই সময়েই পড়বেন, যদি না আলাদা করে “শুধু সকাল” বা “শুধু সন্ধ্যা” বলা থাকে। যেসব দুআর সকাল ও সন্ধ্যার শব্দ আলাদা, সেখানে দুটিই দেওয়া আছে।"})
    for i, d in enumerate(C.MORNING_EVENING, 1): B.append(make_item(d, i))
    B.append({"t": "h1", "text": toc[2][0], "id": "p2",
              "lead": "এই যিকিরগুলো হিসনুল মুসলিমসহ নির্ভরযোগ্য সংকলনে আছে। তবে এগুলোর সনদ নিয়ে মুহাদ্দিসদের মধ্যে মতভেদ রয়েছে। যিকির হিসেবে পড়া যায়, কিন্তু উল্লিখিত ফযীলতকে অকাট্য মনে না করাই সতর্কতা।"})
    n0 = len(C.MORNING_EVENING)
    for i, d in enumerate(C.MIXED, n0 + 1): B.append(make_item(d, i))
    B.append({"t": "warn", "title": "সতর্কতা: সমাজে প্রসিদ্ধ, কিন্তু সনদ দুর্বল", "items": C.WEAK_POPULAR, "note": C.WEAK_NOTE})
    B.append({"t": "h1", "text": toc[3][0], "id": "p3",
              "lead": "এই সূরাগুলো এশার পর থেকে ঘুমানোর আগ পর্যন্ত যেকোনো সময় পড়া যায়। সূরা মুলক ও সাজদা মাগরিবের পরও পড়া যায়।"})
    for i, d in enumerate(C.NIGHT_SURAHS, 1): B.append(make_item(d, i))
    B.append({"t": "h1", "text": toc[4][0], "id": "p4"})
    B.append({"t": "h2", "text": "ঘুমের সুন্নাত আদব"})
    B.append({"t": "ul", "items": C.SLEEP_ADAB})
    B.append({"t": "h2", "text": "বিছানায় যাওয়ার সময়ের দুআ"})
    k = 0
    for d in C.SLEEP_DUAS: k += 1; B.append(make_item(d, k))
    B.append({"t": "h2", "text": "রাতে জাগা, পাশ ফেরা ও ঘুম থেকে ওঠা"})
    for d in C.NIGHT_WAKE: k += 1; B.append(make_item(d, k))
    B.append({"t": "h1", "text": toc[5][0], "id": "p5",
              "lead": "নিচে ফজরের আগ থেকে রাতে ঘুমানো পর্যন্ত একজন মুসলিমের দিনের মাসনূন আমলের একটি রুটিন দেওয়া হলো। ফরজ ও ওয়াজিব সবার আগে। বাকিগুলো সুন্নাত ও নফল, তাই সামর্থ্য অনুযায়ী ধীরে ধীরে অভ্যাস গড়ুন।"})
    B.append({"t": "routine", "head": ["সময়", "আমল", "দলিল ও ফযীলত"], "rows": C.DAY_ROUTINE})
    B.append({"t": "h2", "text": "সারাদিন চলতে-ফিরতে"})
    B.append({"t": "table2", "head": ["আমল", "ফযীলত ও দলিল"], "rows": C.ALL_DAY})
    B.append({"t": "h1", "text": toc[6][0], "id": "p6"})
    B.append({"t": "h2", "text": "দৈনন্দিন দুআ"})
    for i, d in enumerate(C.DAILY_DUAS, 1): B.append(make_item(d, i))
    B.append({"t": "h2", "text": "বিতর সালাত"})
    for i, d in enumerate(C.WITR, len(C.DAILY_DUAS) + 1): B.append(make_item(d, i))
    B.append({"t": "h1", "text": toc[7][0], "id": "p7"})
    B.append({"t": "h2", "text": "সাপ্তাহিক ও মাসিক আমল"})
    B.append({"t": "routine", "head": ["কখন", "আমল", "দলিল ও ফযীলত"], "rows": C.WEEKLY})
    B.append({"t": "h2", "text": "সাপ্তাহিক আমল-ট্র্যাকার (প্রিন্ট করে টিক দিন)"})
    B.append({"t": "tracker", "rows": C.TRACKER, "days": C.DAYS})
    B.append({"t": "h1", "text": toc[8][0], "id": "src"})
    B.append({"t": "ul", "items": C.SOURCES})
    B.append({"t": "note", "text": C.DISCLAIMER})
    return B

if __name__ == "__main__":
    B = build()
    json.dump(B, open("blocks.json", "w"), ensure_ascii=False, indent=1)
    for b in B:
        if b["t"] == "item":
            for a in b["ar"]: print(b["no"], a["text"][:400]); print()
