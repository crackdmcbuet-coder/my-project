# Brief for writing one chapter's data files (for the writer agent)

You turn a verified raw OCR file into the chapter data files for the HTML study pages.
The OCR and the answers are already checked. **Do not change any question text, option or
answer letter.** Your job is the teaching content.

## Read first (in this order)
1. `/home/user/.claude/skills/mcq-chapter-notes/SKILL.md`: the rules, especially "User rules" and "Data format".
2. The finished reference chapter, which you should match in tone, depth and format:
   `/home/user/medical-mcq-notes/chapters/ch05-plant-physiology/00-meta.js`, `10-mineral.js` (whole file),
   the first 60 lines of `30-photosynthesis.js`, the first 40 lines of `50-hints.js` and the first 30 lines of `60-terms.js`.
3. `/home/user/medical-mcq-notes/roots/roots.js`: the existing shared word-root dictionary. Reuse its keys.
4. Your raw file (given in your task).

## Raw format
`n | src | M | question | opt ‖ opt ‖ … | letter | note`
- `M` → `m:1`. Empty → omit `m`.
- letter a–e → `a:` 0–4. A 5th option ("বইয়ের নোট: …", "(a) ও (c) দুটোই") is part of `o`, kept exactly.
- `note`: put "বি.দ্র"/ব্যাখ্যা text into `w` (the why), in your own simple words plus the book's point.
  A note marked ⚠ means the book's answer looks wrong: keep the book's answer, and in `w` say
  "⚠ বইয়ের উত্তর এটা; কিন্তু …(সঠিক তথ্য)… — পরীক্ষার আগে স্যারকে জিজ্ঞেস করো". Lines like
  "student margin note: …" are the student's own memory hooks; use them in the mnemonic or hint.
- "(X)" = the student crossed the question out; still a normal marked question.
- A note containing "verify on the web" (a conflict, or an answer read from a cut-off column): run ONE
  WebSearch (mode "standard") for that fact. If the book has an explicit বি.দ্র correction, follow the book.
  Otherwise keep the book's answer and, if the web disagrees, add the ⚠ "ask sir" line with what the web says.
  Never change the answer letter yourself.
- Each `## topic: <id> — <name>` heading is one topic. Create `topics` from these headings in this order
  and choose a fitting emoji icon for each.

## Files to write in `/home/user/medical-mcq-notes/chapters/<chapter-id>/`
- `00-meta.js`: `const CHAPTER = {id, title, subtitle, topics:[…], sections:[], questions:[], cheats:[]}`.
  Copy the style of ch05; put the page range and the topic list in the subtitle.
- `05-roots-new.js`: `Object.assign(ROOTS, { key: {w, lang, m, also:[], med:[]}, … });` with ONLY the
  roots this chapter needs that are not already in roots.js. Don't edit roots.js itself. Etymology must
  be real; if unsure, leave the root out.
- One file per topic, numbered `10-…js`, `20-…js`, … (≤ 9 topics → 10,15,20,25,30,35,40,45): each one
  `CHAPTER.sections.push(…)`, `CHAPTER.questions.push(…)`, `CHAPTER.cheats.push(…)`.
  - Use 2–4 sections per topic (≈ 6–12 questions per section). Every question's `s` must point to a
    section whose `note` contains the facts needed to answer it.
  - Each section has `id, topic, heading, figure:{svg, caption}, note, why, mnemonic, story, traps:[…]`, the same as ch05:
    - `note`: book-style Bangla paragraph(s) with **every** fact needed for that section's questions.
      `<span class="k">` marks key terms. `<span class="err">` marks the facts behind the M-marked questions
      (every M question's key fact must appear red at least once).
    - `figure.svg`: an inline SVG drawn by you (viewBox width 420, height ≤ 260), with a simple CSS
      keyframe or SMIL animation that *explains* something (a process, comparison, map, or cycle). Use
      dark text on light shapes, font ≤ 14px, and keep labels inside the viewBox and not overlapping.
      Don't use class names `k`, `err`, `card`, `box`, `story`, `why`. Caption: one plain sentence.
    - `why`: cause → effect reasons.
    - `mnemonic`: **varied** hooks: sound/letter match, Bangladeshi places, cricket/football, food,
      family, hospital life, Islamic context, history. Don't reuse the same kind back to back, and
      reuse the student's margin notes.
    - `story`: a 4–6 sentence vivid scene that carries every exam fact of the section, especially the red ones.
    - `traps`: 3–6 one-line elimination rules ("X দেখলে বাদ, কারণ …"), drawn from the actual distractors.
  - `questions`: `{n, s, src, m?, q, o:[…], a, w, e}`, copied exactly from raw. `w` = short why,
    `e` = one line on why the other options are wrong (the elimination).
  - `cheats`: 1–3 compact `<table>` cards per topic (numbers, pairs, who-did-what), with `class="err"` on
    cells for marked facts.
- `50-hints.js`: `CHAPTER.hints = { n: [cue, hint], … }` for **every** question. `cue` must be an exact
  substring of that question's text (or of one option); the build fails otherwise. `hint` nudges
  toward the answer without stating it (root meaning, sound match, number in the name, option pattern,
  or the section's story).
- `60-terms.js`: `CHAPTER.terms = [{t, bn, s, p:[root keys], lit, bnp?, fact}, …]` with 25–45
  important terms of this chapter, each broken into Greek/Latin/Sanskrit roots (keys from roots.js or
  your 05-roots-new.js). `fact` = which MCQ fact the literal meaning gives away. Include scientific
  names where the roots really help (e.g. Heritiera fomes, Bacillus thuringiensis).

## Language
Simple spoken-style Bangla, like ch05. Scientific terms in English where the exam uses them.
Don't write grand or flowery phrases and don't pad. Be concrete.

## Check before you finish
1. Build into a private folder (not the shared output):
   `python3 /home/user/.claude/skills/mcq-chapter-notes/build.py /home/user/medical-mcq-notes/chapters/<chapter-id> /tmp/claude-0/-home-user/8dc663aa-c6ec-5273-87af-79fee923e0d4/scratchpad/build-<chapter-id>`
   Fix every reported error until it prints "ok". The question count must equal the raw file's count.
2. Screenshot every figure at 390px width with Playwright
   (`const { chromium } = require('/opt/node22/lib/node_modules/playwright')`, open the built
   `<chapter-id>-study.html` via file://, `page.$$('figure')`, `el.screenshot()`), combine them into 1–2
   contact sheets with PIL, look at them, and fix clipped or overlapping labels. Also check that
   `page.on('pageerror')` reports nothing.
3. Don't edit any file outside your chapter folder.
4. Final reply (short, English is fine): file list, question/section/term counts, roots added, and
   anything you were unsure about.
