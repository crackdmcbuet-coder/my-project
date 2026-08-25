---
name: study-memory-map
description: >
  Turn a class-note or lecture-slide PDF into an interconnected "memory map" — a
  fifteen-part HTML study database that links every organism, term, number, disease and
  MCQ to everything related to it, with a slide/page reference on each fact. Built for
  Bengali medical/dental admission (MAT/DAT) biology notes but works for any exam
  chapter. Use this whenever someone uploads a class note, lecture deck, coaching-centre
  PDF, or textbook chapter and wants it turned into notes, a revision sheet, a summary,
  a cheat sheet, a mind map, a confusion list, or anything they will study from —
  including when they only say "make notes from this PDF" or "সব একসাথে সাজাও" without
  naming a format. Also use it when someone asks to extend, correct, or add a chapter to
  a memory map that already exists in memory-maps/.
---

# Study memory map

Someone revising for an admission test does not fail because a fact was missing from
their notes. They fail because two facts sat in different places and got swapped in the
exam hall. A summary makes the notes shorter; it does not fix that. This skill builds
the opposite of a summary: everything is kept, and the value comes from how densely it
is cross-linked.

The target behaviour for the reader is: see a name → its properties surface; see a
property → the organisms surface; and the moment two things could be confused, the
distinction is already sitting next to them.

Work through it in three stages: **read the whole source**, **build the index**, **cross-link it**.

---

## Stage 1 — Read every page

Coaching-centre class notes are almost always screenshots of slides with handwritten
annotations on top. There is no text layer, and OCR destroys the handwriting — which is
where the teacher's emphasis lives (★★★, "100%", "বাদ", circled options, mnemonics in the
margin). That emphasis is often more predictive of the exam than the printed text, so it
has to be read visually.

```bash
python3 <repo>/.claude/skills/study-memory-map/scripts/pdf_to_pages.py note.pdf pages --check-only
```

Use the script's absolute path — the shell's working directory is not always the repo root,
and a relative path fails with a confusing "No such file" that looks like the skill is missing.

If it reports a text layer, extract text instead — far cheaper. If not, drop
`--check-only` to render every page, then read the PNGs **one at a time, in order**.

Two things make this stage work:

**Take notes as you go, in a scratch file, page by page.** A seventy-page deck cannot be
held in working memory well enough to write a page-referenced document afterwards.
Transcribe each page into text — the printed content, the highlighted phrases, the
handwritten marginalia, the figure captions and their labels — under a heading like
`p17 [বই পৃ.১৯৭]`. That scratch file becomes the source you write the map from, and it is
what lets every fact carry a real reference instead of a guessed one.

**Record the annotations as data, not decoration.** `★★★` next to a table, `100% common`,
`MCQ Must`, `বাদ`, a circled distractor, `NO = Nostoc, Oscillatoria` in a margin — all of
these belong in the notes and later in the map. A hook the teacher invented is better
than one you invent, because the student already heard it said aloud.

Do not skip the quiz and past-question slides. They anchor Part 12 and they tell you
which confusions the examiner actually exploits.

---

## Stage 2 — Build the map

Read `references/structure.md` for the full fifteen-part specification. Write the parts
in order; later ones reuse tables from earlier ones.

The fifteen parts are a frame, not a quota. A chapter may simply not contain what a part
asks for — a plant-reproduction chapter has no diseases, a taxonomy chapter may have no
numbers worth collecting. Don't pad the part with thin material and don't silently drop
it: give that slot to the closest thing the chapter *does* have a dense many-to-many
mapping for (in the plant-reproduction case, the before-fertilisation → after-fertilisation
table, which is the single most-examined mapping in the chapter), keep the part number, and
say in one line at the top what it now holds and why. The point of the part is the
cross-linking it forces, not its title.

Compose the HTML in chunks — one file per part in a build directory, then concatenate —
rather than one enormous write. It keeps each part editable and makes tag-balance
checking meaningful. Start from `assets/template-head.html`, which carries the full
stylesheet and documents every class name; change the `<title>` and the six accent
colours, and append your parts.

Before publishing, check that tags balance:

