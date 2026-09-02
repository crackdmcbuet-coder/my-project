"""STEP 1 -- locate course source media.

Never assumes a folder is known. Scans configured roots (or sensible defaults for
the host OS), groups candidates into likely course folders, and ranks them so the
strongest source set can be chosen deliberately rather than guessed.
"""
from __future__ import annotations

import fnmatch
import os
import platform
import re
from collections import defaultdict
from pathlib import Path

from .config import Config
from .util import write_json

COURSE_HINTS = [
    "course", "lecture", "class", "lesson", "module", "batch", "recording",
    "screen", "session", "seminar", "workshop", "training", "tutorial",
    "কোর্স", "ক্লাস", "লেকচার", "ব্যাচ", "রেকর্ড",
]
NEGATIVE_HINTS = ["sample", "template", "stock", "music", "sfx", "render", "export", "proxy", "backup"]

_SEQ_RE = re.compile(r"(?:^|[^0-9])(\d{1,3})(?:[^0-9]|$)")


def default_roots() -> list[Path]:
    home = Path.home()
    sysname = platform.system()
    cands = [home / "Desktop", home / "Documents", home / "Videos", home / "Movies", home / "Downloads"]
    if sysname == "Darwin":
        cands += [home / "Movies"]
    elif sysname == "Windows":
        cands += [home / "Videos", Path("D:/"), Path("E:/")]
    else:
        cands += [Path("/media"), Path("/mnt")]
    return [c for c in cands if c.exists()]


def _excluded(path: Path, patterns: list[str]) -> bool:
    s = str(path)
    return any(fnmatch.fnmatch(s, pat) for pat in patterns)


def scan(cfg: Config, roots: list[str] | None = None, max_depth: int = 6) -> dict:
    exts = {e.lower() for e in cfg.get("sources.extensions", [])}
    still_exts = {e.lower() for e in cfg.get("sources.still_extensions", [])}
    excl = cfg.get("sources.exclude_globs", [])
    min_bytes = cfg.get("sources.min_bytes", 0)

    root_paths = [Path(r).expanduser() for r in (roots or cfg.get("sources.roots") or [])]
    if not root_paths:
        root_paths = default_roots()
    root_paths = [r for r in root_paths if r.exists()]

    media: list[dict] = []
    stills: list[dict] = []
    seen: set[str] = set()

    for root in root_paths:
        base_depth = len(root.resolve().parts)
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            d = Path(dirpath)
            if len(d.resolve().parts) - base_depth >= max_depth:
                dirnames[:] = []
                continue
            dirnames[:] = [n for n in dirnames
                           if not n.startswith(".") and not _excluded(d / n, excl)]
            for fn in filenames:
                p = d / fn
                ext = p.suffix.lower()
                if ext not in exts and ext not in still_exts:
                    continue
                if _excluded(p, excl):
                    continue
                try:
                    st = p.stat()
                    real = str(p.resolve())
                except OSError:
                    continue
                if real in seen:
                    continue
                seen.add(real)
                rec = {"path": real, "name": p.name, "dir": str(p.parent),
                       "ext": ext, "bytes": st.st_size, "mtime": st.st_mtime}
                if ext in still_exts:
                    stills.append(rec)
                elif st.st_size >= min_bytes:
                    media.append(rec)

    return {
        "roots_scanned": [str(r) for r in root_paths],
        "media": sorted(media, key=lambda r: r["path"]),
        "stills": sorted(stills, key=lambda r: r["path"]),
        "candidates": rank_folders(media, stills),
    }


def rank_folders(media: list[dict], stills: list[dict]) -> list[dict]:
    """Group media by directory and score each as a candidate course folder.

    Signals: how much footage lives there, total runtime proxy (bytes), whether the
    path names read like a course, and whether filenames form a numbered sequence
    (lecture_01, lecture_02 ... is a very strong course signal).
    """
    by_dir: dict[str, list[dict]] = defaultdict(list)
    for rec in media:
        by_dir[rec["dir"]].append(rec)
    stills_by_dir: dict[str, int] = defaultdict(int)
    for rec in stills:
        stills_by_dir[rec["dir"]] += 1

    out = []
    for d, items in by_dir.items():
        low = d.lower()
        name_hits = sum(1 for h in COURSE_HINTS if h in low)
        name_hits += sum(1 for h in COURSE_HINTS
                         if any(h in i["name"].lower() for i in items))
        neg = sum(1 for h in NEGATIVE_HINTS if h in low)

        seq = {int(m.group(1)) for i in items for m in [_SEQ_RE.search(i["name"])] if m}
        sequential = len(seq) >= 3 and (max(seq) - min(seq)) <= len(seq) * 3

        total_gb = sum(i["bytes"] for i in items) / 1e9
        score = (
            min(len(items), 40) * 1.5
            + min(total_gb, 50) * 2.0
            + min(name_hits, 8) * 4.0
            + (10.0 if sequential else 0.0)
            + min(stills_by_dir.get(d, 0), 10) * 0.5
            - neg * 6.0
        )
        out.append({
            "dir": d,
            "file_count": len(items),
            "total_gb": round(total_gb, 2),
            "still_count": stills_by_dir.get(d, 0),
            "name_hits": name_hits,
            "sequential_naming": sequential,
            "score": round(score, 2),
        })
    return sorted(out, key=lambda r: -r["score"])


def run(cfg: Config, roots: list[str] | None = None) -> dict:
    cfg.ensure_dirs()
    result = scan(cfg, roots)
    write_json(cfg.dir_index / "discovered.json", result)
    return result
