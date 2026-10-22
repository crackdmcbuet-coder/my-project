# Brief: picture cards (ছবি-কার্ড) for one part of zoo ch2 (for a writer agent)

The student remembers pictures, not text. Every question gets a small picture that shows its answer.
The pictures appear in the 📘 notes tab, under each section's note ("🖼️ ছবিতে মনে রাখো"). They are drawn by
`<skill>/templates/visual.js` from ONE line of data per question. You write only that data
(plus `data-p` pin targets in figures). **Never change any question, option, answer, note, or other text.**

Repo `/home/user/my-project` (`<repo>`); skill `<repo>/.claude/skills/mcq-chapter-notes` (`<skill>`).

## Read first
1. `<skill>/SKILL.md`, section "🖼️ Picture cards": the 7 kinds and their fields.
2. `<skill>/templates/visual.js`: how each kind is drawn (sizes, what fits).
3. `<repo>/chapters/zoo-ch2-animal-intro/70-visuals.js`: the finished pilot (30 questions). Match its quality.
4. Your part's topic files in `<repo>/chapters/zoo-ch2-animal-intro/` (the questions, their `s` section, the notes, the figures).

## Your file
`CHAPTER.visuals = Object.assign(CHAPTER.visuals || {}, { n: {...}, … });` with an entry for EVERY question in your range.
- `cap` (required): one short line under the picture stating the fact (≤ 45 characters, Bangla).
- Same fact asked twice (e.g. Q109 and Q116 both "রক্তকণিকার নাম"): give the first one a picture and the others `{same: 109}`.
  Only point `same` at a question in YOUR range (or the pilot's 63–72, 125–133, 184–194).
- The picture must show the BOOK's answer. Where the question's `w` has a ⚠ (book doubtful), write "(বই)" in `cap`.

## Choosing the kind (picture must teach the fact at a glance)
- Where something is / which part of a structure → `pin` on the section figure. Add `data-p="name"` to the
  element(s) in that section's `figure.svg` (only that attribute; several elements may share a name prefix,
  e.g. `ic` and `ic-gonad` both glow for `el:"ic"`). Use `sec` to pin a figure of another section.
- A count (≤ 12 things) → `count`; a measurement, length, time or range → `scale`.
- An order of steps / a path (blood flow, food path, development) → `chain`.
- Months or seasons → `cal`.
- "কোনটি নয় / সঠিক নয়" → `odd` (the odd one gets ✗); "কোনটি X" with one right pick → `odd` with `good: true` (gets ✓).
- Names, species, people, places, functions, "কেন" → `scene`: 2–4 common emoji + 2–3 short lines; put the word-root
  meaning in a line when it gives the answer away (chloro = সবুজ, ovi = ডিম).
- Variety: at least 5 different kinds in your part, and not the same kind more than 3 times in a row inside a section.

## Fit rules (the picture is 420 wide)
- chain step ≤ 14 characters; odd tiles use the options (long Latin names are fine, they shrink); scene lines ≤ 40
  characters at size 12, ≤ 28 at size 16; keep every text and emoji inside `h` (lowest baseline ≤ h − 8).
- Use only common emoji (food, animals, body, weather, objects); no flags, no skin-tone or ZWJ sequences.

## Work in your own scratch copy (never edit `<repo>` directly)
```
mkdir -p <scratch>/chapters <scratch>/out && cp -r <repo>/chapters/zoo-ch2-animal-intro <scratch>/chapters/ && cp -r <repo>/roots <scratch>/
```
Edit only `<scratch>/chapters/zoo-ch2-animal-intro/<your visuals file>` and, for pins, `data-p` attributes in your part's topic files.
Check until clean:
1. `python3 <skill>/verify_raw.py <repo>/chapters/raw/zoo-ch2.md <scratch>/chapters/zoo-ch2-animal-intro` → 0 problems.
2. `python3 <skill>/build.py <scratch>/chapters/zoo-ch2-animal-intro <scratch>/out` → "ok … visuals"; fix every error.
3. `node /tmp/claude-0/-home-user-my-project/ea1493e3-98fe-5ecb-97b9-ff8a07679250/scratchpad/tools/shoot_gal.js <scratch>/out/zoo-ch2-animal-intro-study.html <scratch>/shots <your section prefix>`
   (mkdir `<scratch>/shots` first). It must report no SPILL, no errors and scrollWidth=390. Then LOOK at every
   `gal-*.png` of your sections and fix overlapping or cramped pictures, and any picture that doesn't show its fact clearly.
Final reply (short): your files, number of entries (pictures + `same`), kinds used with counts, figures you added `data-p` to, anything unsure.
