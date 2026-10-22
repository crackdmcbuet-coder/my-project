# Brief for writing one PART of zoo ch2's data files (for a writer agent)

You turn a verified raw file into chapter data files for the offline HTML study pages.
The questions and answers are already checked. **Do not change any question text, option, answer
letter or marked flag.** Your job is the teaching content. Three writers work in parallel, one per
animal (Hydra / ঘাসফড়িং / রুই মাছ), each on its own slice of the same chapter.

Repo: `/home/user/my-project` (call it `<repo>`). Skill: `<repo>/.claude/skills/mcq-chapter-notes/` (`<skill>`).

## Read first (in this order)
1. `<skill>/SKILL.md`: the rules, especially "User rules" and "Step 3: Data format". It is the spec:
   there is NO finished reference chapter in this repo (this is the project's first chapter).
2. `<skill>/templates/common.js` and `<skill>/templates/study.html` (skim) so you know how the
   fields render.
3. `<repo>/chapters/zoo-ch2-animal-intro/00-meta.js`: the chapter id and the 9 topics (already written; don't edit).
4. `<repo>/roots/roots.js`: the existing shared word-root dictionary. Reuse its keys; don't edit it.
5. Your raw file (given in your task).

## Raw format
`n | src | M | question | opt ‖ opt ‖ … | letter | note`
- `M` → `m:1`. Empty → omit `m`. (This chapter has none marked; the student marks on the phone.)
- letter a–e → `a:` 0–4. Copy `q` and every option EXACTLY (including odd spellings, duplicated options
  like Q67, and typos). `src` → the `src` field as given.
- `note`: "ব্যাখ্যা (বই): …" text goes into `w` (the why), in your own simple words plus the book's point.
  A note marked ⚠ / "verify on the web": run ONE WebSearch (mode "standard") for that fact.
  If the book has an explicit Note/বি.দ্র correction, follow the book. Otherwise keep the book's answer
  and, if the web disagrees, write in `w`: "⚠ বইয়ের উত্তর এটা; কিন্তু …(সঠিক তথ্য)… — পরীক্ষার আগে স্যারকে জিজ্ঞেস করো".
  "বইয়ের উত্তর কাটা পড়েছে; … বসানো" = the answer was cut off in the scan and was filled from standard
  textbook facts: confirm with the search and say in `w` "(বইয়ের উত্তর ছবিতে কাটা পড়েছিল; পাঠ্যবই অনুযায়ী)".
  Never change an answer letter yourself; if you believe a filled answer is wrong, report it in your final reply.
- Each `## topic: <id> — <name>` heading is one topic; the ids match 00-meta.js.

## Your files (fixed slots, so the three writers never collide)
| part | roots | topic files | hints | terms | section ids |
|---|---|---|---|---|---|
| hydra (t1–t4) | `05-roots-hydra.js` | `10-…js` (t1), `15-…js` (t2), `20-…js` (t3), `25-…js` (t4) | `51-hints-hydra.js` | `61-terms-hydra.js` | `hy-…` |
| grasshopper (t5–t7) | `06-roots-gh.js` | `30-…js` (t5), `35-…js` (t6), `40-…js` (t7) | `52-hints-gh.js` | `62-terms-gh.js` | `gh-…` |
| rui (t8–t9) | `07-roots-rui.js` | `45-…js` (t8), `48-…js` (t9) | `53-hints-rui.js` | `63-terms-rui.js` | `ru-…` |

- Roots file: `Object.assign(ROOTS, { key: {w, lang, m, also:[], med:[]}, … });` ONLY roots this part needs
  that are not already in roots.js. Etymology must be real; if unsure, leave it out. Bangla/Sanskrit keys use `bn_*`.
- Topic files: `CHAPTER.sections.push(…)`, `CHAPTER.questions.push(…)`, `CHAPTER.cheats.push(…)`.
  - 2–4 sections per topic (≈ 6–12 questions per section). Every question's `s` points to a section whose
    `note` contains the facts needed to answer it.
  - Section: `{id, topic, heading, figure:{svg, caption}, note, why, mnemonic, story, traps:[…]}`
    - `note`: book-style Bangla paragraph(s) (HTML allowed: `<p>`, `<b>`, `<br>`, small `<ul>`) with **every**
      fact needed for that section's questions. `<span class="k">` marks key terms. Use `<span class="err">`
      only for facts behind M questions (none in this chapter) — so skip `err` here.
    - `figure.svg`: an inline SVG you draw (viewBox width 420, height ≤ 260), with a simple CSS keyframe or
      SMIL animation that *explains* something (a process, comparison, cycle, structure with labels).
      Dark text on light shapes, font ≤ 14px, labels inside the viewBox and not overlapping. Don't use class
      names `k`, `err`, `card`, `box`, `story`, `why`. Caption: one plain sentence.
    - `why`: cause → effect reasons.
    - `mnemonic`: **varied** hooks: sound/letter match, Bangladeshi places, cricket/football, food, family,
      hospital life, history. Don't reuse the same kind back to back.
    - `story`: a 4–6 sentence vivid scene that carries every exam fact of the section.
    - `traps`: 3–6 one-line elimination rules ("X দেখলে বাদ, কারণ …"), drawn from the actual distractors.
  - Question: `{n, s, src, q, o:[…], a, w, e}` copied exactly from raw. `w` = short why, `e` = one line on why
    the other options are wrong.
  - `cheats`: 1–3 compact `<table>` cards per topic (`{topic, title, html}`): numbers, pairs, sequences.
- Hints: `CHAPTER.hints = Object.assign(CHAPTER.hints || {}, { n: [cue, hint], … });` for EVERY question of your
  part. `cue` must be an exact substring of that question's text (or one option). `hint` nudges toward the
  answer without stating it (root meaning, sound match, number in the name, option pattern, the story).
- Terms: `CHAPTER.terms = (CHAPTER.terms || []).concat([ {t, bn, s, p:[root keys], lit, bnp?, fact}, … ]);`
  with 12–15 important terms of your part, broken into Greek/Latin/Sanskrit roots (keys in roots.js or your
  roots file). `fact` = which MCQ fact the literal meaning gives away. Scientific names count when the
  roots really help (Chlorohydra viridissima, Labeo rohita, Poekilocerus pictus …).
- **Never assign** `CHAPTER.hints = {…}` or `CHAPTER.terms = […]` directly: the other parts' data would be lost.

## Language
Simple spoken-style Bangla. Scientific terms in English where the exam uses them. No grand or flowery
phrases, no padding. Be concrete.

## Work and check in your own scratch project (never in `<repo>/chapters`)
Your task gives you a scratch dir `<scratch>`. Set it up:
```
mkdir -p <scratch>/chapters/zoo-ch2-animal-intro <scratch>/roots
cp <repo>/roots/roots.js <scratch>/roots/
cp <repo>/chapters/zoo-ch2-animal-intro/00-meta.js <scratch>/chapters/zoo-ch2-animal-intro/
```
Write your files into `<scratch>/chapters/zoo-ch2-animal-intro/`. Then:
1. `python3 <skill>/verify_raw.py <your raw file> <scratch>/chapters/zoo-ch2-animal-intro` → must print 0 problems.
2. `python3 <skill>/build.py <scratch>/chapters/zoo-ch2-animal-intro <scratch>/output` → fix every error
   until it prints "ok"; the question count must equal your raw file's count.
3. Screenshot every figure at 390px width with Playwright
   (`const { chromium } = require('/opt/node22/lib/node_modules/playwright')`, open
   `<scratch>/output/zoo-ch2-animal-intro-study.html` via file://, `page.$$('figure')`, `el.screenshot()`),
   combine them into 1–2 contact sheets with PIL, LOOK at them, and fix clipped or overlapping labels.
   Also check that `page.on('pageerror')` reports nothing.
4. Don't edit any file outside `<scratch>`. The lead copies your files into the repo afterwards.
5. Final reply (short, English is fine): file list, question/section/term counts, roots added, each ⚠ item
   with what the web said, and anything you were unsure about.
