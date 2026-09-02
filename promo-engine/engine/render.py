"""STEP 9/14/16/22 -- turn a timeline into ffmpeg work.

Two stages, deliberately:
  1. each shot -> an intermediate segment (cached, uniform codec params)
  2. concat -> subtitle burn-in -> loudness normalisation -> music bed -> master

One giant filtergraph is fragile and uncacheable; two stages let a single bad
shot be re-rendered without redoing the promo.

Camera movement: the STATIC path (a fixed crop per shot) is the default because
it is correct on every ffmpeg build. `motion=True` adds a real push using
zoompan, which is worth having but is build-sensitive -- `promo doctor` tests
both on the target machine and reports which to use.
"""
from __future__ import annotations

import shlex
from pathlib import Path

from .config import Config
from .util import clamp, even, have, require, run, write_text


# ------------------------------------------------------------------ geometry


def crop_only(src_w: int, src_h: int, cfg: Config, punch: float,
              focus: tuple[float, float]) -> str | None:
    """The crop rectangle alone, at source resolution. None if the size is unknown."""
    W, H = cfg.get("output.width"), cfg.get("output.height")
    if src_w <= 0 or src_h <= 0:
        return None
    target = W / H

    # Largest region of the source matching the output aspect.
    if src_w / src_h > target:
        ch, cw = src_h, src_h * target
    else:
        cw, ch = src_w, src_w / target

    z = max(1.0, float(punch))
    cw, ch = cw / z, ch / z
    cw, ch = even(min(cw, src_w)), even(min(ch, src_h))

    fx, fy = focus
    x = even(clamp(fx * (src_w - cw), 0, max(0, src_w - cw)))
    y = even(clamp(fy * (src_h - ch), 0, max(0, src_h - ch)))
    return f"crop={cw}:{ch}:{x}:{y}"


def crop_chain(src_w: int, src_h: int, cfg: Config, punch: float,
               focus: tuple[float, float]) -> str:
    """Fixed crop -> output size. Handles landscape, square and vertical sources."""
    W, H = cfg.get("output.width"), cfg.get("output.height")
    c = crop_only(src_w, src_h, cfg, punch, focus)
    if c is None:
        return f"scale={W}:{H}"
    return f"{c},scale={W}:{H}:flags=lanczos,setsar=1"


def motion_chain(src_w: int, src_h: int, cfg: Config, punch: float,
                 focus: tuple[float, float], dur: float, push: bool) -> str:
    """Slow push using zoompan. `d=1` + explicit fps is what makes zoompan work on
    video rather than on a single still."""
    W, H = cfg.get("output.width"), cfg.get("output.height")
    fps = cfg.get("output.fps")
    z0 = 1.0 if push else float(punch)
    z1 = float(punch) if push else float(punch) * 1.06
    frames = max(1, int(round(dur * fps)))
    fx, fy = focus
    # Crop at SOURCE resolution and let zoompan do the only scale to output size --
    # cropping, scaling, then zooming would resample the picture twice.
    base = crop_only(src_w, src_h, cfg, 1.0, focus)
    prefix = f"{base}," if base else ""
    zexpr = f"{z0:.4f}+{z1 - z0:.4f}*on/{frames}"
    return (f"{prefix}zoompan=z='{zexpr}'"
            f":x='(iw-iw/zoom)*{fx:.3f}':y='(ih-ih/zoom)*{fy:.3f}'"
            f":d=1:s={W}x{H}:fps={fps},setsar=1")


def treatment_filters(shot: dict, src: dict, cfg: Config, *, motion: bool) -> str:
    """Full per-shot video chain, including the treatment's own look."""
    fps = cfg.get("output.fps")
    sw, sh = int(src.get("width") or 0), int(src.get("height") or 0)
    focus = tuple(shot.get("focus") or (0.5, 0.42))
    punch = float(shot.get("punch") or 1.0)
    push = shot.get("transition") == "PUSH" or shot["treatment"] in ("PUNCH_MED", "PUNCH_CLOSE")

    if motion:
        geom = motion_chain(sw, sh, cfg, punch, focus, shot["dur"], push)
    else:
        geom = crop_chain(sw, sh, cfg, punch, focus)

    chain = [f"fps={fps}", geom]

    if shot["treatment"] == "TEXT_CARD":
        # The card sits on the speaker's own footage, blurred and pushed down --
        # so it still feels like this course, not a stock template (STEP 13).
        chain.append("gblur=sigma=28,eq=brightness=-0.16:saturation=0.75")
    elif shot["treatment"] == "KEYWORD_POP":
        chain.append("eq=contrast=1.04:saturation=1.03")

    # STEP 16: gentle, consistent, no heavy LUT.
    chain.append("eq=contrast=1.02:saturation=1.02:gamma=1.01")
    chain.append("format=yuv420p")
    return ",".join(chain)


