"""Generate a synthetic Bengali course transcript + library so the engine can be
exercised end-to-end without real footage."""
from __future__ import annotations

import json
import sys
from pathlib import Path

LINES = [
    # (text, seconds)
    ("আসসালামু আলাইকুম, আজকে আমরা নতুন একটি ক্লাস শুরু করব।", 3.4),
    ("আমার নাম রাকিব, আমি এই কোর্সের ইন্সট্রাক্টর।", 2.9),
    ("আচ্ছা মানে, তো একটু দেখি, ইয়ে বুঝলেন কি বলব।", 3.0),
    ("বেশিরভাগ মানুষ এই একটা ভুলটা করে, আর সেজন্যই তারা কখনো এগোতে পারে না।", 4.2),
    ("কেন আপনার আগের সব চেষ্টা ব্যর্থ হয়েছে, জানেন?", 3.1),
    ("আসলে মূল কারণ হলো, কেউ আপনাকে ভিত্তিটাই শেখায়নি।", 3.6),
    ("আমি ১২ বছর ধরে এই ইন্ডাস্ট্রিতে কাজ করেছি এবং প্রায় ৪ হাজার শিক্ষার্থীকে শিখিয়েছি।", 5.1),
    ("প্রথম ধাপ হলো সমস্যাটা ঠিকভাবে চিহ্নিত করা, যেমন একটা উদাহরণ দিই।", 4.4),
    ("দ্বিতীয় ধাপে আমরা একটা সহজ পদ্ধতি ব্যবহার করব, যেটা আপনি আজই প্রয়োগ করতে পারবেন।", 5.0),
    ("অনেকে বলে আমার তো সময় নেই, কিন্তু দিনে মাত্র ২০ মিনিটই যথেষ্ট।", 4.3),
    ("এই কোর্স শেষে আপনি নিজেই পুরো কাজটা করতে পারবেন, কারো উপর নির্ভর করতে হবে না।", 5.2),
    ("আমার মা সবসময় বলতেন, শেখার কোনো বয়স নেই। এই কথাটাই আমার জীবন বদলে দিয়েছে।", 5.4),
    ("এটা একটু, হ্যাঁ, ওইটা।", 1.4),
    ("বিস্তারিত জানতে এবং কোর্সে ভর্তি হতে নিচের লিংকে যোগাযোগ করুন।", 4.0),
]


def make(out_dir: Path, media_path: str, name: str) -> dict:
    segs, t = [], 12.0
    for i, (text, dur) in enumerate(LINES):
        toks = text.split()
        per = dur / max(1, len(toks))
        words, wt = [], t
        for tok in toks:
            words.append({"w": tok, "start": round(wt, 3),
                          "end": round(wt + per, 3), "prob": 0.93})
            wt += per
        # Index 6 is the line carrying numbers ("১২ বছর", "৪ হাজার শিক্ষার্থী").
        # Digits are exactly where transcription errs, and a mis-heard number is a
        # fabricated claim -- so this is the segment that must reach the review list.
        lp = -0.95 if i == 6 else -0.32
        segs.append({
            "id": i, "start": round(t, 3), "end": round(t + dur, 3),
            "text": text, "words": words, "avg_logprob": lp,
            "no_speech_prob": 0.02, "needs_review": lp < -0.85,
        })
        t += dur + 0.7
    data = {"path": media_path, "name": name, "language": "bn",
            "language_probability": 0.99, "model": "synthetic",
            "segments": segs, "review_count": sum(1 for s in segs if s["needs_review"])}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{Path(name).stem}.synthetic.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main(work: str = "promo_work") -> None:
    w = Path(work)
    files = []
    for idx, nm in enumerate(["Lecture_07.mp4", "Lecture_11.mp4"], start=1):
        mp = f"/synthetic/course/{nm}"
        make(w / "02_transcripts", mp, nm)
        files.append({
            "path": mp, "name": nm, "duration": 3600.0, "bytes": 900_000_000,
            "container": "mov,mp4", "has_video": True, "has_audio": True,
            "width": 1920, "height": 1080, "fps": 30.0, "vcodec": "h264",
            "acodec": "aac", "sample_rate": 48000, "channels": 2,
            "loudness": {"input_i": -19.0 - idx, "input_tp": -2.0, "input_lra": 7.0},
            "audio_quality": 1.0, "visual_quality": 0.9, "usable": True,
        })
    (w / "01_index").mkdir(parents=True, exist_ok=True)
    (w / "01_index" / "library.json").write_text(
        json.dumps({"count": len(files), "files": files}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"fixture written to {w}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "promo_work")
