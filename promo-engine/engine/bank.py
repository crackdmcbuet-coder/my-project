"""The CONTENT BANK -- scan the course once, reuse it for every future reel.

Turns transcripts + the source library into a queryable database of scored,
categorised clips. `promo bank query --category HOOK` then answers "what are my
20 strongest hooks?" without ever re-scanning the course again.
"""
from __future__ import annotations

from pathlib import Path

from . import lexicon as lx
from . import scoring
from .config import Config
from .transcribe import load_all
from .util import read_json, write_json, tc

BANK_VERSION = 2


def _source_index(cfg: Config) -> dict[str, dict]:
    lib = read_json(cfg.dir_index / "library.json", default={"files": []})
    idx = {}
    for f in lib.get("files", []):
        idx[str(Path(f["path"]).resolve())] = f
    return idx


def _merge_short(segments: list[dict], *, min_dur: float, max_dur: float) -> list[dict]:
    """Whisper often splits one thought across two short segments. Merge adjacent
    fragments when they are close in time and the first does not end a sentence."""
    out: list[dict] = []
    for seg in segments:
        if out:
            prev = out[-1]
            gap = float(seg["start"]) - float(prev["end"])
            prev_dur = float(prev["end"]) - float(prev["start"])
            ends_sentence = (prev.get("text", "").rstrip()[-1:] in "।?!.॥")
            if (prev_dur < min_dur and gap < 0.6 and not ends_sentence
                    and (float(seg["end"]) - float(prev["start"])) <= max_dur):
                prev["end"] = seg["end"]
                prev["text"] = (prev.get("text", "") + " " + seg.get("text", "")).strip()
                prev["words"] = (prev.get("words") or []) + (seg.get("words") or [])
                prev["avg_logprob"] = min(prev.get("avg_logprob", 0.0),
                                          seg.get("avg_logprob", 0.0))
                continue
        out.append(dict(seg))
    return out


def build(cfg: Config) -> dict:
    """Build (or rebuild) the content bank from cached transcripts."""
    cfg.ensure_dirs()
    sources = _source_index(cfg)
    transcripts = load_all(cfg)
    if not transcripts:
        raise RuntimeError(
            "no transcripts found -- run `promo transcribe` first "
            f"(looked in {cfg.dir_transcripts})"
        )

    clips: list[dict] = []
    rejected: list[dict] = []
    review: list[dict] = []

    for tr in transcripts:
        spath = str(Path(tr["path"]).resolve())
        src = sources.get(spath, {})
        segs = _merge_short(tr.get("segments", []),
                            min_dur=scoring.MIN_CLIP, max_dur=scoring.MAX_CLIP)

        for seg in segs:
            feats = scoring.segment_features(seg)
            sc = scoring.score_segment(seg, src, feats)
            reason = scoring.rejection_reason(seg, feats, sc)
            base = {
                "source": spath,
                "source_name": tr.get("name") or Path(spath).name,
                "start": round(float(seg["start"]), 3),
                "end": round(float(seg["end"]), 3),
                "duration": round(feats["duration"], 3),
                "tc": f"{tc(seg['start'], ms=False)}-{tc(seg['end'], ms=False)}",
                "text": seg.get("text", "").strip(),
                "script": feats["script"],
            }
            if reason:
                rejected.append({**base, "reason": reason, "composite": sc["composite"]})
                continue

            cats = scoring.categorize(seg, sc, feats)
            if not cats:
                rejected.append({**base, "reason": "no category matched",
                                 "composite": sc["composite"]})
                continue

            clip = {
                **base,
                "id": f"{Path(spath).stem}@{seg['start']:.2f}",
                "categories": cats,
                "scores": sc,
                "words": seg.get("words") or [],
                "n_words": feats["n_words"],
                "wps": round(feats["wps"], 2),
                "needs_review": bool(seg.get("needs_review")),
                "keywords": top_keywords(seg),
            }
            clips.append(clip)
            if clip["needs_review"]:
                review.append({"id": clip["id"], "tc": clip["tc"],
                               "source_name": clip["source_name"], "text": clip["text"]})

    clips.sort(key=lambda c: -c["scores"]["composite"])

    by_cat: dict[str, list[str]] = {c: [] for c in lx.CATEGORIES}
    for c in clips:
        for cat in c["categories"]:
            by_cat[cat].append(c["id"])

    bank = {
        "version": BANK_VERSION,
        "project": cfg.get("project_name"),
        "source_count": len(transcripts),
        "clip_count": len(clips),
        "rejected_count": len(rejected),
        "by_category": {k: v for k, v in by_cat.items()},
        "category_counts": {k: len(v) for k, v in by_cat.items()},
        "clips": clips,
        "needs_review": review,
    }
    write_json(cfg.dir_bank / "content_bank.json", bank)
    write_json(cfg.dir_bank / "rejected.json",
               {"count": len(rejected), "clips": rejected})
    return bank


