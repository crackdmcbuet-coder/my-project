"""STEP 5/6/8/9 -- concept selection, beat planning, and the ATTENTION ENGINE.

The engine does not cut on a fixed cadence. It computes candidate change points
from real speech structure (sentence ends, breaths, emphasised words, energy) and
spends an *attention budget* that tightens early in the promo and relaxes later.
A shot is only cut when there is a reason, and the reason is recorded.
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field, asdict

from . import lexicon as lx
from .config import Config
from .util import clamp

# ------------------------------------------------------------------ concepts

CONCEPTS = {
    "A": {
        "name": "CURIOSITY / HOOK-DRIVEN",
        "why": "opens on an unanswered question and withholds the answer",
        "beats": [
            ("HOOK",           ["HOOK", "INSIGHT"],                    0.09, "hook_power"),
            ("CURIOSITY_GAP",  ["INSIGHT", "PROBLEM"],                 0.13, "curiosity"),
            ("KEY_INSIGHT",    ["INSIGHT", "TEACHING"],                0.20, "curiosity"),
            ("VALUE",          ["TEACHING", "TRANSFORMATION"],         0.22, "value"),
            ("PROOF",          ["AUTHORITY"],                          0.16, "authority"),
            ("OUTCOME",        ["TRANSFORMATION"],                     0.12, "value"),
            ("CTA",            ["CTA"],                                0.08, "clarity"),
        ],
    },
    "B": {
        "name": "PROBLEM / EMOTION-DRIVEN",
        "why": "names the viewer's pain first, then relieves it",
        "beats": [
            ("HOOK",           ["PROBLEM", "HOOK"],                    0.09, "relatability"),
            ("PAIN",           ["PROBLEM", "EMOTIONAL"],               0.17, "emotional"),
            ("OBJECTION",      ["OBJECTION", "PROBLEM"],               0.13, "relatability"),
            ("RELIEF",         ["INSIGHT", "TEACHING"],                0.21, "value"),
            ("VALUE",          ["TEACHING"],                           0.16, "value"),
            ("OUTCOME",        ["TRANSFORMATION", "EMOTIONAL"],        0.16, "emotional"),
            ("CTA",            ["CTA"],                                0.08, "clarity"),
        ],
    },
    "C": {
        "name": "AUTHORITY / VALUE-DRIVEN",
        "why": "earns trust first, so the teaching lands as credible",
        "beats": [
            ("HOOK",           ["AUTHORITY", "HOOK"],                  0.09, "authority"),
            ("CREDENTIAL",     ["AUTHORITY"],                          0.15, "authority"),
            ("PROBLEM",        ["PROBLEM"],                            0.13, "relatability"),
            ("TEACHING",       ["TEACHING"],                           0.24, "value"),
            ("DIFFERENTIATOR", ["INSIGHT", "TEACHING"],                0.16, "curiosity"),
            ("OUTCOME",        ["TRANSFORMATION"],                     0.15, "value"),
            ("CTA",            ["CTA"],                                0.08, "clarity"),
        ],
    },
}

# Visual treatments (STEP 9 / STEP 18). A-roll variants come from the same footage.
TREATMENTS = ["WIDE", "PUNCH_MED", "PUNCH_CLOSE", "REFRAME", "TEXT_CARD", "KEYWORD_POP"]
AROLL = ["WIDE", "PUNCH_MED", "PUNCH_CLOSE", "REFRAME"]


@dataclass
class Shot:
    t_in: float                 # promo-relative
    t_out: float
    source: str
    source_name: str
    src_in: float               # source-relative
    src_out: float
    beat: str
    treatment: str
    punch: float
    focus: tuple = (0.5, 0.42)  # normalised crop centre; faces sit above centre
    text: str = ""
    emphasis: str = ""
    transition: str = "CUT"
    sfx: str = ""
    reason: str = ""
    clip_id: str = ""
    words: list = field(default_factory=list)

    @property
    def dur(self) -> float:
        return self.t_out - self.t_in

    def to_dict(self) -> dict:
        d = asdict(self)
        d["focus"] = list(self.focus)
        d["dur"] = round(self.dur, 3)
        for k in ("t_in", "t_out", "src_in", "src_out", "punch"):
            d[k] = round(d[k], 3)
        return d


# ------------------------------------------------------------ clip selection


def _similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, lx.normalize(a), lx.normalize(b)).ratio()


def tighten(clip: dict, max_dur: float) -> tuple[float, float]:
    """Trim a clip to its strongest word window, snapped to word boundaries.

    Prefers a window that keeps the clip's keywords and ends on punctuation, so a
    trimmed line still sounds like a finished thought rather than a chop.
    """
    start, end = float(clip["start"]), float(clip["end"])
    if (end - start) <= max_dur:
        return start, end
    ws = clip.get("words") or []
    if not ws:
        return start, start + max_dur

    keys = set(clip.get("keywords") or [])
    best, best_score = (start, start + max_dur), -1e9
    for i in range(len(ws)):
        w_in = float(ws[i]["start"])
        j = i
        while j + 1 < len(ws) and float(ws[j + 1]["end"]) - w_in <= max_dur:
            j += 1
        w_out = float(ws[j]["end"])
        if w_out - w_in < min(1.0, max_dur * 0.6):
            continue
        span = ws[i:j + 1]
        toks = [lx.normalize(w["w"]).strip("।॥.,!?;:") for w in span]
        score = sum(1.5 for t in toks if t in keys)
        score += sum(0.4 for t in toks if t not in lx.STOPWORDS_EMPHASIS and len(t) > 2)
        if span[-1]["w"].rstrip()[-1:] in "।?!.॥":
            score += 2.0                                  # lands on a full stop
        if i == 0:
            score += 0.8                                  # keeps the natural opening
        score -= abs((w_out - w_in) - max_dur) * 0.5      # fill the slot
        if score > best_score:
            best_score, best = score, (w_in, w_out)
    return best


def select_clips(bank: dict, concept_key: str, target: float, cfg: Config,
                 *, forced_hook: dict | None = None) -> list[dict]:
    """Pick one strong clip per beat, avoiding repetition and source monotony."""
    from .bank import query

    concept = CONCEPTS[concept_key]
    used_ids: set[str] = set()
    used_texts: list[str] = []
    picked: list[dict] = []
    last_source = None
    same_source_run = 0

    for beat_name, cats, share, sort_key in concept["beats"]:
        slot = target * share
        chosen = None

        if beat_name == "HOOK" and forced_hook is not None:
            chosen = forced_hook
        else:
            cands: list[dict] = []
            for cat in cats:
                cands += query(bank, category=cat, top=40, sort_by=sort_key,
                               exclude_ids=used_ids)
            seen, uniq = set(), []
            for c in cands:
                if c["id"] in seen:
                    continue
                seen.add(c["id"])
                uniq.append(c)

            def rank(c: dict) -> float:
                s = c["scores"].get(sort_key, 0.0) * 2.0 + c["scores"]["composite"]
                # Prefer clips that roughly fit the slot; heavy trims lose context.
                fit = 1.0 - clamp(abs(c["duration"] - slot) / max(slot, 1.0), 0.0, 1.0)
                s += fit * 0.5
                if c["source"] == last_source and same_source_run >= 2:
                    s -= 0.35                            # force visual variety
                if c.get("needs_review"):
                    s -= 0.15                            # prefer confidently heard lines
                return -s

            for c in sorted(uniq, key=rank):
                if any(_similar(c["text"], t) > 0.72 for t in used_texts):
                    continue                             # near-duplicate line
                chosen = c
                break

        if chosen is None:
            picked.append({"beat": beat_name, "missing": True, "wanted": cats,
                           "slot": round(slot, 2)})
            continue

        used_ids.add(chosen["id"])
        used_texts.append(chosen["text"])
        same_source_run = same_source_run + 1 if chosen["source"] == last_source else 1
        last_source = chosen["source"]

        s_in, s_out = tighten(chosen, max(slot, 1.4))
        picked.append({**chosen, "beat": beat_name, "slot": round(slot, 2),
                       "use_in": s_in, "use_out": s_out, "missing": False})
    return picked


# ------------------------------------------------------------ attention engine


def change_points(words: list[dict], s_in: float, s_out: float,
                  keywords: set[str]) -> list[dict]:
    """Where the footage *invites* a visual change, and why."""
    pts: list[dict] = []
    prev_end = None
    for w in words:
        ws, we = float(w["start"]), float(w["end"])
        if ws < s_in - 0.01 or we > s_out + 0.01:
            continue
        tok = lx.normalize(w["w"]).strip("।॥.,!?;:\"'()[]")
        if prev_end is not None and ws - prev_end >= 0.22:
            pts.append({"t": ws, "kind": "BREATH", "weight": 0.7,
                        "reason": "breath / pause -- natural cut"})
        if tok in keywords:
            pts.append({"t": ws, "kind": "KEYWORD", "weight": 1.0, "token": w["w"],
                        "reason": f"emphasised word: {w['w'].strip()}"})
        if w["w"].rstrip()[-1:] in "।?!.॥,":
            pts.append({"t": we, "kind": "THOUGHT_END", "weight": 0.9,
                        "reason": "thought completes -- new idea begins"})
        if lx.count_cues(tok, lx.CONTRAST_CUES):
            pts.append({"t": ws, "kind": "CONTRAST", "weight": 0.95,
                        "reason": "contrast marker -- the argument turns"})
        prev_end = we
    pts.sort(key=lambda p: p["t"])
    # Collapse points that land within 120ms of each other, keeping the strongest.
    merged: list[dict] = []
    for p in pts:
        if merged and p["t"] - merged[-1]["t"] < 0.12:
            if p["weight"] > merged[-1]["weight"]:
                merged[-1] = p
            continue
        merged.append(p)
    return merged


def budget_at(t: float, total: float, cfg: Config) -> float:
    """Attention budget: how long a single visual may hold at promo time t."""
    early = cfg.get("attention.early_budget", 1.6)
    late = cfg.get("attention.late_budget", 2.6)
    window = cfg.get("attention.early_window", 8.0)
    if t <= window:
        return early
    frac = clamp((t - window) / max(1.0, total - window), 0.0, 1.0)
    return early + (late - early) * frac


def _next_treatment(prev: str, cp_kind: str, allow_card: bool) -> tuple[str, str]:
    """Choose the next visual and say why (STEP 18: purposeful pattern interrupts)."""
    if cp_kind == "KEYWORD" and prev != "KEYWORD_POP":
        return "KEYWORD_POP", "emphasised word gets a typographic hit"
    # A card lands hardest cutting *from* the speaker; stacking it on another text
    # frame is how a promo turns into a wall of text (STEP 10).
    if allow_card and prev in AROLL:
        return "TEXT_CARD", "strongest statement -- full-screen pattern interrupt"
    if cp_kind == "CONTRAST":
        return ("PUNCH_CLOSE" if prev != "PUNCH_CLOSE" else "REFRAME",
                "argument turns -- push in on the speaker")
    order = [t for t in AROLL if t != prev]
    if cp_kind == "THOUGHT_END":
        pick = "WIDE" if prev in ("PUNCH_CLOSE", "KEYWORD_POP") else "PUNCH_MED"
        if pick == prev:
            pick = order[0]
        return pick, "new idea -- reset the frame"
    return order[0], "attention budget spent -- refresh the visual"


def build_shots(picked: list[dict], cfg: Config, total: float) -> list[Shot]:
    levels = cfg.get("attention.punch_levels", [1.0, 1.12, 1.22, 1.35])
    punch_for = {"WIDE": levels[0], "PUNCH_MED": levels[1], "PUNCH_CLOSE": levels[2],
                 "REFRAME": levels[1], "KEYWORD_POP": levels[3], "TEXT_CARD": levels[0]}
    min_shot = cfg.get("attention.min_shot", 0.5)
    max_hero = cfg.get("attention.hero_shot", 4.5)

    shots: list[Shot] = []
    t = 0.0
    prev_treatment = ""
    prev_source = None

    usable = [p for p in picked if not p.get("missing")]
    # STEP 10 says statement cards are *occasional*: exactly one per promo, on the
    # strongest non-CTA line, so it reads as a deliberate interrupt rather than noise.
    # Not the hook (which needs the speaker's face and energy) and not the CTA
    # (which needs to read as a real instruction, not a graphic).
    card_candidates = [p for p in usable if p["beat"] not in ("HOOK", "CTA")]
    money_id = (max(card_candidates, key=lambda p: p["scores"]["composite"])["id"]
                if card_candidates else None)
    card_placed = False

    for p in usable:
        s_in, s_out = float(p["use_in"]), float(p["use_out"])
        keywords = set(p.get("keywords") or [])
        cps = change_points(p.get("words") or [], s_in, s_out, keywords)
        is_money = (p["id"] == money_id)
        cursor = s_in
        first_in_clip = True

        while cursor < s_out - 0.05:
            budget = budget_at(t, total, cfg)
            if first_in_clip and p["beat"] == "HOOK":
                budget = min(budget, 1.2)          # the first frames must move
            deadline = cursor + budget

            nxt = next((c for c in cps if c["t"] > cursor + min_shot), None)
            if nxt and nxt["t"] <= deadline + 0.45:
                cut_at, cp_kind, why = nxt["t"], nxt["kind"], nxt["reason"]
            elif nxt is None and (s_out - cursor) <= max_hero and is_money:
                cut_at, cp_kind, why = s_out, "HERO", "let the strongest line breathe"
            else:
                cut_at = min(deadline, s_out)
                cp_kind, why = "BUDGET", "attention would drop -- change the visual"

            if s_out - cut_at < min_shot:
                cut_at = s_out                      # never leave an orphan frame

            if first_in_clip:
                treatment = "WIDE" if p["beat"] in ("HOOK", "CTA") else "PUNCH_MED"
                if prev_source == p["source"]:
                    treatment = "PUNCH_CLOSE"       # same speaker again: change the size
                reason = f"{p['beat']} begins -- hard cut to a new source"
                transition = "CUT"
            else:
                card_ok = (is_money and not card_placed
                           and prev_treatment != "TEXT_CARD"
                           and t >= 2.0                      # the hook keeps the face
                           and (cut_at - cursor) >= 0.9)     # unreadable if shorter
                if card_ok:
                    # The promo's strongest line gets its one full-screen card, cut
                    # straight from the speaker so the interrupt actually lands.
                    treatment, why_t = ("TEXT_CARD",
                                        "strongest statement -- full-screen interrupt")
                    card_placed = True
                else:
                    treatment, why_t = _next_treatment(prev_treatment, cp_kind, False)
                head = why_t.split(" --")[0]
                reason = why_t if head in why else f"{why} -> {why_t}"
                transition = "CUT" if cp_kind in ("THOUGHT_END", "CONTRAST") else "PUSH"

            dur = cut_at - cursor
            shot_words = [w for w in (p.get("words") or [])
                          if cursor - 0.01 <= float(w["start"]) < cut_at + 0.01]
            # Emphasise a keyword this shot actually contains -- otherwise the
            # caption highlights a word that is not on screen.
            emph = ""
            for w in shot_words:
                tok = lx.normalize(w["w"]).strip("।॥.,!?;:\"'()[]")
                if tok in keywords:
                    emph = tok
                    break
            shots.append(Shot(
                t_in=t, t_out=t + dur,
                source=p["source"], source_name=p["source_name"],
                src_in=cursor, src_out=cut_at,
                beat=p["beat"], treatment=treatment, punch=punch_for[treatment],
                text=p["text"],
                emphasis=emph,
                transition=transition,
                sfx=("impact" if treatment == "TEXT_CARD" else
                     ("tick" if treatment == "KEYWORD_POP" else "")),
                reason=reason,
                clip_id=p["id"],
                words=shot_words,
            ))
            t += dur
            cursor = cut_at
            prev_treatment = treatment
            first_in_clip = False
        prev_source = p["source"]
    return shots


def fit_duration(picked: list[dict], target: float, *, tol: float = 0.06) -> list[dict]:
    """Expand or tighten the selected windows so the promo lands on its target.

    Expansion only ever gives a clip back its own real footage -- it never invents
    or stretches material (RULE 1).
    """
    usable = [p for p in picked if not p.get("missing")]
    if not usable:
        return picked
    for _ in range(6):
        total = sum(p["use_out"] - p["use_in"] for p in usable)
        if total <= 0:
            break
        drift = (target - total) / target
        if abs(drift) <= tol:
            break
        if drift > 0:                       # too short -- restore trimmed footage
            headroom = [((p["end"] - p["start"]) - (p["use_out"] - p["use_in"]), p)
                        for p in usable]
            room = sum(h for h, _ in headroom)
            if room <= 0.05:
                break
            need = target - total
            for h, q in headroom:
                if h <= 0:
                    continue
                give = min(h, need * (h / room))
                # Prefer restoring the tail: a line usually builds to its point.
                q["use_out"] = min(q["end"], q["use_out"] + give * 0.7)
                q["use_in"] = max(q["start"], q["use_in"] - give * 0.3)
        else:                               # too long -- retighten to word bounds
            over = total - target
            for q in usable:
                cur = q["use_out"] - q["use_in"]
                take = min(over * (cur / total), cur - 1.2)
                if take <= 0:
                    continue
                q["use_in"], q["use_out"] = tighten(
                    {**q, "start": q["use_in"], "end": q["use_out"]}, cur - take)
    return picked


def build(bank: dict, cfg: Config, *, concept: str, target: float,
          forced_hook: dict | None = None, label: str = "") -> dict:
    picked = select_clips(bank, concept, target, cfg, forced_hook=forced_hook)
    picked = fit_duration(picked, target)
    shots = build_shots(picked, cfg, target)
    dur = shots[-1].t_out if shots else 0.0
    shortfall = target - dur
    return {
        # STEP 25: if the material cannot carry this length, say so rather than
        # padding it out with filler.
        "underfilled": shortfall > target * 0.12,
        "shortfall": round(max(0.0, shortfall), 2),
        "label": label or f"concept_{concept}_{int(target)}s",
        "concept": concept,
        "concept_name": CONCEPTS[concept]["name"],
        "concept_why": CONCEPTS[concept]["why"],
        "target": target,
        "duration": round(dur, 3),
        "shot_count": len(shots),
        "missing_beats": [p["beat"] for p in picked if p.get("missing")],
        "beats": [{k: v for k, v in p.items() if k != "words"} for p in picked],
        "shots": [s.to_dict() for s in shots],
    }


def score_concept(tl: dict) -> float:
    """STEP 5 -- pick the strongest concept on expected retention, not taste."""
    shots = tl["shots"]
    if not shots:
        return -1e9
    beats = [b for b in tl["beats"] if not b.get("missing")]
    avg = sum(b["scores"]["composite"] for b in beats) / max(1, len(beats))
    hook = next((b["scores"]["hook_power"] for b in beats if b["beat"] == "HOOK"), 0.0)
    has_cta = any(b["beat"] == "CTA" for b in beats)
    variety = len({s["treatment"] for s in shots}) / len(TREATMENTS)
    sources = len({s["source"] for s in shots})
    penalty = len(tl["missing_beats"]) * 0.12
    fit = 1.0 - clamp(abs(tl["duration"] - tl["target"]) / tl["target"], 0.0, 1.0)
    return round(avg * 1.6 + hook * 1.8 + variety * 0.6 + min(sources, 4) * 0.08
                 + (0.3 if has_cta else 0.0) + fit * 0.5 - penalty, 4)
