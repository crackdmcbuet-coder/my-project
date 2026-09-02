"""STEP 23/24/25 -- the paperwork: hooks, script, timeline breakdown, decisions.

Every line traces to a real source file and timestamp so nothing in the promo is
unattributable (RULE 1, RULE 7).
"""
from __future__ import annotations

from pathlib import Path

from . import timeline as tlmod
from .config import Config
from .util import short_tc, tc, write_text

RULE = "=" * 68


def timeline_breakdown(tl: dict, cfg: Config) -> str:
    lines = [RULE, f"TIMELINE BREAKDOWN -- {tl['label']}",
             f"concept : {tl['concept']} ({tl['concept_name']})",
             f"why     : {tl['concept_why']}",
             f"duration: {tl['duration']:.2f}s over {tl['shot_count']} shots"
             f"  (target {tl['target']}s)", RULE, ""]
    if tl.get("missing_beats"):
        lines += [f"!! beats with no matching clip: {', '.join(tl['missing_beats'])}", ""]
    if tl.get("underfilled"):
        lines += [f"!! {tl['shortfall']:.1f}s short of target -- the source material "
                  f"does not support this length", ""]

    music = cfg.get("audio.music_bed") or "(none configured)"
    for i, s in enumerate(tl["shots"], 1):
        spoken = " ".join(w["w"].strip() for w in (s.get("words") or [])).strip()
        lines += [
            f"[{i:02d}] {short_tc(s['t_in'])}-{short_tc(s['t_out'])}   ({s['dur']:.2f}s)",
            f"     VIDEO SOURCE : {s['source_name']}",
            f"     TIMESTAMP    : {tc(s['src_in'])} - {tc(s['src_out'])}",
            f"     BEAT         : {s['beat']}",
            f"     AUDIO        : \"{spoken}\"" if spoken else "     AUDIO        : (no speech in this frame)",
            f"     TEXT         : {_text_for(s)}",
            f"     VISUAL       : {_visual_for(s)}",
            f"     TRANSITION   : {s['transition']}",
            f"     SFX          : {s['sfx'] or '(none)'}",
            f"     MUSIC        : {music}",
            f"     REASON       : {s['reason']}",
            "",
        ]
    return "\n".join(lines)


def _visual_for(s: dict) -> str:
    return {
        "WIDE": "full frame, speaker centred",
        "PUNCH_MED": f"punch-in {s['punch']:.2f}x",
        "PUNCH_CLOSE": f"close punch-in {s['punch']:.2f}x",
        "REFRAME": f"reframe / alternate crop {s['punch']:.2f}x",
        "TEXT_CARD": "full-screen statement card over blurred A-roll",
        "KEYWORD_POP": f"extreme punch-in {s['punch']:.2f}x + keyword animation",
    }.get(s["treatment"], s["treatment"])


def _text_for(s: dict) -> str:
    if s["treatment"] == "TEXT_CARD":
        spoken = " ".join(w["w"].strip() for w in (s.get("words") or [])).strip()
        return f"CARD: \"{spoken}\""
    if s.get("emphasis"):
        return f"caption, emphasising \"{s['emphasis']}\""
    return "caption"


def promo_script(tl: dict) -> str:
    lines = [RULE, f"PROMO SCRIPT -- {tl['label']}",
             "every line below is spoken in the source footage; nothing is written for it",
             RULE, ""]
    for b in tl.get("beats", []):
        if b.get("missing"):
            lines += [f"{b['beat']:<16} [NO CLIP FOUND -- wanted {', '.join(b['wanted'])}]", ""]
            continue
        lines += [
            f"{b['beat']:<16} ({b.get('use_out', 0) - b.get('use_in', 0):.1f}s)",
            f"    \"{b['text']}\"",
            f"    source: {b['source_name']} @ {tc(b.get('use_in', b['start']))}",
            "",
        ]
    return "\n".join(lines)


def hook_options(bank: dict, cfg: Config, n: int = 3) -> str:
    """STEP 24 -- alternate openings for A/B testing, each a different angle."""
    from .bank import query
    lines = [RULE, "HOOK OPTIONS (A/B)", "each is a real spoken line -- swap with "
             "`promo build --hook-id <id>`", RULE, ""]
    angles = [("A", "CURIOSITY", "INSIGHT", "curiosity"),
              ("B", "PROBLEM", "PROBLEM", "relatability"),
              ("C", "AUTHORITY / INSIGHT", "AUTHORITY", "authority")]
    used: set[str] = set()
    for label, title, cat, key in angles:
        lines.append(f"HOOK {label}: {title}")
        picks = query(bank, category=cat, top=n + 4, sort_by=key, exclude_ids=used)
        if not picks:
            lines += ["    (no clip in the bank supports this angle)", ""]
            continue
        for c in picks[:n]:
            used.add(c["id"])
            lines += [f"    id     : {c['id']}",
                      f"    line   : \"{c['text']}\"",
                      f"    source : {c['source_name']} @ {c['tc']}",
                      f"    scores : hook={c['scores']['hook_power']:.2f} "
                      f"{key}={c['scores'][key]:.2f} composite={c['scores']['composite']:.2f}",
                      ""]
    return "\n".join(lines)


def source_clips(tl: dict) -> str:
    lines = [RULE, "SOURCE CLIPS USED", RULE, ""]
    seen = []
    for b in tl.get("beats", []):
        if b.get("missing"):
            continue
        seen.append(b)
    for b in seen:
        lines += [f"{b['source_name']}  {tc(b.get('use_in', b['start']))} - "
                  f"{tc(b.get('use_out', b['end']))}   [{b['beat']}]",
                  f"    \"{b['text']}\"",
                  f"    categories: {', '.join(b['categories'])}",
                  f"    path: {b['source']}",
                  ""]
    return "\n".join(lines)


def edit_decisions(tl: dict, audit_report: dict, concepts: dict[str, float]) -> str:
    lines = [RULE, f"EDIT DECISIONS -- {tl['label']}", RULE, "",
             "CONCEPT SELECTION (STEP 5)"]
    for key, score in sorted(concepts.items(), key=lambda kv: -kv[1]):
        mark = "  <-- SELECTED" if key == tl["concept"] else ""
        lines.append(f"    {key}  {tlmod.CONCEPTS[key]['name']:<30} "
                     f"score {score:.3f}{mark}")
    lines += ["", f"    reason: {tl['concept_why']}", "",
              "CUT DECISIONS (STEP 8) -- every visual change and why", ""]
    for i, s in enumerate(tl["shots"], 1):
        lines.append(f"    {i:02d}. {short_tc(s['t_in'])} {s['treatment']:<12} "
                     f"{s['dur']:.2f}s -- {s['reason']}")
    lines += ["", "RETENTION AUDIT (STEP 21)", ""]
    from .audit import format_report
    lines.append(format_report(audit_report))
    return "\n".join(lines)


def write_all(tl: dict, cfg: Config, bank: dict, audit_report: dict,
              concepts: dict[str, float], out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = [
        write_text(out_dir / "TIMELINE_BREAKDOWN.txt", timeline_breakdown(tl, cfg)),
        write_text(out_dir / "PROMO_SCRIPT.txt", promo_script(tl)),
        write_text(out_dir / "SOURCE_CLIPS.txt", source_clips(tl)),
        write_text(out_dir / "EDIT_DECISIONS.txt", edit_decisions(tl, audit_report, concepts)),
        write_text(out_dir / "HOOK_OPTIONS.txt", hook_options(bank, cfg)),
    ]
    return written
