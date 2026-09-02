"""STEP 2 -- technical inspection of every source file via ffprobe/ffmpeg.

Produces the source library: duration, resolution, fps, audio quality, plus a
measured loudness profile used later for audio-quality scoring and for
normalisation targets.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .config import Config
from .util import require, run, write_json, read_json


def ffprobe(path: str | Path) -> dict:
    exe = require("ffprobe", "install ffmpeg (brew install ffmpeg / apt install ffmpeg)")
    cp = run([exe, "-v", "error", "-print_format", "json",
              "-show_format", "-show_streams", str(path)], check=False)
    if cp.returncode != 0:
        return {"error": (cp.stderr or "").strip()[:400]}
    try:
        return json.loads(cp.stdout)
    except json.JSONDecodeError as e:
        return {"error": f"unparseable ffprobe output: {e}"}


def _fps(stream: dict) -> float:
    for key in ("avg_frame_rate", "r_frame_rate"):
        val = stream.get(key) or ""
        if "/" in val:
            num, den = val.split("/", 1)
            try:
                num, den = float(num), float(den)
            except ValueError:
                continue
            if den:
                return round(num / den, 3)
    return 0.0


_LOUDNORM_KEYS = ("input_i", "input_tp", "input_lra", "input_thresh")


def measure_loudness(path: str | Path, *, sample_seconds: float = 180.0) -> dict:
    """EBU R128 stats from the first N seconds. Cheap proxy for audio quality."""
    exe = require("ffmpeg")
    cp = run([exe, "-nostdin", "-hide_banner", "-t", str(sample_seconds), "-i", str(path),
              "-map", "0:a:0?", "-af", "loudnorm=print_format=json",
              "-f", "null", "-"], check=False)
    text = (cp.stderr or "") + (cp.stdout or "")
    blocks = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", text, re.S)
    if not blocks:
        return {}
    try:
        data = json.loads(blocks[-1])
    except json.JSONDecodeError:
        return {}
    out = {}
    for k in _LOUDNORM_KEYS:
        try:
            out[k] = float(data[k])
        except (KeyError, TypeError, ValueError):
            pass
    return out


def audio_quality_score(loud: dict, astream: dict | None) -> float:
    """0..1. Rewards healthy level, controlled peaks, and a sane dynamic range."""
    if not loud and not astream:
        return 0.0
    score = 0.5
    i = loud.get("input_i")
    if i is not None:
        # -12..-24 LUFS is comfortable spoken-word territory.
        score += 0.25 if -26.0 <= i <= -10.0 else -0.2
        if i < -35.0:
            score -= 0.2           # very quiet -> noisy once normalised
    tp = loud.get("input_tp")
    if tp is not None:
        score += 0.15 if tp <= -0.5 else -0.25   # clipped source
    lra = loud.get("input_lra")
    if lra is not None:
        if 3.0 <= lra <= 14.0:
            score += 0.1
        elif lra > 20.0:
            score -= 0.15          # wildly inconsistent
    if astream:
        try:
            if int(astream.get("sample_rate", 0)) >= 44100:
                score += 0.05
        except (TypeError, ValueError):
            pass
    return max(0.0, min(1.0, score))


def visual_quality_score(vstream: dict | None) -> float:
    """0..1 from resolution and frame rate. A 4K 60fps lecture crops to 9:16 far
    better than a 720p 24fps one."""
    if not vstream:
        return 0.0
    h = int(vstream.get("height") or 0)
    w = int(vstream.get("width") or 0)
    fps = _fps(vstream)
    short_side = min(w, h) or 0
    if short_side >= 2000:
        s = 1.0
    elif short_side >= 1400:
        s = 0.9
    elif short_side >= 1000:
        s = 0.75
    elif short_side >= 700:
        s = 0.5
    else:
        s = 0.25
    if fps >= 50:
        s = min(1.0, s + 0.05)
    elif fps and fps < 24:
        s -= 0.1
    return max(0.0, min(1.0, s))


def inspect(path: str | Path, *, loudness: bool = True) -> dict:
    p = Path(path)
    meta = ffprobe(p)
    if "error" in meta:
        return {"path": str(p), "name": p.name, "error": meta["error"], "usable": False}

    fmt = meta.get("format", {})
    vs = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), None)
    as_ = next((s for s in meta.get("streams", []) if s.get("codec_type") == "audio"), None)
    loud = measure_loudness(p) if (loudness and as_) else {}

    try:
        duration = float(fmt.get("duration") or 0.0)
    except (TypeError, ValueError):
        duration = 0.0

    rec = {
        "path": str(p),
        "name": p.name,
        "duration": round(duration, 3),
        "bytes": int(fmt.get("size") or 0),
        "container": fmt.get("format_name"),
        "has_video": vs is not None,
        "has_audio": as_ is not None,
        "width": int(vs.get("width")) if vs else 0,
        "height": int(vs.get("height")) if vs else 0,
        "fps": _fps(vs) if vs else 0.0,
        "vcodec": vs.get("codec_name") if vs else None,
        "acodec": as_.get("codec_name") if as_ else None,
        "sample_rate": int(as_.get("sample_rate") or 0) if as_ else 0,
        "channels": int(as_.get("channels") or 0) if as_ else 0,
        "loudness": loud,
    }
    rec["audio_quality"] = round(audio_quality_score(loud, as_), 3)
    rec["visual_quality"] = round(visual_quality_score(vs), 3)
    # Usable as promo source: has speech to cut on, and is long enough to matter.
    rec["usable"] = bool(as_) and duration >= 5.0
    if not as_:
        rec["flag"] = "no audio stream -- cannot be transcribed or used for A-roll"
    elif duration < 5.0:
        rec["flag"] = "under 5s -- treated as B-roll/insert only"
    return rec


def run_probe(cfg: Config, paths: list[str] | None = None, *, loudness: bool = True) -> dict:
    cfg.ensure_dirs()
    if paths is None:
        disc = read_json(cfg.dir_index / "discovered.json", default={"media": []})
        paths = [m["path"] for m in disc.get("media", [])]
    out = []
    for i, p in enumerate(paths, 1):
        print(f"  [{i}/{len(paths)}] probing {Path(p).name}")
        out.append(inspect(p, loudness=loudness))
    lib = {"count": len(out), "files": out}
    write_json(cfg.dir_index / "library.json", lib)
    return lib
