"""promo -- command line for the course promo engine.

Pipeline order mirrors the brief's EXECUTION MODE: nothing renders until the
material has been found, understood, banked, and audited.

    promo discover      STEP 1   find course footage
    promo probe         STEP 2   technical library
    promo transcribe    STEP 2   word-level transcripts
    promo bank build    STEP 2/4 the reusable content bank
    promo bank query             pull clips for any future reel
    promo positioning   STEP 3   course positioning map
    promo hooks         STEP 24  A/B hook options
    promo build         STEP 5-9 concept -> timeline -> audit
    promo audit         STEP 21  re-audit a saved timeline
    promo render        STEP 25  ffmpeg render + deliverables
    promo doctor                 verify ffmpeg on this machine
    promo all                    discover -> render, one command
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import audit as audit_mod
from . import bank as bank_mod
from . import deliver, discover, probe, render as render_mod, subtitles, timeline as tl_mod
from . import transcribe as tr_mod
from .config import Config
from .util import read_json, write_json, write_text, eprint


# ----------------------------------------------------------------- commands


def cmd_discover(args, cfg: Config) -> int:
    res = discover.run(cfg, args.root or None)
    print(f"scanned: {', '.join(res['roots_scanned']) or '(nothing)'}")
    print(f"media files: {len(res['media'])}   stills: {len(res['stills'])}")
    if not res["media"]:
        eprint("\nNo media found. Point the engine at the right place:")
        eprint("  promo discover --root '/path/to/course'")
        eprint("  (or set sources.roots in promo.config.json)")
        return 1
    print("\ncandidate course folders (strongest first):")
    for c in res["candidates"][:8]:
        seq = " sequential-naming" if c["sequential_naming"] else ""
        print(f"  [{c['score']:>6.1f}] {c['dir']}")
        print(f"           {c['file_count']} files, {c['total_gb']} GB,"
              f" {c['still_count']} stills{seq}")
    print("\nIf the top folder is not your course, re-run with --root on the right one.")
    return 0


def cmd_probe(args, cfg: Config) -> int:
    paths = None
    if args.dir:
        disc = read_json(cfg.dir_index / "discovered.json", default={"media": []})
        paths = [m["path"] for m in disc["media"] if m["dir"] == args.dir]
        if not paths:
            eprint(f"no discovered media under {args.dir}")
            return 1
    lib = probe.run_probe(cfg, paths, loudness=not args.fast)
    usable = [f for f in lib["files"] if f.get("usable")]
    print(f"\nprobed {lib['count']} files, {len(usable)} usable")
    for f in lib["files"]:
        if f.get("flag"):
            print(f"  !! {f['name']}: {f['flag']}")
        elif f.get("error"):
            print(f"  !! {f['name']}: {f['error']}")
    total = sum(f.get("duration", 0) for f in usable)
    print(f"total usable runtime: {total / 3600:.2f} h")
    return 0


def cmd_transcribe(args, cfg: Config) -> int:
    tr_mod.run_transcribe(cfg, args.file or None, force=args.force)
    return 0


def cmd_bank(args, cfg: Config) -> int:
    if args.bank_cmd == "build":
        b = bank_mod.build(cfg)
        print("\n".join(bank_mod.summary_lines(b)))
        return 0
    b = bank_mod.load(cfg)
    if args.bank_cmd == "stats":
        print("\n".join(bank_mod.summary_lines(b)))
        return 0
    clips = bank_mod.query(b, category=args.category, top=args.top,
                           min_dur=args.min_dur, max_dur=args.max_dur,
                           source=args.source, sort_by=args.sort)
    if args.json:
        print(json.dumps(clips, ensure_ascii=False, indent=2))
        return 0
    if not clips:
        print("no clips matched")
        return 1
    for c in clips:
        print(f"[{c['scores'][args.sort]:.3f}] {c['id']}  {c['tc']}  ({c['duration']:.1f}s)")
        print(f"    {c['text']}")
        print(f"    {c['source_name']} | {', '.join(c['categories'])}"
              f"{' | NEEDS REVIEW' if c['needs_review'] else ''}")
    return 0


def cmd_positioning(args, cfg: Config) -> int:
    """STEP 3 -- assemble what the footage actually says, per positioning question.

    Deliberately does not write the positioning statement itself: that is a claim
    about the course, and claims come from the owner, not from a keyword match.
    """
    b = bank_mod.load(cfg)
    questions = [
        ("What problem does it solve?", "PROBLEM"),
        ("What is taught?", "TEACHING"),
        ("What makes it different?", "INSIGHT"),
        ("Why trust the instructor?", "AUTHORITY"),
        ("What transformation is offered?", "TRANSFORMATION"),
        ("What objections come up?", "OBJECTION"),
        ("What is the call to action?", "CTA"),
    ]
    lines = ["=" * 68, "COURSE POSITIONING MAP", "",
             "Evidence drawn from the footage. Blank sections are gaps in the",
             "material, not answers to invent (RULE 1 / RULE 14).", "=" * 68, ""]
    for q, cat in questions:
        lines.append(f"## {q}   [{cat}]")
        picks = bank_mod.query(b, category=cat, top=args.top)
        if not picks:
            lines += ["    !! NO EVIDENCE IN THE FOOTAGE -- flag to the course owner", ""]
            continue
        for c in picks:
            lines += [f'    "{c["text"]}"',
                      f"        {c['source_name']} @ {c['tc']}  ({c['id']})"]
        lines.append("")
    out = cfg.dir_out / "COURSE_POSITIONING_MAP.txt"
    write_text(out, "\n".join(lines))
    print("\n".join(lines))
    print(f"\nwritten: {out}")
    return 0


def cmd_hooks(args, cfg: Config) -> int:
    b = bank_mod.load(cfg)
    text = deliver.hook_options(b, cfg, n=args.top)
    write_text(cfg.dir_out / "HOOK_OPTIONS.txt", text)
    print(text)
    return 0


def _pick_concept(b: dict, cfg: Config, target: float, forced_hook, concept: str | None):
    scores: dict[str, float] = {}
    best, best_tl = None, None
    for key in tl_mod.CONCEPTS:
        tl = tl_mod.build(b, cfg, concept=key, target=target, forced_hook=forced_hook)
        scores[key] = tl_mod.score_concept(tl)
        if concept and key == concept:
            best, best_tl = key, tl
        elif not concept and (best is None or scores[key] > scores[best]):
            best, best_tl = key, tl
    return best, best_tl, scores


def cmd_build(args, cfg: Config) -> int:
    b = bank_mod.load(cfg)
    forced_hook = None
    if args.hook_id:
        forced_hook = next((c for c in b["clips"] if c["id"] == args.hook_id), None)
        if not forced_hook:
            eprint(f"no clip with id {args.hook_id} -- see `promo hooks`")
            return 1

    concept = (args.concept or "").upper() or None
    if concept and concept not in tl_mod.CONCEPTS:
        eprint(f"concept must be one of {list(tl_mod.CONCEPTS)}")
        return 1

    best, tl, scores = _pick_concept(b, cfg, args.target, forced_hook, concept)
    tl["label"] = args.label or f"promo_{int(args.target)}s"
    tl["concept_scores"] = scores

    lib = read_json(cfg.dir_index / "library.json", default={"files": []})
    srcs = {str(Path(f["path"]).resolve()): f for f in lib.get("files", [])}
    rep = audit_mod.audit(tl, cfg, b, srcs)
    tl["audit"] = rep

    out = cfg.dir_timelines / f"{tl['label']}.json"
    write_json(out, tl)
    print(f"CONCEPT SCORES: " +
          "  ".join(f"{k}={v:.3f}" for k, v in sorted(scores.items())))
    print(f"selected {best} ({tl['concept_name']}) -- {tl['concept_why']}")
    print(f"{tl['duration']:.1f}s / {tl['shot_count']} shots -> {out}\n")
    print(audit_mod.format_report(rep))
    return 0 if rep["verdict"] != "blocked" else 2


def _load_tl(cfg: Config, label: str) -> dict:
    p = cfg.dir_timelines / f"{label}.json"
    if not p.exists():
        raise SystemExit(f"no timeline named {label} -- run `promo build --label {label}`")
    return read_json(p)


def cmd_audit(args, cfg: Config) -> int:
    tl = _load_tl(cfg, args.label)
    b = bank_mod.load(cfg)
    lib = read_json(cfg.dir_index / "library.json", default={"files": []})
    srcs = {str(Path(f["path"]).resolve()): f for f in lib.get("files", [])}
    rep = audit_mod.audit(tl, cfg, b, srcs)
    print(audit_mod.format_report(rep))
    return 0 if rep["verdict"] != "blocked" else 2


def cmd_render(args, cfg: Config) -> int:
    tl = _load_tl(cfg, args.label)
    b = bank_mod.load(cfg)
    out_dir = cfg.dir_out / tl["label"]
    out_dir.mkdir(parents=True, exist_ok=True)

    ass = out_dir / f"{tl['label']}.ass"
    subtitles.write_ass(tl["shots"], cfg, ass)
    write_text(out_dir / f"{tl['label']}.srt", subtitles.build_srt(tl["shots"], cfg))

    rep = tl.get("audit") or audit_mod.audit(tl, cfg, b)
    if rep.get("verdict") == "blocked" and not args.force:
        eprint(audit_mod.format_report(rep))
        eprint("\nAudit blocked this cut. Fix the FAILs, or re-run with --force.")
        return 2

    deliver.write_all(tl, cfg, b, rep, tl.get("concept_scores", {}), out_dir)
    mp4 = out_dir / f"{tl['label']}.mp4"
    res = render_mod.render(tl, cfg, mp4, ass_path=ass, motion=args.motion,
                            dry_run=args.dry_run)
    print(f"deliverables: {out_dir}")
    if args.dry_run:
        print(f"dry run -- ffmpeg script written to {res['script']}")
    else:
        print(f"rendered: {mp4}")
    return 0


def cmd_doctor(args, cfg: Config) -> int:
    rep = render_mod.doctor(cfg)
    for k, v in rep.items():
        print(f"  {k:<20} {v}")
    return 0 if rep.get("verdict") == "ready" else 1


def cmd_all(args, cfg: Config) -> int:
    """STEP 25 -- the whole pipeline, producing every version the source supports."""
    if cmd_discover(argparse.Namespace(root=args.root), cfg) != 0:
        return 1
    cmd_probe(argparse.Namespace(dir=args.dir, fast=False), cfg)
    tr_mod.run_transcribe(cfg, None, force=False)
    b = bank_mod.build(cfg)
    print("\n".join(bank_mod.summary_lines(b)))

    made, skipped = [], []
    for v in cfg.get("versions", []):
        target = float(v["target"])
        concept = None if v.get("concept") in (None, "auto") else v["concept"]
        best, tl, scores = _pick_concept(b, cfg, target, None, concept)
        tl["label"] = v["id"]
        tl["concept_scores"] = scores
        if tl["underfilled"]:
            skipped.append((v["id"], tl["shortfall"]))
            continue
        lib = read_json(cfg.dir_index / "library.json", default={"files": []})
        srcs = {str(Path(f["path"]).resolve()): f for f in lib.get("files", [])}
        tl["audit"] = audit_mod.audit(tl, cfg, b, srcs)
        write_json(cfg.dir_timelines / f"{tl['label']}.json", tl)
        rc = cmd_render(argparse.Namespace(label=tl["label"], motion=args.motion,
                                           dry_run=args.dry_run, force=False), cfg)
        (made if rc == 0 else skipped).append((v["id"], tl["duration"]))

    print("\n" + "=" * 60)
    for vid, d in made:
        print(f"  BUILT   {vid}  ({d:.1f}s)")
    for vid, short in skipped:
        print(f"  SKIPPED {vid}  -- source material {short:.1f}s short (STEP 25)")
    return 0


# -------------------------------------------------------------------- parser


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="promo", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-c", "--config", default=None, help="path to promo.config.json")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="STEP 1: find course footage")
    d.add_argument("--root", action="append", help="folder to scan (repeatable)")
    d.set_defaults(fn=cmd_discover)

    pr = sub.add_parser("probe", help="STEP 2: technical source library")
    pr.add_argument("--dir", help="only probe files in this discovered folder")
    pr.add_argument("--fast", action="store_true", help="skip loudness measurement")
    pr.set_defaults(fn=cmd_probe)

    t = sub.add_parser("transcribe", help="STEP 2: word-level transcripts")
    t.add_argument("--file", action="append", help="specific file (repeatable)")
    t.add_argument("--force", action="store_true", help="ignore cache")
    t.set_defaults(fn=cmd_transcribe)

    bk = sub.add_parser("bank", help="the reusable content bank")
    bs = bk.add_subparsers(dest="bank_cmd", required=True)
    bs.add_parser("build", help="build/rebuild from transcripts")
    bs.add_parser("stats", help="category counts")
    q = bs.add_parser("query", help="pull clips for any future reel")
    q.add_argument("--category", help="HOOK PROBLEM EMOTIONAL AUTHORITY INSIGHT "
                                      "TEACHING TRANSFORMATION OBJECTION CTA")
    q.add_argument("--top", type=int, default=20)
    q.add_argument("--min-dur", type=float, default=0.0, dest="min_dur")
    q.add_argument("--max-dur", type=float, default=999.0, dest="max_dur")
    q.add_argument("--source", help="filter by source filename substring")
    q.add_argument("--sort", default="composite",
                   help="composite or any scoring dimension")
    q.add_argument("--json", action="store_true")
    bk.set_defaults(fn=cmd_bank)

    po = sub.add_parser("positioning", help="STEP 3: course positioning map")
    po.add_argument("--top", type=int, default=4)
    po.set_defaults(fn=cmd_positioning)

    hk = sub.add_parser("hooks", help="STEP 24: A/B hook options")
    hk.add_argument("--top", type=int, default=3)
    hk.set_defaults(fn=cmd_hooks)

    b = sub.add_parser("build", help="STEP 5-9: concept -> timeline -> audit")
    b.add_argument("--target", type=float, default=30.0, help="target seconds")
    b.add_argument("--concept", help="A, B or C (default: pick the strongest)")
    b.add_argument("--hook-id", dest="hook_id", help="force a specific opening clip")
    b.add_argument("--label", help="name for this timeline")
    b.set_defaults(fn=cmd_build)

    a = sub.add_parser("audit", help="STEP 21: re-audit a saved timeline")
    a.add_argument("label")
    a.set_defaults(fn=cmd_audit)

    r = sub.add_parser("render", help="STEP 25: render + write deliverables")
    r.add_argument("label")
    r.add_argument("--motion", action="store_true",
                   help="zoompan camera movement (run `promo doctor` first)")
    r.add_argument("--dry-run", action="store_true",
                   help="write the ffmpeg script without running it")
    r.add_argument("--force", action="store_true", help="render despite audit FAILs")
    r.set_defaults(fn=cmd_render)

    doc = sub.add_parser("doctor", help="verify ffmpeg filtergraphs on this machine")
    doc.set_defaults(fn=cmd_doctor)

    al = sub.add_parser("all", help="discover -> render, every supported version")
    al.add_argument("--root", action="append")
    al.add_argument("--dir")
    al.add_argument("--motion", action="store_true")
    al.add_argument("--dry-run", action="store_true")
    al.set_defaults(fn=cmd_all)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = Config.load(args.config)
    cfg.ensure_dirs()
    try:
        return args.fn(args, cfg)
    except KeyboardInterrupt:
        eprint("\ninterrupted")
        return 130
    except (RuntimeError, FileNotFoundError) as e:
        eprint(f"error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
