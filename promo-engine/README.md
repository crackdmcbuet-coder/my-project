# Course Promo Engine

Turn existing course recordings into high-retention 9:16 promos — and, more
importantly, into a **content bank** you can pull from for the next twenty reels
without ever re-scanning the course.

Built to a specific brief: attention-based editing (not a 2-second metronome),
source-first (no stock filler), and **no invented claims** — every word on
screen is a word the instructor actually said, traceable to a file and a
timestamp.

আপনার কোর্স রেকর্ডিং থেকে হাই-রিটেনশন প্রোমো বানানোর ইঞ্জিন। বাংলা ও ইংরেজি
দুই ভাষার লেকচারেই কাজ করে।

---

## Why this is an engine, not a one-off promo

A single promo is one output. Scanning a 40-hour course to make it is the
expensive part — and that work is thrown away the moment the promo is done.

So the engine does the scan **once** and keeps the result:

```
course footage  ->  transcripts  ->  CONTENT BANK  ->  promo #1
                                            |         promo #2
                                            |         ad variant #3
                                            +-------> reel #4 ...
```

The bank is a queryable database of scored, categorised, timestamped clips:

```
HOOK · PROBLEM · EMOTIONAL · AUTHORITY · INSIGHT
TEACHING · TRANSFORMATION · OBJECTION · CTA
```

```bash
./promo bank query --category HOOK --top 20          # 20 strongest openings
./promo bank query --category AUTHORITY --sort authority
./promo bank query --category PROBLEM --max-dur 3.0  # short, punchy pain lines
```

That query answers in milliseconds, forever, off one scan.

---

## Install

Runs on **your machine**, where the footage is. Python 3.10+.

```bash
git clone <this repo> && cd promo-engine
pip install -r requirements.txt      # faster-whisper
# ffmpeg + ffprobe must be on PATH:
#   macOS   brew install ffmpeg
#   Debian  sudo apt install ffmpeg
#   Windows winget install Gyan.FFmpeg

./promo doctor        # verifies the filtergraphs actually run here
```

`doctor` renders a synthetic 2-second clip through the real pipeline and reports
whether the static path, the motion path and subtitle burn-in all work on your
ffmpeg build. **Run it once before your first render** — it turns a confusing
render failure into a one-line answer.

For Bengali captions you need a Bengali font installed system-wide
(`Noto Sans Bengali` is the default; set `subtitles.font` to change it).

---

## Quick start

```bash
cp promo.config.example.json promo.config.json
# edit sources.roots to point at your course folders, set language to bn/en

./promo all --root "/path/to/course"
```

That runs the whole pipeline and produces every version the material actually
supports. Or step through it:

```bash
./promo discover --root "/path/to/course"   # STEP 1  find footage
./promo probe                               # STEP 2  resolution, fps, loudness
./promo transcribe                          # STEP 2  word-level transcripts
./promo bank build                          # STEP 4  the content bank
./promo positioning                         # STEP 3  what the footage supports
./promo hooks                               # STEP 24 A/B hook options
./promo build --target 30 --label promo_30  # STEP 5-9 concept, timeline, audit
./promo render promo_30                     # STEP 25 render + paperwork
```

---

## What each stage actually does

### STEP 1 — discover
Walks your drives, groups media by folder, and **ranks candidate course
folders** by file count, runtime, course-like naming, and sequential filenames
(`lecture_01`, `lecture_02`… is a strong signal). Stock/render/proxy folders are
penalised. It never assumes it found the right folder — it shows you the
ranking and lets you redirect with `--root`.

### STEP 2 — library and transcripts
`ffprobe` for resolution/fps/codecs, plus an EBU R128 loudness measurement per
file. These become the `audio_quality` and `visual_quality` scores, so a clip
from a clipped, noisy recording loses to the same line from a clean one.

Transcription uses faster-whisper with **word-level timestamps** — not optional,
because the attention engine cuts on word boundaries and the typography needs to
know when each word lands. Results are cached by file size + mtime + model, so
re-running is free.

### STEP 4 — scoring and the bank
Every segment is scored across the eleven dimensions from the brief
(`hook_power`, `curiosity`, `emotional`, `authority`, `clarity`, `specificity`,
`value`, `relatability`, `visual_quality`, `audio_quality`, `retention`).

Rejected outright, with the reason recorded: greetings and self-introductions
(STEP 7), filler-dense lines, sub-1.2s fragments, non-speech.

Bengali cue matching is stem-aware: `ভুল` matches `ভুলটা`/`ভুলগুলো`, but a
2-character cue like `মা` must be a whole word so it doesn't fire inside `মানুষ`.

### STEP 5 — three concepts, scored
All three are built, then compared on expected retention, hook strength, visual
variety, source diversity and arc completeness:

```
CONCEPT SCORES: A=2.955  B=2.620  C=2.145
selected A (CURIOSITY / HOOK-DRIVEN) -- opens on an unanswered question
```

The comparison is written to `EDIT_DECISIONS.txt`, so the choice is auditable.

### STEP 8/9 — the attention engine
**This is the part that isn't a metronome.** Cut points come from real speech
structure:

| signal | why it's a cut point |
|---|---|
| sentence end (`।` `?` `!`) | a thought completes, a new idea begins |
| breath / pause ≥ 220ms | natural seam in delivery |
| emphasised keyword | the important word deserves a hit |
| contrast marker (`কিন্তু`, `আসলে`, "but") | the argument turns |
| attention budget spent | nothing else justified a change, but attention would drop |