# ------------------------------------------------------------------- stage 1


def segment_cmd(shot: dict, src: dict, cfg: Config, out: Path, *, motion: bool) -> list[str]:
    dur = round(shot["dur"], 3)
    fade = min(0.012, dur / 4)          # kill the click at every cut point
    vf = treatment_filters(shot, src, cfg, motion=motion)
    af = (f"atrim=0:{dur},asetpts=N/SR/TB,aresample=48000,"
          f"afade=t=in:st=0:d={fade:.3f},afade=t=out:st={max(0.0, dur - fade):.3f}:d={fade:.3f}")
    return [
        "ffmpeg", "-y", "-hide_banner", "-nostdin", "-loglevel", "error",
        "-accurate_seek", "-ss", f"{shot['src_in']:.3f}", "-t", f"{dur}",
        "-i", shot["source"],
        "-filter_complex", f"[0:v]{vf}[v];[0:a]{af}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
        "-pix_fmt", "yuv420p", "-r", str(cfg.get("output.fps")),
        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
        str(out),
    ]


# ------------------------------------------------------------------- stage 2


def master_cmd(concat_list: Path, ass: Path | None, cfg: Config, out: Path,
               *, music: str | None = None) -> list[str]:
    W, H = cfg.get("output.width"), cfg.get("output.height")
    lufs = cfg.get("audio.target_lufs", -14.0)
    tp = cfg.get("audio.true_peak", -1.5)
    duck = cfg.get("audio.music_duck_db", -16.0)

    cmd = ["ffmpeg", "-y", "-hide_banner", "-nostdin", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", str(concat_list)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]

    vchain = f"[0:v]scale={W}:{H},setsar=1"
    if ass:
        # ASS carries its own PlayRes, so burn after the final scale.
        vchain += f",subtitles={_escape_filter_path(ass)}"
    vchain += "[v]"

    if music:
        # STEP 15 / RULE 8: music never competes with the voice. Sidechain ducking
        # keyed on the voice itself, plus a fixed attenuation floor.
        achain = (
            f"[0:a]aformat=channel_layouts=stereo,asplit=2[voice][key];"
            f"[1:a]aformat=channel_layouts=stereo,volume={duck}dB[mus];"
            f"[mus][key]sidechaincompress=threshold=0.05:ratio=8:attack=8:release=320[ducked];"
            f"[voice][ducked]amix=inputs=2:duration=first:dropout_transition=0:weights=1 0.55,"
            f"loudnorm=I={lufs}:TP={tp}:LRA=9[a]"
        )
    else:
        achain = f"[0:a]loudnorm=I={lufs}:TP={tp}:LRA=9[a]"

    cmd += ["-filter_complex", f"{vchain};{achain}",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", str(cfg.get("output.preset")),
            "-crf", str(cfg.get("output.crf")), "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-level", "4.1",
            "-r", str(cfg.get("output.fps")),
            "-c:a", "aac", "-b:a", str(cfg.get("output.audio_bitrate")), "-ar", "48000",
            "-movflags", "+faststart", str(out)]
    return cmd


def _escape_filter_path(p: Path) -> str:
    """ffmpeg filter args need ':' and '\\' escaped, and the whole thing quoted."""
    s = str(p).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    return f"'{s}'"


# --------------------------------------------------------------------- driver


def render(timeline: dict, cfg: Config, out_path: Path, *,
           ass_path: Path | None = None, motion: bool = False,
           dry_run: bool = False, sources: dict | None = None) -> dict:
    from .util import read_json
    cfg.ensure_dirs()
    if sources is None:
        lib = read_json(cfg.dir_index / "library.json", default={"files": []})
        sources = {str(Path(f["path"]).resolve()): f for f in lib.get("files", [])}

    seg_dir = cfg.dir_cache / timeline["label"]
    seg_dir.mkdir(parents=True, exist_ok=True)
    cmds: list[list[str]] = []
    seg_files: list[Path] = []

    for i, shot in enumerate(timeline["shots"]):
        src = sources.get(str(Path(shot["source"]).resolve()), {})
        seg = seg_dir / f"shot_{i:03d}.mkv"
        seg_files.append(seg)
        cmds.append(segment_cmd(shot, src, cfg, seg, motion=motion))

    listing = "\n".join(f"file {shlex.quote(str(s.resolve()))}" for s in seg_files) + "\n"
    list_path = seg_dir / "concat.txt"

    master = master_cmd(list_path, ass_path, cfg, out_path,
                        music=cfg.get("audio.music_bed"))

    script = "\n".join(["#!/usr/bin/env bash", "set -euo pipefail", ""] +
                       [" ".join(shlex.quote(c) for c in cmd) for cmd in cmds] +
                       ["", " ".join(shlex.quote(c) for c in master), ""])
    script_path = seg_dir / "render.sh"
    write_text(script_path, script)
    script_path.chmod(0o755)

    result = {"segments": len(cmds), "script": str(script_path),
              "concat_list": str(list_path), "output": str(out_path),
              "motion": motion, "executed": False}
    if dry_run:
        return result

    require("ffmpeg", "install ffmpeg, then re-run (or use --dry-run to inspect commands)")
    write_text(list_path, listing)
    for i, cmd in enumerate(cmds):
        print(f"  shot {i + 1}/{len(cmds)}")
        cp = run(cmd, check=False)
        if cp.returncode != 0:
            raise RuntimeError(f"shot {i} failed:\n{cp.stderr.strip()[:800]}\n"
                               f"cmd: {' '.join(shlex.quote(c) for c in cmd)}")
    print("  mastering")
    cp = run(master, check=False)
    if cp.returncode != 0:
        raise RuntimeError(f"master failed:\n{cp.stderr.strip()[:800]}")
    result["executed"] = True
    return result


# ---------------------------------------------------------------- self-test


def doctor(cfg: Config) -> dict:
    """Verify on THIS machine that the filtergraphs actually run, and whether the
    motion path is usable. Run once per machine before the first real render."""
    report: dict = {"ffmpeg": have("ffmpeg"), "ffprobe": have("ffprobe")}
    if not report["ffmpeg"]:
        report["verdict"] = "ffmpeg missing -- install it first"
        return report

    tmp = cfg.dir_cache / "_doctor"
    tmp.mkdir(parents=True, exist_ok=True)
    probe_src = tmp / "src.mkv"
    gen = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "lavfi", "-i", "testsrc2=size=1920x1080:rate=30:duration=3",
           "-f", "lavfi", "-i", "sine=frequency=300:duration=3",
           "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
           "-c:a", "pcm_s16le", str(probe_src)]
    report["synth_source"] = run(gen, check=False).returncode == 0
    if not report["synth_source"]:
        report["verdict"] = "could not synthesise a test clip -- check the ffmpeg build"
        return report

    src = {"width": 1920, "height": 1080}
    shot = {"dur": 2.0, "src_in": 0.2, "source": str(probe_src), "punch": 1.22,
            "focus": [0.5, 0.42], "treatment": "PUNCH_CLOSE", "transition": "PUSH"}

    for mode in ("static", "motion"):
        out = tmp / f"seg_{mode}.mkv"
        cmd = segment_cmd(shot, src, cfg, out, motion=(mode == "motion"))
        cp = run(cmd, check=False)
        report[f"{mode}_ok"] = cp.returncode == 0
        if cp.returncode != 0:
            report[f"{mode}_error"] = cp.stderr.strip()[-400:]

    # Subtitle burn-in needs libass compiled in; check separately.
    ass = tmp / "t.ass"
    from .subtitles import _style_block
    write_text(ass, _style_block(cfg) +
               "Dialogue: 0,0:00:00.00,0:00:01.00,Caption,,0,0,0,,test\n")
    if report.get("static_ok"):
        lst = tmp / "c.txt"
        write_text(lst, f"file {shlex.quote(str((tmp / 'seg_static.mkv').resolve()))}\n")
        cp = run(master_cmd(lst, ass, cfg, tmp / "master.mp4"), check=False)
        report["subtitles_ok"] = cp.returncode == 0
        if cp.returncode != 0:
            report["subtitles_error"] = cp.stderr.strip()[-400:]

    report["recommended_motion"] = bool(report.get("motion_ok"))
    ok = report.get("static_ok") and report.get("subtitles_ok")
    report["verdict"] = ("ready" if ok else
                         "static or subtitle path failed -- see errors above")
    return report
