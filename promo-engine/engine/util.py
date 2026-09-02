"""Small shared helpers: process running, JSON IO, timecodes."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


class ToolMissing(RuntimeError):
    pass


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def require(tool: str, hint: str = "") -> str:
    path = shutil.which(tool)
    if not path:
        raise ToolMissing(f"required tool not found on PATH: {tool}" + (f"\n  {hint}" if hint else ""))
    return path


def run(cmd: list[str], *, capture: bool = True, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a command. Never shell=True -- paths with spaces/quotes are common in media libraries."""
    return subprocess.run(
        [str(c) for c in cmd],
        capture_output=capture,
        text=True,
        check=check,
        cwd=str(cwd) if cwd else None,
    )


def read_json(path: Path, default=None):
    p = Path(path)
    if not p.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"missing: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def write_text(path: Path, text: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def tc(seconds: float, *, ms: bool = True) -> str:
    """Seconds -> HH:MM:SS.mmm (ms=False gives HH:MM:SS)."""
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if ms:
        return f"{h:02d}:{m:02d}:{s:06.3f}"
    return f"{h:02d}:{m:02d}:{int(s):02d}"


def short_tc(seconds: float) -> str:
    """Seconds -> MM:SS.s for promo-relative timelines."""
    seconds = max(0.0, float(seconds))
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:04.1f}"


def even(n: float) -> int:
    """Nearest even int -- H.264 chroma subsampling requires even dimensions."""
    i = int(round(n))
    return i - (i % 2)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def eprint(*a) -> None:
    print(*a, file=sys.stderr)
