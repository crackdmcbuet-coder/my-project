"""STEP 10/11/22 -- phrase-chunked captions with keyword emphasis, as ASS.

ASS (not SRT) because the brief needs per-word emphasis, scale animation and
precise safe-area placement -- none of which SRT can express.

Every caption is built from words the speaker actually said, at the times they
said them. The engine never writes a caption that is not in the transcript.
"""
from __future__ import annotations

from pathlib import Path

from . import lexicon as lx
from .config import Config
from .util import write_text


def _ass_time(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _esc(text: str) -> str:
    return (text.replace("\\", "\\\\").replace("{", "(").replace("}", ")")
                .replace("\n", "\\N"))


def chunk_words(words: list[dict], *, max_words: int, max_chars: int,
                max_dur: float) -> list[dict]:
    """Break a line into readable caption chunks.

    Breaks are chosen at punctuation first, then at the word/char/duration ceiling.
    This is what stops captions turning into a wall of text (STEP 10).
    """
    chunks: list[dict] = []
    cur: list[dict] = []

    def flush() -> None:
        nonlocal cur
        if cur:
            chunks.append({
                "start": float(cur[0]["start"]),
                "end": float(cur[-1]["end"]),
                "words": cur,
                "text": " ".join(w["w"].strip() for w in cur).strip(),
            })
            cur = []

    for w in words:
        cur.append(w)
        text = " ".join(x["w"].strip() for x in cur)
        dur = float(cur[-1]["end"]) - float(cur[0]["start"])
        ends_punct = w["w"].rstrip()[-1:] in "।॥.,!?;:"
        if (ends_punct or len(cur) >= max_words or len(text) >= max_chars
                or dur >= max_dur):
            flush()
    flush()
    return chunks


def _style_block(cfg: Config) -> str:
    w, h = cfg.get("output.width"), cfg.get("output.height")
    sub = cfg.data["subtitles"]
    size = int(h * float(sub["size_pct"]))
    # Captions sit just above the platform UI band, inside the safe area.
    margin_v = int(h * cfg.get("safe_area.bottom_pct")) + int(h * 0.02)
    margin_h = int(w * cfg.get("safe_area.side_pct"))
    font = sub.get("font") or sub.get("font_fallback") or "Sans"
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},{size},{sub['primary']},{sub['primary']},&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,{sub['outline']},{sub['shadow']},2,{margin_h},{margin_h},{margin_v},1
Style: Card,{font},{int(size * 1.55)},{sub['primary']},{sub['primary']},&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,{sub['outline'] + 2},{sub['shadow']},5,{margin_h},{margin_h},0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _render_chunk(chunk: dict, emphasis: set[str], cfg: Config) -> str:
    """One caption line, with the emphasised word coloured and scaled."""
    sub = cfg.data["subtitles"]
    parts = []
    for w in chunk["words"]:
        tok = w["w"].strip()
        norm = lx.normalize(tok).strip("।॥.,!?;:\"'()[]")
        if norm and norm in emphasis:
            parts.append(f"{{\\c{sub['emphasis']}\\fscx112\\fscy112}}{_esc(tok)}"
                         f"{{\\c{sub['primary']}\\fscx100\\fscy100}}")
        else:
            parts.append(_esc(tok))
    body = " ".join(parts)
    # Short pop-in: scale up from 92% so a caption lands with its word.
    intro = "{\\fscx92\\fscy92\\fad(60,60)\\t(0,110,\\fscx100\\fscy100)}"
    return (f"Dialogue: 0,{_ass_time(chunk['start'])},{_ass_time(chunk['end'])},"
            f"Caption,,0,0,0,,{intro}{body}")


def build_ass(shots: list[dict], cfg: Config) -> str:
    """Captions for a whole timeline, in promo time."""
    sub = cfg.data["subtitles"]
    lines = [_style_block(cfg)]
    for s in shots:
        words = s.get("words") or []
        if not words:
            continue
        offset = s["t_in"] - s["src_in"]          # source time -> promo time
        emphasis = {lx.normalize(s.get("emphasis") or "")} - {""}
        rebased = [{"w": w["w"], "start": float(w["start"]) + offset,
                    "end": float(w["end"]) + offset} for w in words]
        for ch in chunk_words(rebased, max_words=int(sub["max_words"]),
                              max_chars=int(sub["max_chars"]),
                              max_dur=float(sub["max_dur"])):
            # Clamp to the shot so a caption never outlives its picture.
            ch["start"] = max(ch["start"], s["t_in"])
            ch["end"] = min(ch["end"], s["t_out"])
            if ch["end"] - ch["start"] < 0.18:
                continue
            if s["treatment"] == "TEXT_CARD":
                continue                          # the card *is* the text
            lines.append(_render_chunk(ch, emphasis, cfg))

        if s["treatment"] == "TEXT_CARD":
            card = " ".join(w["w"].strip() for w in words).strip()
            if card:
                lines.append(
                    f"Dialogue: 1,{_ass_time(s['t_in'])},{_ass_time(s['t_out'])},"
                    f"Card,,0,0,0,,{{\\fad(90,90)\\an5}}{_esc(card)}")
    return "\n".join(lines) + "\n"


def write_ass(shots: list[dict], cfg: Config, path: str | Path) -> Path:
    return write_text(Path(path), build_ass(shots, cfg))


def build_srt(shots: list[dict], cfg: Config) -> str:
    """Plain SRT companion for platforms that want an upload-able caption file."""
    sub = cfg.data["subtitles"]
    out, n = [], 0
    for s in shots:
        words = s.get("words") or []
        if not words:
            continue
        offset = s["t_in"] - s["src_in"]
        rebased = [{"w": w["w"], "start": float(w["start"]) + offset,
                    "end": float(w["end"]) + offset} for w in words]
        for ch in chunk_words(rebased, max_words=int(sub["max_words"]),
                              max_chars=int(sub["max_chars"]),
                              max_dur=float(sub["max_dur"])):
            st = max(ch["start"], s["t_in"])
            en = min(ch["end"], s["t_out"])
            if en - st < 0.18:
                continue
            n += 1
            out.append(f"{n}\n{_srt_time(st)} --> {_srt_time(en)}\n{ch['text']}\n")
    return "\n".join(out)


def _srt_time(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
