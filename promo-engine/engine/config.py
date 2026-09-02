"""Project configuration. Everything tunable lives here so the engine is not hardcoded
to one course, one language, or one aspect ratio."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .util import read_json

# ---------------------------------------------------------------- defaults

DEFAULTS: dict = {
    "project_name": "course-promo",
    # STEP 1 -- where to look for footage. Absolute paths on the machine that holds it.
    "sources": {
        "roots": [],
        "extensions": [".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm",
                       ".wav", ".mp3", ".m4a", ".aac", ".flac"],
        "still_extensions": [".png", ".jpg", ".jpeg", ".webp"],
        "exclude_globs": ["**/node_modules/**", "**/.git/**", "**/Trash/**",
                          "**/cache/**", "**/*proxy*"],
        "min_bytes": 262144,
    },
    "work_dir": "promo_work",
    # STEP 11 -- language of the spoken source. "bn" for Bengali, "en", or "auto".
    "language": "auto",
    "transcribe": {
        "model": "large-v3",
        "device": "auto",
        "compute_type": "auto",
        "vad": True,
        "beam_size": 5,
    },
    # STEP 22 -- mobile-first delivery
    "output": {
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "audio_bitrate": "192k",
        "crf": 19,
        "preset": "slow",
    },
    # Reels/Shorts UI overlays. Nothing important is placed inside these bands.
    "safe_area": {"top_pct": 0.10, "bottom_pct": 0.20, "side_pct": 0.06},
    "subtitles": {
        "font": "Noto Sans Bengali",
        "font_fallback": "Noto Sans",
        "size_pct": 0.052,
        "max_words": 4,
        "max_chars": 26,
        "max_dur": 1.8,
        "primary": "&H00FFFFFF",
        "emphasis": "&H0034D9FF",
        "outline": 4,
        "shadow": 1,
    },
    # STEP 8/9 -- the attention engine.
    "attention": {
        "min_shot": 0.5,
        "max_shot": 3.2,
        "hero_shot": 4.5,
        "early_budget": 1.6,
        "late_budget": 2.6,
        "early_window": 8.0,
        "punch_levels": [1.0, 1.12, 1.22, 1.35],
        "max_same_source_run": 2.0,
    },
    # STEP 13 -- B-roll policy: own material first, always.
    "broll": {"allow_external": False, "external_dir": None},
    "audio": {
        "target_lufs": -14.0,
        "true_peak": -1.5,
        "music_duck_db": -16.0,
        "music_bed": None,
        "sfx_dir": None,
    },
    "cta": {"text": None, "sub": None},
    # Text the engine may render on screen that is NOT spoken in the footage
    # (e.g. the course name). Empty = spoken transcript text only.
    "approved_claims": [],
    "versions": [
        {"id": "01_FINAL_PROMO_30S", "target": 30, "concept": "auto"},
        {"id": "02_FINAL_PROMO_45S", "target": 45, "concept": "auto"},
        {"id": "03_FINAL_PROMO_60S", "target": 60, "concept": "auto"},
    ],
}


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


@dataclass
class Config:
    data: dict = field(default_factory=lambda: _deep_merge(DEFAULTS, {}))
    path: Path | None = None

    @classmethod
    def load(cls, path: str | Path | None) -> "Config":
        if path is None:
            for cand in ("promo.config.json", "promo-engine/promo.config.json"):
                if Path(cand).exists():
                    path = cand
                    break
        if path is None:
            return cls()
        p = Path(path)
        return cls(data=_deep_merge(DEFAULTS, read_json(p)), path=p)

    def __getitem__(self, key: str):
        return self.data[key]

    def get(self, dotted: str, default=None):
        cur = self.data
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    @property
    def work(self) -> Path:
        return Path(self.data["work_dir"])

    # Canonical work-dir layout. Originals are never written to (RULE 12).
    @property
    def dir_index(self) -> Path:
        return self.work / "01_index"

    @property
    def dir_transcripts(self) -> Path:
        return self.work / "02_transcripts"

    @property
    def dir_bank(self) -> Path:
        return self.work / "03_bank"

    @property
    def dir_timelines(self) -> Path:
        return self.work / "04_timelines"

    @property
    def dir_cache(self) -> Path:
        return self.work / "05_cache"

    @property
    def dir_out(self) -> Path:
        return self.work / "06_deliverables"

    def ensure_dirs(self) -> None:
        for d in (self.dir_index, self.dir_transcripts, self.dir_bank,
                  self.dir_timelines, self.dir_cache, self.dir_out):
            d.mkdir(parents=True, exist_ok=True)

    def safe_box(self) -> tuple[int, int, int, int]:
        """(x, y, w, h) of the region where text may live, in output pixels."""
        w, h = self.get("output.width"), self.get("output.height")
        sx = int(w * self.get("safe_area.side_pct"))
        ty = int(h * self.get("safe_area.top_pct"))
        by = int(h * self.get("safe_area.bottom_pct"))
        return sx, ty, w - 2 * sx, h - ty - by