```bash
python3 -c "
import re,sys
h=open(sys.argv[1]).read()
for t in ['dt','dd','dl','tr','td','th','table','section','ul','li','div','span','b','i','p']:
    o=len(re.findall(r'<%s[ >]'%t,h)); c=len(re.findall(r'</%s>'%t,h))
    print(t,o,c,'OK' if o==c else '<<< MISMATCH')
" memory-maps/your-file.html
```

A stray `</dd>` closing a `<dt>` will not throw an error, it will silently wreck a
profile card. This check catches it in a second.

Save the finished page to `memory-maps/<chapter-slug>.html`, publish it as an Artifact
so it is readable on a phone, and send the file with `SendUserFile` so it can be
downloaded and opened offline.

---

## The source rule

The student will revise from this document and will not go back to check it. Anything
invented here becomes something they confidently write down wrong. So:

- **Nothing enters the map that is not in the source.** Not general subject knowledge,
  not a fact you are sure of, not a "helpful" addition. If a comparison table has a cell
  the source never fills, leave it blank.
- **Where the source is unclear or a section is absent, say so explicitly** —
  `[PDF-এ অস্পষ্ট]` or `[PDF-এ অনুপস্থিত]` — with the slide numbers that bracket the gap.
  A named hole is useful; the student can go find that page. A silently filled hole is
  a lie with a page reference attached to it.
- **Preserve the source's spellings**, even wrong ones (`Ocillatoria`, `Chladophora`,
  `Mycrocystis`). The exam may reuse them, and a student who has only seen the corrected
  form will hesitate. Note the correct form alongside if it helps, but do not replace.
- **Where two books in the same deck disagree**, show both with their own references
  rather than merging. The disagreement is itself examinable.
- **A source also contradicts itself.** The same fact can appear twice in one book with
  different values — a variety numbered BR-15 on one page and BR-16 on another. Don't
  quietly pick one, and don't average them. Record both with their page numbers, say
  plainly that the source is inconsistent, and give the student the discriminator that
  actually decides it (usually which list or context the question is asking about). An
  inconsistency you name is a fact they can use; one you resolve for them is a coin flip
  you made on their behalf.

---

## Cross-referencing instead of repeating

A fact that appears on three slides gets written once, in the place it belongs, with all
three references on it: `[স্লা.১৬, ২৪, ৭৭]`. Everywhere else, it is a link rather than a
repeat — Part 02's "আর কোথায় এসেছে" column, or a pointer in prose.

But context is content. If slide 16 gives *Nostoc* as a fragmentation example and slide 22
gives it as a nitrogen fixer, those are two facts, not one fact twice. The test is whether
the second mention teaches something new. If it does, keep it. If it is the same sentence
again, cross-reference it.

Names that recur across many contexts are the highest-yield material in the chapter —
worth flagging as such where you notice them.

---

## Referencing

Every substantive fact carries a `.ref` pill: the slide number and, where the deck shows
it, the textbook page — `[স্লা.১৯ · পৃ.১৯৮]`. Multiple sources: `[স্লা.১৬, ২৪ · পৃ.১৯৭, ২০২]`.

Slide numbers are counted from the rendered PNGs, so `p017.png` is `স্লা.১৭`. Keep those
two numbering systems distinct and label them — the deck's own page badges refer to the
textbook, not to the PDF.

---

## Writing it

The document is Bengali. Keep organism names in Latin italics (`<i>`), bold them on first
mention in a row, and give Bengali + English + scientific name together wherever the
source does.

Almost nothing should be a paragraph. Tables, nested bullets, arrows (`→`), bidirectional
links (`↔`), trees, confusion boxes, hooks. The two exceptions are the running-paragraph
blocks in Part 14, where the reader is skimming for recognition rather than looking
something up.

Weight follows the source's own emphasis. A topic the deck marks `★★★` and lists against
six exam years gets a full profile card; a topic marked `★` and never examined gets a
table row. Reproducing the teacher's emphasis is part of reproducing the teacher's note.

---

## Extending an existing map

If `memory-maps/` already holds the chapter, republish to the **same Artifact URL** by
passing `url` — a new link orphans whatever the student has already bookmarked. Read the
existing file first, keep the part structure and the accent palette, and integrate new
material into the existing tables rather than appending a new section. A second
"all examples" table defeats the whole point.