def load(cfg: Config) -> dict:
    p = cfg.dir_bank / "content_bank.json"
    if not p.exists():
        raise RuntimeError(f"content bank not built yet -- run `promo bank build` ({p})")
    return read_json(p)


def query(bank: dict, *, category: str | None = None, top: int = 20,
          min_dur: float = 0.0, max_dur: float = 999.0,
          source: str | None = None, sort_by: str = "composite",
          exclude_ids: set[str] | None = None) -> list[dict]:
    """The reuse workhorse: pull the strongest clips of a kind, any time."""
    exclude_ids = exclude_ids or set()
    out = []
    for c in bank.get("clips", []):
        if c["id"] in exclude_ids:
            continue
        if category and category.upper() not in c["categories"]:
            continue
        if not (min_dur <= c["duration"] <= max_dur):
            continue
        if source and source.lower() not in c["source_name"].lower():
            continue
        out.append(c)
    key = (lambda c: -c["scores"].get(sort_by, c["scores"]["composite"]))
    return sorted(out, key=key)[:top]


def top_keywords(seg: dict, k: int = 3) -> list[str]:
    """Words worth emphasising on screen (STEP 10). Content words only, and always
    words actually spoken -- the engine never puts an unspoken word on screen."""
    ws = seg.get("words") or []
    if not ws:
        toks = [w for w in lx.words(seg.get("text", ""))
                if w not in lx.STOPWORDS_EMPHASIS and len(w) > 2]
        return toks[:k]

    scored = []
    for i, w in enumerate(ws):
        tok = lx.normalize(w.get("w", "")).strip("।॥.,!?;:\"'()[]")
        if not tok or tok in lx.STOPWORDS_EMPHASIS or len(tok) < 3:
            continue
        dur = max(0.01, float(w.get("end", 0)) - float(w.get("start", 0)))
        stress = dur / max(0.05, len(tok) / 8.0)      # drawn-out word = emphasised word
        cue_bonus = 0.0
        for cues in (lx.CUES["PROBLEM"], lx.CUES["INSIGHT"], lx.CUES["TRANSFORMATION"]):
            if lx.count_cues(tok, cues):
                cue_bonus += 0.6
        scored.append((stress + cue_bonus, i, tok))
    scored.sort(key=lambda t: -t[0])
    seen, out = set(), []
    for _, _, tok in scored:
        if tok in seen:
            continue
        seen.add(tok)
        out.append(tok)
        if len(out) >= k:
            break
    return out


def summary_lines(bank: dict) -> list[str]:
    lines = [
        f"CONTENT BANK -- {bank.get('project')}",
        f"  sources indexed : {bank.get('source_count')}",
        f"  usable clips    : {bank.get('clip_count')}",
        f"  rejected        : {bank.get('rejected_count')}",
        "",
        "  by category:",
    ]
    for cat, n in bank.get("category_counts", {}).items():
        lines.append(f"    {cat:<16} {n:>4}")
    if bank.get("needs_review"):
        lines += ["", f"  !! {len(bank['needs_review'])} clips have low-confidence "
                      f"transcription -- run `promo review` before using them on screen"]
    return lines
