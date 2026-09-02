"""STEP 21/22 -- brutal retention audit and mobile-first check.

Answers the 15 questions from the brief against the actual timeline, plus the
mobile checks. Findings are severities, not opinions: FAIL blocks delivery,
WARN is a judgement call, INFO is context.
"""
from __future__ import annotations

from statistics import mean, pstdev

from . import lexicon as lx
from .config import Config

FAIL, WARN, INFO, OK = "FAIL", "WARN", "INFO", "OK"


def _f(sev: str, q: str, detail: str, fix: str = "") -> dict:
    return {"severity": sev, "check": q, "detail": detail, "fix": fix}


def audit(timeline: dict, cfg: Config, bank: dict | None = None,
          sources: dict | None = None) -> dict:
    shots = timeline.get("shots") or []
    out: list[dict] = []
    if not shots:
        return {"findings": [_f(FAIL, "timeline", "no shots -- nothing to audit")],
                "score": 0.0, "verdict": "empty"}

    total = timeline["duration"]
    durs = [s["dur"] for s in shots]
    beats = [b for b in timeline.get("beats", []) if not b.get("missing")]

    # 1. Is the first second strong?
    first = shots[0]
    hook_beat = next((b for b in beats if b["beat"] == "HOOK"), None)
    hp = hook_beat["scores"]["hook_power"] if hook_beat else 0.0
    if hp < 0.35:
        out.append(_f(FAIL, "1. first second", f"hook_power={hp:.2f} -- weak opener",
                      "try `promo hooks` and force a stronger one with --hook-id"))
    elif hp < 0.5:
        out.append(_f(WARN, "1. first second", f"hook_power={hp:.2f} -- serviceable, not strong",
                      "check the alternates in HOOK_OPTIONS.txt"))
    else:
        out.append(_f(OK, "1. first second", f"hook_power={hp:.2f}"))
    if first["dur"] > 1.6:
        out.append(_f(WARN, "1. first second",
                      f"opening shot holds {first['dur']:.2f}s before any change",
                      "the first visual should move inside ~1.2s"))

    # 2. Unnecessary intro?
    if hook_beat and lx.starts_with_greeting(hook_beat.get("text", "")):
        out.append(_f(FAIL, "2. no intro boilerplate", "promo opens on a greeting",
                      "STEP 7: never open on salam/welcome/name"))
    else:
        out.append(_f(OK, "2. no intro boilerplate", "opens on substance"))

    # 3. Repetition?
    import difflib
    texts = [b.get("text", "") for b in beats]
    dupes = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            r = difflib.SequenceMatcher(None, lx.normalize(texts[i]),
                                        lx.normalize(texts[j])).ratio()
            if r > 0.62:
                dupes.append((beats[i]["beat"], beats[j]["beat"], round(r, 2)))
    if dupes:
        out.append(_f(WARN, "3. repetition",
                      "; ".join(f"{a}~{b} ({r})" for a, b, r in dupes[:3]),
                      "these beats say the same thing -- swap one out"))
    else:
        out.append(_f(OK, "3. repetition", "no near-duplicate lines"))

    # 4/5. Does the visual change when attention may drop? Boring stretches?
    long_holds = [(s["t_in"], s["dur"]) for s in shots
                  if s["dur"] > cfg.get("attention.max_shot", 3.2)]
    if long_holds:
        out.append(_f(WARN, "4/5. attention holds",
                      "; ".join(f"{t:.1f}s holds {d:.2f}s" for t, d in long_holds[:4]),
                      "add a punch-in or an insert at these points"))
    else:
        out.append(_f(OK, "4/5. attention holds", "no shot outstays its budget"))

    # 6. Speaker talking too long without visual support?
    runs, cur, cur_src = [], 0.0, None
    for s in shots:
        if s["source"] == cur_src and s["treatment"] in ("WIDE", "PUNCH_MED"):
            cur += s["dur"]
        else:
            runs.append(cur)
            cur, cur_src = s["dur"], s["source"]
    runs.append(cur)
    if runs and max(runs) > 5.0:
        out.append(_f(WARN, "6. unsupported talking head",
                      f"{max(runs):.1f}s of plain A-roll from one source",
                      "insert a slide, screen recording or statement card"))
    else:
        out.append(_f(OK, "6. unsupported talking head",
                      f"longest plain A-roll run {max(runs) if runs else 0:.1f}s"))

    # 7. Captions repetitive / wall of text?
    cards = [s for s in shots if s["treatment"] == "TEXT_CARD"]
    text_frac = sum(s["dur"] for s in shots
                    if s["treatment"] in ("TEXT_CARD", "KEYWORD_POP")) / total
    if text_frac > 0.45:
        out.append(_f(WARN, "7. wall of text",
                      f"{text_frac:.0%} of the promo is text-dominant",
                      "STEP 10: the speaker must stay primary"))
    else:
        out.append(_f(OK, "7. wall of text", f"text-dominant frames {text_frac:.0%}"))
    if len(cards) > 2:
        out.append(_f(WARN, "7. statement cards", f"{len(cards)} full-screen cards",
                      "cards are an interrupt; 1 is usually right"))

    # 8/9. Pacing -- too fast, too slow, and is it varied at all?
    m, sd = mean(durs), (pstdev(durs) if len(durs) > 1 else 0.0)
    if m < 0.75:
        out.append(_f(WARN, "8. too fast", f"mean shot {m:.2f}s -- reads as frantic",
                      "raise attention.early_budget"))
    elif m > 2.8:
        out.append(_f(WARN, "9. too slow", f"mean shot {m:.2f}s",
                      "lower attention.late_budget"))
    else:
        out.append(_f(OK, "8/9. pacing", f"mean shot {m:.2f}s"))
    if sd < 0.22:
        out.append(_f(FAIL, "5. mechanical cutting",
                      f"shot lengths barely vary (sd={sd:.2f}s)",
                      "RULE 5: this is metronome editing, not attention editing"))
    else:
        out.append(_f(OK, "5. mechanical cutting", f"shot-length variety sd={sd:.2f}s"))

    # 10. Does every shot have a purpose?
    unexplained = [s for s in shots if not s.get("reason")]
    out.append(_f(FAIL if unexplained else OK, "10. every cut has a reason",
                  f"{len(unexplained)} shots with no recorded reason"
                  if unexplained else "all cuts justified"))

    # 11/12/13. Value, curiosity, CTA.
    for label, beat_names, key, thresh in (
        ("11. value obvious", ("VALUE", "TEACHING", "RELIEF"), "value", 0.35),
        ("12. curiosity", ("CURIOSITY_GAP", "KEY_INSIGHT", "DIFFERENTIATOR"), "curiosity", 0.30),
    ):
        rel = [b for b in beats if b["beat"] in beat_names]
        if not rel:
            out.append(_f(WARN, label, "no beat of this kind made the cut"))
            continue
        v = max(b["scores"][key] for b in rel)
        out.append(_f(OK if v >= thresh else WARN, label, f"best {key}={v:.2f}"))

    cta = next((b for b in beats if b["beat"] == "CTA"), None)
    if not cta:
        out.append(_f(FAIL, "13. CTA", "no CTA clip found in the bank",
                      "record one line, or set cta.text in the config"))
    else:
        out.append(_f(OK, "13. CTA", f'"{cta["text"][:56]}"'))

    # 14. Abrupt ending?
    if shots[-1]["dur"] < 1.0:
        out.append(_f(WARN, "14. ending", f"final shot is {shots[-1]['dur']:.2f}s",
                      "let the CTA hold ~1.5s so it can be read"))
    else:
        out.append(_f(OK, "14. ending", f"final shot {shots[-1]['dur']:.2f}s"))

    # 15. Would a stranger follow it? Proxy: is the arc complete?
    if timeline.get("missing_beats"):
        out.append(_f(WARN, "15. stranger test",
                      f"missing beats: {', '.join(timeline['missing_beats'])}",
                      "the arc has a gap -- the bank has no clip for it"))
    else:
        out.append(_f(OK, "15. stranger test", "full arc present"))

    # Length honesty (STEP 25).
    if timeline.get("underfilled"):
        out.append(_f(WARN, "length", f"{timeline['shortfall']:.1f}s short of target",
                      "the source cannot carry this length -- ship the shorter cut"))

    out += mobile_checks(timeline, cfg, sources)

    fails = sum(1 for f in out if f["severity"] == FAIL)
    warns = sum(1 for f in out if f["severity"] == WARN)
    score = max(0.0, 1.0 - fails * 0.25 - warns * 0.06)
    return {
        "findings": out,
        "fail": fails, "warn": warns,
        "score": round(score, 3),
        "verdict": "blocked" if fails else ("ship with notes" if warns else "clean"),
    }


