"""Regression tests for the promo engine. Run: python3 tests/test_engine.py

Pure-Python only -- no ffmpeg, no whisper, no network. The parts that need real
media are covered by `promo doctor` on the target machine instead.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from statistics import pstdev

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))

from engine import audit, bank, lexicon as lx, render, scoring, subtitles, timeline  # noqa: E402
from engine.config import Config  # noqa: E402
from engine.discover import rank_folders  # noqa: E402
import make_fixture  # noqa: E402

PASS, FAIL = [], []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    print(f"  {'ok  ' if cond else 'FAIL'} {name}" + (f"  -- {detail}" if detail and not cond else ""))


def fixture_cfg(tmp: Path) -> Config:
    make_fixture.main(str(tmp))
    cfg = Config()
    cfg.data["work_dir"] = str(tmp)
    cfg.data["language"] = "bn"
    return cfg


# ------------------------------------------------------------------ lexicon

def test_lexicon() -> None:
    print("\nlexicon")
    check("short Bengali cue does not match inside a longer word",
          lx.count_cues("মানুষ অনেক কিছু", ["মা"]) == 0)
    check("standalone short cue still matches",
          lx.count_cues("আমার মা বলতেন", ["মা"]) == 1)
    check("Bengali stem matches inflected form",
          lx.count_cues("এই ভুলটা করবেন না", ["ভুল"]) == 1)
    check("multi-word cue matches as a phrase",
          lx.count_cues("বেশিরভাগ মানুষ পারে না", ["বেশিরভাগ মানুষ"]) == 1)
    check("greeting detected", lx.starts_with_greeting("আসসালামু আলাইকুম সবাইকে"))
    check("non-greeting not flagged", not lx.starts_with_greeting("বেশিরভাগ মানুষ ভুল করে"))
    check("Bengali question word detected", lx.is_question("কেন এটা কাজ করে না"))
    check("Bengali digits count as digits", lx.has_digit("১২ বছর"))
    check("script detection", lx.script_of("আমি বাংলা") == "bn"
          and lx.script_of("hello world") == "en")


# ------------------------------------------------------------------ scoring

def test_scoring() -> None:
    print("\nscoring")
    src = {"audio_quality": 1.0, "visual_quality": 0.9}

    def sc(text: str, dur: float = 3.0) -> dict:
        seg = {"start": 0.0, "end": dur, "text": text, "words": [], "avg_logprob": -0.3}
        return scoring.score_segment(seg, src)

    greet = sc("আসসালামু আলাইকুম, আজকে আমরা শুরু করব।")
    strong = sc("বেশিরভাগ মানুষ এই ভুলটা করে, আর সেজন্যই কখনো এগোতে পারে না।")
    check("greeting is crushed as a hook", greet["hook_power"] < 0.06,
          f"{greet['hook_power']}")
    check("problem line outranks greeting as hook",
          strong["hook_power"] > greet["hook_power"] * 5)
    check("authority line scores authority",
          sc("আমি ১২ বছর ধরে কাজ করেছি এবং হাজারো শিক্ষার্থীকে শিখিয়েছি।")["authority"] > 0.5)
    check("filler tanks clarity",
          sc("আচ্ছা মানে তো একটু ইয়ে বুঝলেন")["clarity"] < 0.6)
    check("all dimensions present and in range",
          all(0.0 <= strong[d] <= 1.0 for d in scoring.DIMENSIONS))


# ---------------------------------------------------------------- discovery

def test_discover() -> None:
    print("\ndiscovery")
    media = [{"path": f"/c/Course/lecture_{i:02d}.mp4", "name": f"lecture_{i:02d}.mp4",
              "dir": "/c/Course", "ext": ".mp4", "bytes": 800_000_000, "mtime": 0}
             for i in range(1, 7)]
    media.append({"path": "/c/stock/clip.mp4", "name": "clip.mp4", "dir": "/c/stock",
                  "ext": ".mp4", "bytes": 10_000_000, "mtime": 0})
    ranked = rank_folders(media, [])
    check("course folder ranks first", ranked[0]["dir"] == "/c/Course")
    check("stock folder is penalised", ranked[-1]["score"] < 0)
    check("sequential naming detected", ranked[0]["sequential_naming"])


# --------------------------------------------------------------------- bank

def test_bank(cfg: Config) -> dict:
    print("\ncontent bank")
    b = bank.build(cfg)
    texts = [c["text"] for c in b["clips"]]
    check("bank has clips", b["clip_count"] > 0)
    check("greetings never enter the bank",
          not any(lx.starts_with_greeting(t) for t in texts))
    check("filler line rejected", not any("ইয়ে বুঝলেন" in t for t in texts))
    check("every category key present",
          set(b["category_counts"]) == set(lx.CATEGORIES))
    check("CTA clip found", b["category_counts"]["CTA"] > 0)
    check("AUTHORITY clip found", b["category_counts"]["AUTHORITY"] > 0)
    check("low-confidence segment flagged for review", len(b["needs_review"]) > 0)
    check("every clip traces to a source and timestamp",
          all(c["source"] and c["duration"] > 0 for c in b["clips"]))
    check("query filters by category",
          all("PROBLEM" in c["categories"]
              for c in bank.query(b, category="PROBLEM", top=5)))
    check("query respects duration bounds",
          all(2.0 <= c["duration"] <= 4.0
              for c in bank.query(b, min_dur=2.0, max_dur=4.0, top=20)))
    return b


# ----------------------------------------------------------------- timeline

def test_timeline(cfg: Config, b: dict) -> dict:
    print("\ntimeline / attention engine")
    tl = timeline.build(b, cfg, concept="A", target=30)
    shots = tl["shots"]
    durs = [s["dur"] for s in shots]

    check("timeline has shots", len(shots) > 0)
    check("shot lengths are NOT mechanical (RULE 5)", pstdev(durs) > 0.22,
          f"sd={pstdev(durs):.3f}")
    check("no shot below the floor",
          min(durs) >= cfg.get("attention.min_shot") - 0.01, f"min={min(durs):.2f}")
    check("every shot records a reason (RULE 6)", all(s["reason"] for s in shots))
    check("shots are contiguous with no gaps",
          all(abs(shots[i]["t_out"] - shots[i + 1]["t_in"]) < 1e-6
              for i in range(len(shots) - 1)))
    check("source windows stay inside their clip",
          all(s["src_out"] > s["src_in"] for s in shots))
    check("promo does not open on a greeting (STEP 7)",
          not lx.starts_with_greeting(shots[0]["text"]))
    check("at most one statement card (STEP 10)",
          sum(1 for s in shots if s["treatment"] == "TEXT_CARD") <= 1)
    check("no card inside the first 2s",
          all(s["t_in"] >= 2.0 for s in shots if s["treatment"] == "TEXT_CARD"))
    check("emphasis word is present in its own shot",
          all(any(lx.normalize(w["w"]).strip("।॥.,!?;:\"'()[]") == s["emphasis"]
                  for w in s["words"])
              for s in shots if s["emphasis"]))
    check("early shots are tighter than late shots",
          (sum(s["dur"] for s in shots if s["t_in"] < 8) / max(1, sum(1 for s in shots if s["t_in"] < 8)))
          <= (sum(s["dur"] for s in shots if s["t_in"] >= 8) / max(1, sum(1 for s in shots if s["t_in"] >= 8))) + 0.01)
    check("concepts score differently",
          len({round(timeline.score_concept(timeline.build(b, cfg, concept=k, target=30)), 3)
               for k in "ABC"}) > 1)
    check("underfill is reported honestly",
          timeline.build(b, cfg, concept="A", target=120)["underfilled"])
    return tl


# ---------------------------------------------------------------- subtitles

def test_subtitles(cfg: Config, tl: dict) -> None:
    print("\nsubtitles")
    ass = subtitles.build_ass(tl["shots"], cfg)
    events = [l for l in ass.splitlines() if l.startswith("Dialogue")]
    check("ASS has a style block", "[V4+ Styles]" in ass and "Style: Caption" in ass)
    check("captions were generated", len(events) > 0)
    check("Bengali font requested", "Noto Sans Bengali" in ass)
    check("PlayRes matches output",
          f"PlayResX: {cfg.get('output.width')}" in ass)
    margin = int(cfg.get("output.height") * cfg.get("safe_area.bottom_pct"))
    check("captions clear the platform UI band", f",{margin + int(cfg.get('output.height') * 0.02)},1" in ass,
          "MarginV not inside safe area")
    check("emphasis colour used at least once",
          cfg.get("subtitles.emphasis") in ass)

    chunks = subtitles.chunk_words(
        [{"w": f"w{i}", "start": i * 0.3, "end": i * 0.3 + 0.3} for i in range(20)],
        max_words=4, max_chars=26, max_dur=1.8)
    check("chunks respect the word ceiling", all(len(c["words"]) <= 4 for c in chunks))
    check("chunks respect the duration ceiling",
          all(c["end"] - c["start"] <= 1.81 for c in chunks))

    srt = subtitles.build_srt(tl["shots"], cfg)
    check("SRT companion generated", "-->" in srt)


# ------------------------------------------------------------------- render

def test_render(cfg: Config) -> None:
    print("\nrender geometry")
    W, H = cfg.get("output.width"), cfg.get("output.height")
    for (sw, sh, label) in [(1920, 1080, "16:9"), (3840, 2160, "4K"),
                            (1080, 1920, "vertical"), (1080, 1080, "square")]:
        c = render.crop_only(sw, sh, cfg, 1.0, (0.5, 0.42))
        dims = c.split("=")[1].split(":")
        cw, ch, x, y = (int(v) for v in dims)
        check(f"{label}: crop is 9:16", abs(cw / ch - W / H) < 0.01, f"{cw}x{ch}")
        check(f"{label}: crop fits inside the source",
              cw <= sw and ch <= sh and x + cw <= sw and y + ch <= sh)
        check(f"{label}: even dimensions (H.264)", cw % 2 == 0 and ch % 2 == 0)

    tight = render.crop_only(1920, 1080, cfg, 1.35, (0.5, 0.42))
    wide = render.crop_only(1920, 1080, cfg, 1.0, (0.5, 0.42))
    check("punch-in crops a smaller region",
          int(tight.split("=")[1].split(":")[0]) < int(wide.split("=")[1].split(":")[0]))

    shot = {"dur": 1.4, "src_in": 12.5, "source": "/x/a.mp4", "punch": 1.22,
            "focus": [0.5, 0.42], "treatment": "PUNCH_CLOSE", "transition": "PUSH"}
    cmd = render.segment_cmd(shot, {"width": 1920, "height": 1080}, cfg,
                             Path("/tmp/x.mkv"), motion=False)
    check("segment seeks accurately", "-accurate_seek" in cmd)
    check("segment fades audio at the cut (no clicks)",
          "afade=t=in" in " ".join(cmd) and "afade=t=out" in " ".join(cmd))
    check("segments share a uniform codec for concat",
          "pcm_s16le" in cmd and "libx264" in cmd)

    m = render.master_cmd(Path("/tmp/c.txt"), Path("/tmp/s.ass"), cfg, Path("/tmp/o.mp4"))
    joined = " ".join(m)
    check("master burns subtitles", "subtitles=" in joined)
    check("master normalises loudness", "loudnorm=I=-14.0" in joined)
    check("master is mobile-streamable", "+faststart" in joined)

    cfg2 = Config()
    cfg2.data["work_dir"] = cfg.data["work_dir"]
    cfg2.data["audio"]["music_bed"] = "/x/bed.mp3"
    mm = " ".join(render.master_cmd(Path("/tmp/c.txt"), None, cfg2, Path("/tmp/o.mp4"),
                                    music="/x/bed.mp3"))
    check("music ducks under the voice (RULE 8)", "sidechaincompress" in mm)


# -------------------------------------------------------------------- audit

def test_audit(cfg: Config, tl: dict, b: dict) -> None:
    print("\naudit")
    rep = audit.audit(tl, cfg, b)
    check("audit runs and scores", 0.0 <= rep["score"] <= 1.0)
    check("real timeline is not blocked", rep["verdict"] != "blocked", rep["verdict"])

    shots = [dict(tl["shots"][0], t_in=i * 2.0, t_out=i * 2.0 + 2.0, dur=2.0,
                  reason="", treatment="WIDE") for i in range(8)]
    bad = dict(tl, shots=shots, duration=16.0, missing_beats=[],
               beats=[{"beat": "HOOK", "missing": False,
                       "text": "আসসালামু আলাইকুম, আজকে আমরা শুরু করব।",
                       "scores": {"hook_power": 0.1, "value": 0.1,
                                  "curiosity": 0.1, "composite": 0.2}}])
    rbad = audit.audit(bad, cfg)
    checks = {f["check"] for f in rbad["findings"] if f["severity"] == "FAIL"}
    check("metronome cutting is caught",
          any("mechanical" in c for c in checks), str(checks))
    check("greeting opener is caught", any("boilerplate" in c for c in checks))
    check("unjustified cuts are caught", any("reason" in c for c in checks))
    check("bad timeline is blocked", rbad["verdict"] == "blocked")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cfg = fixture_cfg(tmp)
        test_lexicon()
        test_scoring()
        test_discover()
        b = test_bank(cfg)
        tl = test_timeline(cfg, b)
        test_subtitles(cfg, tl)
        test_render(cfg)
        test_audit(cfg, tl, b)

    print(f"\n{'=' * 56}\n{len(PASS)} passed, {len(FAIL)} failed")
    for f in FAIL:
        print(f"  FAILED: {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
