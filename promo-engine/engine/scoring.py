"""STEP 4 -- score candidate clips across the dimensions in the brief.

Every score is a *shortlist heuristic*, never a verdict. Each returned clip
carries the exact spoken text and its source timestamp so a human can confirm it
before it reaches the screen (RULE 1, RULE 14).
"""
from __future__ import annotations

from . import lexicon as lx

DIMENSIONS = [
    "hook_power", "curiosity", "emotional", "authority", "clarity",
    "specificity", "value", "relatability", "visual_quality",
    "audio_quality", "retention",
]

# Weights for the composite score. Retention and hook dominate for short-form.
WEIGHTS = {
    "hook_power": 1.4, "curiosity": 1.3, "emotional": 1.0, "authority": 1.0,
    "clarity": 1.2, "specificity": 0.9, "value": 1.2, "relatability": 0.9,
    "visual_quality": 0.6, "audio_quality": 1.1, "retention": 1.5,
}

IDEAL_WPS = 2.6          # comfortable spoken pace, words/second
MIN_CLIP = 1.2
MAX_CLIP = 9.0


def _sat(n: float, k: float = 2.0) -> float:
    """Saturating 0..1 curve -- three cue hits should not score 3x one hit."""
    return n / (n + k) if n > 0 else 0.0


def segment_features(seg: dict) -> dict:
    text = seg.get("text", "") or ""
    dur = max(0.01, float(seg.get("end", 0)) - float(seg.get("start", 0)))
    toks = lx.words(text)
    nwords = len(toks)
    wps = nwords / dur
    hits = lx.category_hits(text)
    filler = lx.count_cues(text, lx.FILLERS)
    return {
        "duration": dur,
        "n_words": nwords,
        "wps": wps,
        "hits": hits,
        "filler": filler,
        "filler_density": filler / max(1, nwords),
        "second_person": lx.count_cues(text, lx.SECOND_PERSON),
        "contrast": lx.count_cues(text, lx.CONTRAST_CUES),
        "is_question": lx.is_question(text),
        "has_digit": lx.has_digit(text),
        "greeting": lx.starts_with_greeting(text),
        "script": lx.script_of(text),
        "confidence": float(seg.get("avg_logprob", 0.0) or 0.0),
    }


def score_segment(seg: dict, source: dict, feats: dict | None = None) -> dict:
    """source = a library record from probe.inspect(); supplies A/V quality."""
    f = feats or segment_features(seg)
    h = f["hits"]

    clarity = 1.0
    clarity -= min(0.5, f["filler_density"] * 3.0)
    pace_err = abs(f["wps"] - IDEAL_WPS) / IDEAL_WPS
    clarity -= min(0.4, pace_err * 0.5)
    if f["n_words"] < 4:
        clarity -= 0.3
    if f["confidence"] < -0.8:
        clarity -= 0.2                                  # shaky transcription
    clarity = max(0.0, min(1.0, clarity))

    specificity = min(1.0, (0.4 if f["has_digit"] else 0.0)
                      + _sat(h["TEACHING"], 1.5) * 0.5
                      + (0.15 if f["n_words"] >= 8 else 0.0))

    curiosity = min(1.0, (0.35 if f["is_question"] else 0.0)
                    + _sat(h["INSIGHT"], 1.2) * 0.55
                    + _sat(f["contrast"], 1.5) * 0.25)

    emotional = min(1.0, _sat(h["EMOTIONAL"], 1.2) * 0.75
                    + _sat(h["PROBLEM"], 2.0) * 0.3)

    authority = min(1.0, _sat(h["AUTHORITY"], 1.2) * 0.85
                    + (0.2 if f["has_digit"] and h["AUTHORITY"] else 0.0))

    value = min(1.0, _sat(h["TEACHING"], 1.5) * 0.55
                + _sat(h["TRANSFORMATION"], 1.2) * 0.45
                + _sat(h["INSIGHT"], 2.0) * 0.2)

    relatability = min(1.0, _sat(f["second_person"], 1.5) * 0.6
                       + _sat(h["PROBLEM"], 2.0) * 0.4)

    aq = float(source.get("audio_quality", 0.5) or 0.0)
    vq = float(source.get("visual_quality", 0.5) or 0.0)

    # Hook power: must land in ~2s, so short + punchy + curious/painful wins.
    length_fit = 1.0 if 1.5 <= f["duration"] <= 4.5 else (0.55 if f["duration"] <= 6.5 else 0.2)
    hook = (curiosity * 0.34 + emotional * 0.2 + relatability * 0.16
            + clarity * 0.2 + specificity * 0.1) * length_fit
    if f["greeting"]:
        hook *= 0.05                                    # STEP 7: never open on a greeting
    if f["n_words"] < 3:
        hook *= 0.4
    hook = min(1.0, hook)

    # Retention: would a stranger keep watching through this line?
    retention = min(1.0, curiosity * 0.3 + value * 0.25 + emotional * 0.15
                    + clarity * 0.2 + relatability * 0.1)
    if f["filler_density"] > 0.25:
        retention *= 0.6

    scores = {
        "hook_power": hook, "curiosity": curiosity, "emotional": emotional,
        "authority": authority, "clarity": clarity, "specificity": specificity,
        "value": value, "relatability": relatability,
        "visual_quality": vq, "audio_quality": aq, "retention": retention,
    }
    total_w = sum(WEIGHTS.values())
    composite = sum(scores[k] * WEIGHTS[k] for k in scores) / total_w
    scores = {k: round(v, 3) for k, v in scores.items()}
    scores["composite"] = round(composite, 3)
    return scores


def categorize(seg: dict, scores: dict, feats: dict) -> list[str]:
    """Assign every category the segment genuinely supports. A line can be both a
    PROBLEM and an EMOTIONAL clip -- the bank is meant to be queried many ways."""
    h = feats["hits"]
    cats: list[str] = []
    if scores["hook_power"] >= 0.42:
        cats.append("HOOK")
    if h["PROBLEM"] >= 1 or (feats["second_person"] and scores["relatability"] >= 0.5):
        cats.append("PROBLEM")
    if h["EMOTIONAL"] >= 1 and scores["emotional"] >= 0.3:
        cats.append("EMOTIONAL")
    if h["AUTHORITY"] >= 1:
        cats.append("AUTHORITY")
    if scores["curiosity"] >= 0.45 or h["INSIGHT"] >= 1:
        cats.append("INSIGHT")
    if h["TEACHING"] >= 1 and scores["clarity"] >= 0.45:
        cats.append("TEACHING")
    if h["TRANSFORMATION"] >= 1:
        cats.append("TRANSFORMATION")
    if h["OBJECTION"] >= 1:
        cats.append("OBJECTION")
    if h["CTA"] >= 1:
        cats.append("CTA")
    return cats


def rejection_reason(seg: dict, feats: dict, scores: dict) -> str | None:
    """Why a segment is unusable. Surfaced so nothing is silently dropped."""
    if feats["duration"] < MIN_CLIP:
        return "too short"
    if feats["duration"] > MAX_CLIP:
        return "too long (needs a sub-cut)"
    if feats["n_words"] < 3:
        return "not enough speech"
    if feats["greeting"]:
        return "greeting / intro boilerplate"
    if feats["filler_density"] > 0.4:
        return "filler-heavy"
    if float(seg.get("no_speech_prob", 0.0) or 0.0) > 0.6:
        return "probably not speech"
    if scores["composite"] < 0.28:
        return "weak on every dimension"
    return None