def mobile_checks(timeline: dict, cfg: Config, sources: dict | None) -> list[dict]:
    """STEP 22 -- 9:16, safe areas, and whether the crop actually holds up."""
    out = []
    W, H = cfg.get("output.width"), cfg.get("output.height")
    if abs((W / H) - (9 / 16)) > 0.01:
        out.append(_f(WARN, "22. aspect", f"output is {W}x{H}, not 9:16"))
    else:
        out.append(_f(OK, "22. aspect", f"{W}x{H} (9:16)"))

    sx, ty, sw, sh = cfg.safe_box()
    out.append(_f(OK, "22. safe area",
                  f"text confined to x{sx}..{sx + sw}, y{ty}..{ty + sh} "
                  f"(top {cfg.get('safe_area.top_pct'):.0%} / "
                  f"bottom {cfg.get('safe_area.bottom_pct'):.0%} kept clear)"))

    # Upscale check: a 16:9 1080p source loses real resolution when cropped to 9:16.
    if sources:
        worst = []
        for s in timeline.get("shots", []):
            from pathlib import Path
            src = sources.get(str(Path(s["source"]).resolve()))
            if not src or not src.get("width"):
                continue
            crop_w = src["height"] * (W / H) / max(1.0, s.get("punch", 1.0))
            if crop_w > 0:
                factor = W / crop_w
                if factor > 1.5:
                    worst.append((src["name"], round(factor, 2)))
        if worst:
            uniq = sorted({n: f for n, f in worst}.items(), key=lambda kv: -kv[1])
            out.append(_f(WARN, "22. crop resolution",
                          "; ".join(f"{n} upscales {f}x" for n, f in uniq[:3]),
                          "expected for 16:9 -> 9:16; shoot or export 4K to avoid softness"))
        else:
            out.append(_f(OK, "22. crop resolution", "no significant upscaling"))

    sub_size = int(H * cfg.get("subtitles.size_pct"))
    if sub_size < 60:
        out.append(_f(WARN, "22. caption size", f"{sub_size}px is small on a phone"))
    else:
        out.append(_f(OK, "22. caption size", f"{sub_size}px"))
    return out


def format_report(rep: dict) -> str:
    order = {FAIL: 0, WARN: 1, INFO: 2, OK: 3}
    lines = [f"RETENTION AUDIT -- {rep['verdict'].upper()} "
             f"(score {rep['score']:.2f}, {rep['fail']} fail / {rep['warn']} warn)", ""]
    for f in sorted(rep["findings"], key=lambda f: (order.get(f["severity"], 9), f["check"])):
        lines.append(f"[{f['severity']:<4}] {f['check']}: {f['detail']}")
        if f.get("fix"):
            lines.append(f"         -> {f['fix']}")
    return "\n".join(lines)