The budget **tightens early and relaxes later** — ~1.6s in the first 8 seconds,
~2.6s afterwards — because that's where scroll-away happens. Real output:

```
00:00.0 (1.20s) WIDE         HOOK begins -- hard cut to a new source
00:01.2 (0.60s) KEYWORD_POP  emphasised word: কেউ
00:01.8 (1.80s) WIDE         new idea -- reset the frame
00:05.0 (0.72s) REFRAME      argument turns -- push in on the speaker
00:18.7 (2.55s) WIDE         attention would drop -- change the visual
```

Shot lengths 0.55s–2.55s, none of them equal. Every one carries its reason into
`TIMELINE_BREAKDOWN.txt`.

Visual variety comes from **your own footage**, not stock: `WIDE`, `PUNCH_MED`,
`PUNCH_CLOSE`, `REFRAME`, plus `KEYWORD_POP` and exactly one full-screen
`TEXT_CARD` per promo — placed mid-body, cut from the speaker, never inside the
hook and never shorter than 0.9s (an unreadable card is worse than no card).

### STEP 10/11 — captions
ASS, not SRT, because the brief needs per-word emphasis and precise safe-area
placement. Phrase chunks of ≤4 words, broken at punctuation, the keyword
coloured and scaled, captions clamped so one never outlives its shot. An `.srt`
companion is written for platform upload.

### STEP 14/15/16 — sound and colour
Per-shot 12ms audio fades at every cut (this is what stops the clicking that
gives away an amateur edit), `loudnorm` to −14 LUFS / −1.5 dBTP at master, and
music — when configured — ducked under the voice with `sidechaincompress` keyed
on the voice itself. Colour is a gentle consistency pass, not a cinematic LUT.

### STEP 21/22 — the audit
Runs all 15 retention questions plus the mobile checks against the actual
timeline. It can and does block a render:

```
[FAIL] 5. mechanical cutting: shot lengths barely vary (sd=0.00s)
         -> RULE 5: this is metronome editing, not attention editing
[FAIL] 2. no intro boilerplate: promo opens on a greeting
[WARN] 22. crop resolution: Lecture_07.mp4 upscales 1.99x
         -> expected for 16:9 -> 9:16; shoot or export 4K to avoid softness
```

A `FAIL` stops `promo render` unless you pass `--force`.

### STEP 25 — deliverables
Per version: the `.mp4`, `.ass`, `.srt`, and

```
TIMELINE_BREAKDOWN.txt   time / source / timestamp / audio / text /
                         visual / transition / sfx / music / reason
PROMO_SCRIPT.txt         every spoken line, with its source timestamp
SOURCE_CLIPS.txt         which footage was used where
EDIT_DECISIONS.txt       concept comparison, every cut, the audit
HOOK_OPTIONS.txt         A/B alternates from three different angles
```

---

## The claim guarantee

The engine cannot invent a claim, by construction:

- On-screen text is assembled from transcript **words with their own
  timestamps** — there is no path from the engine to a sentence nobody said.
- Every clip in the bank carries `source`, `start`, `end` and its exact text.
- Low-confidence transcription is flagged (`needs_review`) rather than trusted —
  and lines carrying **numbers** are exactly the ones you should check, because
  a mis-heard number is a fabricated claim.
- Gaps are reported, not filled. If the footage contains no CTA, `positioning`
  prints `!! NO EVIDENCE IN THE FOOTAGE` instead of writing one for you.
- If the material can't carry 60 seconds, that version is **skipped with the
  shortfall stated**, not padded.

`approved_claims` in the config is the only way non-spoken text (a course name,
say) can appear — an explicit, reviewable list.

---

## Tuning

| symptom | setting |
|---|---|
| feels frantic | raise `attention.early_budget` |
| drags late | lower `attention.late_budget` |
| punch-ins too aggressive | lower `attention.punch_levels` |
| captions too small on a phone | raise `subtitles.size_pct` |
| captions collide with platform UI | raise `safe_area.bottom_pct` |
| music too loud | lower `audio.music_duck_db` (more negative) |

Camera movement is **off by default** — the static path is correct on every
ffmpeg build. `--motion` adds a real zoompan push; run `promo doctor` first, it
reports whether motion works on your build.

---

## Tests

```bash
python3 tests/test_engine.py     # 75 checks, no ffmpeg or GPU needed
```

Covers Bengali cue matching, greeting rejection, scoring, folder ranking, bank
queries, the attention engine's non-mechanical cutting, caption safe areas,
crop geometry for 16:9 / 4K / vertical / square sources, ffmpeg command shape,
and that the audit actually blocks a metronome-cut, greeting-opening timeline.

## Layout

```
engine/discover.py    STEP 1   find and rank course folders
engine/probe.py       STEP 2   ffprobe + loudness -> quality scores
engine/transcribe.py  STEP 2   faster-whisper, word timestamps, cached
engine/lexicon.py              Bengali + English cue lexicons
engine/scoring.py     STEP 4   the 11 dimensions
engine/bank.py        STEP 2/4 the content bank
engine/timeline.py    STEP 5-9 concepts, beats, the attention engine
engine/subtitles.py   STEP 10  ASS kinetic typography + SRT
engine/render.py      STEP 9/14/16/22  ffmpeg, two-stage
engine/audit.py       STEP 21/22  retention + mobile audit
engine/deliver.py     STEP 23-25  the paperwork
engine/cli.py                  the promo command
```

Originals are never written to (RULE 12); everything lands in `work_dir`.
