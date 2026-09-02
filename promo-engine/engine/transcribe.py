"""STEP 2/11 -- transcription with word-level timestamps.

Word timings are not optional: the attention engine cuts on word boundaries and
the kinetic-typography pass needs per-word timing to emphasise the right syllable.

Backend: faster-whisper (CTranslate2). Falls back to openai-whisper if present.
Nothing here is trusted blindly -- `promo review` exists so important lines get
human eyes before they reach the screen (STEP 11).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .config import Config
from .util import read_json, write_json

_LOW_CONF = -0.85     # avg logprob below this = flag the segment for manual review


def _key(path: str | Path, model: str, lang: str) -> str:
    p = Path(path)
    try:
        stamp = f"{p.stat().st_size}:{int(p.stat().st_mtime)}"
    except OSError:
        stamp = "0:0"
    raw = f"{p.resolve()}|{stamp}|{model}|{lang}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _pick_device(pref: str) -> tuple[str, str]:
    if pref not in ("auto", None):
        return pref, "auto"
    try:
        import torch  # noqa: F401
        if torch.cuda.is_available():
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def transcribe_file(path: str | Path, cfg: Config, *, force: bool = False) -> dict:
    """Returns {path, language, segments:[{start,end,text,words:[{w,start,end,prob}],...}]}."""
    model_name = cfg.get("transcribe.model", "large-v3")
    lang = cfg.get("language", "auto")
    cfg.ensure_dirs()
    cache = cfg.dir_transcripts / f"{Path(path).stem}.{_key(path, model_name, lang)}.json"
    if cache.exists() and not force:
        return read_json(cache)

    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError(
            "faster-whisper is not installed.\n"
            "  pip install faster-whisper\n"
            "  (GPU: also install a CUDA-enabled ctranslate2 build)"
        ) from e

    device, compute = _pick_device(cfg.get("transcribe.device", "auto"))
    if cfg.get("transcribe.compute_type", "auto") != "auto":
        compute = cfg.get("transcribe.compute_type")

    model = WhisperModel(model_name, device=device, compute_type=compute)
    segments, info = model.transcribe(
        str(path),
        language=None if lang == "auto" else lang,
        word_timestamps=True,
        vad_filter=bool(cfg.get("transcribe.vad", True)),
        beam_size=int(cfg.get("transcribe.beam_size", 5)),
    )

    out_segs = []
    for s in segments:
        words = [
            {"w": w.word.strip(), "start": round(w.start, 3),
             "end": round(w.end, 3), "prob": round(getattr(w, "probability", 0.0) or 0.0, 3)}
            for w in (s.words or []) if w.word and w.word.strip()
        ]
        avg_lp = float(getattr(s, "avg_logprob", 0.0) or 0.0)
        out_segs.append({
            "id": len(out_segs),
            "start": round(float(s.start), 3),
            "end": round(float(s.end), 3),
            "text": (s.text or "").strip(),
            "words": words,
            "avg_logprob": round(avg_lp, 3),
            "no_speech_prob": round(float(getattr(s, "no_speech_prob", 0.0) or 0.0), 3),
            "needs_review": avg_lp < _LOW_CONF,
        })

    data = {
        "path": str(Path(path).resolve()),
        "name": Path(path).name,
        "language": getattr(info, "language", lang),
        "language_probability": round(float(getattr(info, "language_probability", 0.0) or 0.0), 3),
        "model": model_name,
        "segments": out_segs,
        "review_count": sum(1 for s in out_segs if s["needs_review"]),
    }
    write_json(cache, data)
    return data


def run_transcribe(cfg: Config, paths: list[str] | None = None, *, force: bool = False) -> list[dict]:
    if paths is None:
        lib = read_json(cfg.dir_index / "library.json", default={"files": []})
        paths = [f["path"] for f in lib.get("files", []) if f.get("usable")]
    results = []
    for i, p in enumerate(paths, 1):
        print(f"  [{i}/{len(paths)}] transcribing {Path(p).name}")
        try:
            data = transcribe_file(p, cfg, force=force)
            print(f"      {len(data['segments'])} segments, lang={data['language']}, "
                  f"{data['review_count']} low-confidence")
            results.append(data)
        except Exception as e:                      # one bad file must not kill the batch
            print(f"      FAILED: {e}")
            results.append({"path": str(p), "error": str(e), "segments": []})
    return results


def load_all(cfg: Config) -> list[dict]:
    out = []
    for f in sorted(cfg.dir_transcripts.glob("*.json")):
        try:
            d = read_json(f)
        except Exception:
            continue
        if d.get("segments"):
            out.append(d)
    return out
