---
name: mcq-chapter-notes
description: Turn photos/PDFs of a Bangla medical-admission question-bank chapter (exercise + previous-year MCQs, answers printed on the right margin, the student's own pen/highlighter marks) into three self-contained offline HTML study pages — book-style notes with animated SVG diagrams and red-marked mistake points, a "why + mnemonic + visual story" version, tap-to-reveal practice, a timed mock test with negative marking + flashcards, and a one-page revision sheet. Use when the user uploads chapter page images and asks for notes / MCQ practice / mnemonics, or says "এই চ্যাপ্টারটা বানাও".
---

# MCQ Chapter Notes (মেডিকেল ভর্তি নোট বানানোর পদ্ধতি)

Goal: a student with brain fog must **recognise** the right option and **eliminate** the
rest. Recall from memory is not required. Every note, story and trap serves MCQ elimination.

## Layout
```
<skill>/build.py              builds the HTML (node needed for the data check)
<skill>/templates/base.css    shared look (light + dark)
<skill>/templates/common.js   data normaliser, shared progress store, SVG style scoping
<skill>/templates/study.html  📘 notes · 🧠 why/mnemonic/story/traps · ❓ practice (💡 hint first) · 🔑 clue list · 🔤 word roots · 🔴 mistakes
<skill>/templates/quiz.html   ⏱️ mock test (36 s/Q, −0.25 per wrong) + 🃏 flashcards + 🔤 root cards
<skill>/templates/cheatsheet.html  📄 tables + red points + clue table + root table + mnemonics, printable
<skill>/templates/roots.html  🔤 shared word-root dictionary (all chapters)
<skill>/templates/terms.js    term/root rendering shared by all pages
<skill>/templates/visual.js   🖼️ per-question picture cards (CHAPTER.visuals), drawn from data
<skill>/roots-seed.js         starter dictionary for a new project
<project>/roots/roots.js      the project's growing dictionary
<project>/chapters/<id>/*.js  one chapter's data (00-meta.js first, then one file per topic)
<project>/output/<id>-{study,quiz,cheatsheet}.html
```
Build: `python3 <skill>/build.py <project>/chapters/<id> <project>/output`
All three pages share one localStorage key per chapter, so ✅/❌ from the mock test shows up in the study page.

## User rules (from the student; keep them)
- Include ONLY **"বিগত মেডিকেল ও ডেন্টাল ভর্তি পরীক্ষার প্রশ্ন"** and **"বিভিন্ন লেখকের মূল বইয়ের অনুশীলনীর প্রশ্ন"**.
  SKIP every **"সম্ভাব্য প্রশ্ন"** block, even when the student highlighted questions in it.
- Any marking in any ink (circle, slash on the number, highlighter, star, underline, cross) =
  "I got this wrong before" → `m:1` on the question, `<span class="err">` on the fact in the note.
  Big pencil brackets spanning several questions are not marks.
- Mnemonics: vary the type (sound-match, cricket/football, Dhaka places, Bangladesh history,
  food, family, hospital life). Every section also gets a **3–5 sentence visual story** that
  carries every exam fact, especially the red ones.
- **🔑 Every question gets a clue** (student's request: "অপশন দেখে বা প্রশ্নের মধ্যেই উত্তরের হিন্টস"):
  `CHAPTER.hints = { n: [cue, hint] }` in its own file (e.g. `50-hints.js`).
  `cue` = an exact substring of the question (or of an option) that points to the answer.
  It gets highlighted in yellow. `hint` = a one-line nudge linking cue to answer *without
  naming the answer outright*. Kinds of links, in order of preference:
  word roots (ফটো=আলো, লাইসিস=ভাঙা, স্বেদ=ঘাম, ট্রাই=৩, lactis=দুধ, Saccharum=চিনি, oleic=olive oil),
  sound/letter match (ফুল→ফসফরাস, করবী=কর ফাঁকি=লুকায়িত), a number inside the name
  (C₄→৪C OAA, P700→অতি লাল), option-pattern elimination ("শুধুমাত্র" in a "সঠিক নয়"
  question, the only option containing "রক্ষীকোষ", every option with "সবুজ" is wrong), and
  the section's mnemonic or story. build.py refuses a missing hint or a cue not found in the text.
- **🔤 Word roots for every key term** (student's request: Greek/Latin/English meaning so the
  fact sticks and carries over to other chapters):
  `<project>/roots/roots.js` is ONE dictionary shared by all chapters (`ROOTS[key] = {w, lang, m, also[], med[]}`;
  `med` = where the same root shows up in medicine, e.g. lysis → hemolysis). Add only new roots; reuse old keys.
  Bangla/Sanskrit roots use keys `bn_*` (স্বেদ = ঘাম, বাত = বায়ু, রন্ধ্র = ছিদ্র …).
  Each chapter has `60-terms.js`: `CHAPTER.terms = [{t, bn, s, p:[root keys], lit, bnp?, fact}]`.
  `lit` = the literal meaning built from the roots; `fact` = which MCQ fact that meaning gives away.
  Prefer terms whose literal meaning answers a question (Photo-lysis = আলো দিয়ে ভাঙা; an-aerobic = অ-বাত).
  Check the etymology. Never invent one: if unsure, leave the term out.
  The build also writes `output/roots.html`, a searchable dictionary across every chapter
  with a self-test mode. The first build of a new project seeds roots.js from `roots-seed.js`.
- Reuse the student's own margin notes as mnemonics when they are readable (e.g. "Queen" for plastoquinone).

## Step 1: Pages → images
Phone photos are often upside-down or carry EXIF rotation. Use `ImageOps.exif_transpose`,
rotate 180° where needed, then crop each page into 4 overlapping quadrants
(left/right column × top/bottom, ~53%/55% with overlap) and Read each quadrant.
The full-size page is too small to read accurately.

## Step 2: OCR + answer matching (most important; never rush)
- The circled answer letter sits on the right, usually **on the last option line or slightly
  below it**, so it can look like it belongs to the next question. Match by serial: the
  answer must be one of *that* question's options, and the answer count must equal the
  question count on the page.
- Keep the book's answer. When the book prints a "বি.দ্র"/ব্যাখ্যা correcting a teacher's
  book, use the corrected answer and quote the note in `w`. When the book has no correct
  option, add an extra option "বইয়ের নোট: …" and point `a` at it.
- If you think the book itself is wrong, keep its answer, write ⚠ in `w`, and list the item to the user.
- Note pages that are missing from the photos (serial gaps) and tell the user.

## Step 3: Data format (chapters/<id>/*.js)
`00-meta.js` defines `const CHAPTER = {id, title, subtitle, topics:[{id,name,icon}], sections:[], questions:[], cheats:[]}`.
Each topic file does `CHAPTER.sections.push({...})`, `CHAPTER.questions.push({...})`, `CHAPTER.cheats.push({...})`.

Section: `{id, topic, heading, figure:{svg, caption}, note, why, mnemonic, story, traps:[...]}`
- `note`: book-style paragraph(s) containing **every fact** needed for that section's MCQs.
  `<span class="k">` = key term (hidden in recall mode), `<span class="err">` = student's past mistake.
- `figure.svg`: hand-drawn inline SVG (viewBox ≈ 420 wide), with CSS keyframe or SMIL
  animation for processes. The style is scoped automatically per figure, so short class
  names are fine, but avoid page class names (`k`, `err`, `card`, `box`). Dark text on a
  light figure background works in both themes. Real photos: Wikimedia often rate-limits
  this environment; prefer SVG.
- `traps`: one line per distractor pattern: what it looks like and why to eliminate it.

Question (compact keys): `{n, s:sectionId, src:"MAT 21-22"|"অনুশীলনী (আলীম স্যার)", m:1?, q, o:[...], a:0-based, w:why, e:elimination}`.
Cheat: `{topic, title, html}` (a small `<table>`; put `class="err"` on cells the student got wrong).

## 🖼️ Picture cards (optional, pilot in zoo ch2)
The student remembers pictures better than text. `NN-visuals.js` does
`CHAPTER.visuals = Object.assign(CHAPTER.visuals || {}, { n: {t, …, hook, cap} })`, and the practice tab shows a
"🖼️ ছবি-হিন্ট" (answer hidden) before the answer and the full picture after it. `hook` = the hint line, `cap` = the line under the full picture.
Kinds: `pin {el, sec?}` (glow a part of a section figure; mark it with `data-p="el"` in the SVG) ·
`count {n, icon, label, unit?, extra?}` · `chain {steps, hide?, on?, note?}` · `scale {max, step, unit, marks:[{v|[a,b], l}], hl?}` ·
`cal {on?:[1-12], seasons?, season?, label}` · `odd {odd, group, why, good?, items?}` (`good`: the odd one is the right pick) ·
`scene {art:[[emoji,x,y,size,anim]], lines:[[text,x,y,size]], key?, ground?, h?}`. build.py checks the kind, the fields and the pin target.

## Step 4: Build + verify
1. Run build.py. It refuses bad answer indexes, unknown sections, and duplicate numbers.
2. Screenshot with Playwright at 390 px (`require('/opt/node22/lib/node_modules/playwright')`):
   each `figure` element, practice after a tap, the quiz result, the cheatsheet, and dark mode.
   Check for clipped or overlapping SVG labels and console errors.
3. Report to the user: question count, marked count, skipped blocks, missing pages, and
   uncertain or disputed answers.

## Cheapest input: EXTRACT-*.md text files (no images)
If the user gives EXTRACT files (`### Qn`, `**স্টেম:**`, `- ক. …`, `**উত্তর:**`, `**ট্যাগ:**`, `**⚠ দ্বন্দ্ব:**`),
skip OCR entirely:
`python3 <skill>/extract_to_raw.py <project>/chapters/raw/<id>.md "<title>" part1.md part2.md [--wrong 3,7,13]`
- Use the per-part files, not a "joined" file (its sections can be out of order).
- `--wrong` = the questions the student got wrong (→ M). If the user gives none, leave it out; the page
  has a "➕ ভুল করি" button on every question, so they can mark them on the phone (saved locally, and it feeds the 🔴 tab and the mock-test filter).
- The script lists ⚠ items (conflicts, answers read from cut-off columns) and incomplete questions. Fill
  missing answers only when they are standard textbook facts, and note that you did. The writer
  agent checks each ⚠ item with one WebSearch.
- Then continue from step 2 below (the writer agents). Do this in a **fresh session**: a long session
  re-reads its whole history on every step, which cost more than the work itself in this project.

## Cheaper pipeline for several chapters (used for ch10–12)
1. **Opus** transcribes each chapter into `<project>/chapters/raw/<id>.md`:
   `n | src | M | question | opt ‖ opt ‖ … | letter | note`. Crop any doubtful spot and verify it;
   flag suspicious book answers with ⚠ in the note.
2. Spawn one **Sonnet** writer agent per chapter (in parallel, background), pointing it at
   `<project>/chapters/raw/BRIEF.md` + the raw file. Each writes only its own chapter folder; new roots
   go in `05-roots-new.js` (`Object.assign(ROOTS, {...})`).
3. When they finish, check that no question, option, answer or mark changed:
   `python3 <skill>/verify_raw.py <raw.md> <chapter-dir>` must print 0 problems.
4. Merge every `05-roots-new.js` into `roots/roots.js` (keep the first copy of each key), then move the per-chapter files out.
5. Build every chapter into `output/`. The last build writes `index.html` (all chapters) and `roots.html`.
6. Open every page with Playwright: no `pageerror`, and no horizontal scroll at 390 px.

## Model choice (cost vs quality)
- OCR of Bangla scans + handwriting + answer matching, and writing the data: **Opus**
  (one wrong answer poisons the whole page).
- Adding mnemonics or stories to existing data, or fixing wording: **Sonnet**.
- Rebuilding, tiny edits, or adding a few questions: **Haiku**.
