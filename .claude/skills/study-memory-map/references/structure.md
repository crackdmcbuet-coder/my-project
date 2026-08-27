# The fifteen parts

This is the full specification for a memory map. Read it once before writing, then
work through the parts in order — later parts reuse tables built in earlier ones, so
skipping around causes duplicated work.

The parts are numbered because they are a genuine sequence: 01–04 build the raw index,
05–08 cross-link it, 09–13 turn it into recall paths, 14–15 compress it for the last
hour before the exam. Keep the numbering visible (`.part-no`) — the reader navigates by it.

---

## PART 01 — Master map

Three concept trees, one per major topic in the chapter, plus (if the deck contains
one) the exam-weight table showing which topics appeared in which year.

Each tree goes: topic → its sub-branches → a one-line summary of what lives under each,
with a `.ref` pill. Aim for the reader to see the entire chapter's shape in one screen.

Use `.tree > ul > li > span.root` for the topic name, `span.node` for branch names.

## PART 02 — All examples together

The single most important table in the document. Every named organism / entity in the
source, with these columns:

| Organism | Group | কী জন্য গুরুত্বপূর্ণ | আর কোথায় এসেছে | কনফিউশন অ্যালার্ট |

The fourth column is the one that makes this a memory map rather than a list. If a
name appears on slides 8, 9, 17 and 24, write all four — a name that recurs is a name
the examiner likes. The fifth column is where you plant the seed that Part 05 harvests.

Then thematic clusters as `.box` cards inside a `.two` grid: disease-causing,
industrially important, medically important, food/agriculture-related. These are
regroupings of the same rows, not new content — that is the point.

## PART 03 — One organism = one complete profile

For each entity the source treats in depth (usually 3–6 of them), a `.prof` card with a
`<dl>` covering every attribute the source gives: classification, habitat, structure,
each named part, reproduction broken into its types, life cycle, special features,
economic importance, exam appearances, common confusions, related organisms.

Pull the facts from *every* slide that mentions it — the whole point is that scattered
information becomes one card.

Follow each profile with a `.link-chain`: the name, then arrows through 10–15 connected
facts. Read aloud it should sound like a chant. This is what the reader replays in the
exam hall when they see the name.

If the source is missing a section you would expect, say so in a `.gap` box immediately
after the profile, with the slide numbers that bracket the hole. Do not fill it in.

## PART 04 — Same-category comparison

Wide comparison tables where the source supports them: the classification table
(class × colour × pigment × reserve food × example × special feature), the
A-versus-B table the textbook itself provides, and any within-group splits.

Add a final row for the memory device where one exists. Leave cells blank when the
source is silent — a blank cell is honest, an invented cell is not.

## PART 05 — Confusion zone

Numbered CONFUSION blocks. Three kinds, and you want all three:

1. **Two categories that swap** — a table where each row is a question ("কোন pigment?",
   "কোন reserve food?") and the two columns are the two categories.
2. **Names that look alike** — a table of A | B | the difference the source states.
   Include cross-domain collisions (an alga and a fungus with near-identical names).
3. **Adjacent concepts** — structure vs function, pigment vs colour, reserve food vs
   cell wall, vegetative vs asexual. Format each row as
   *"প্রশ্ন দেখে যা মনে হবে"* → *"আসলে যা"* → ref. That framing is what opens the trap.

## PART 06 — Patch opening

Where confusion is worst, a `.patch` card. The fixed shape matters — each field does a
different job, and skipping one leaves the knot half-tied:

```
🔴 PATCH nn — [topic]
যা দেখে ভুল হয়   the surface feature that misleads
সঠিক তথ্য        what is actually true
কেন ভুল হয়      the mechanism of the error — why the brain slips here
শর্টকাট          a hook that makes the right answer feel inevitable
সম্পর্কিত তথ্য     the neighbouring facts that come along for free
MCQ ট্র্যাপ       the actual question form, with the distractor options
PDF-এ কোথায়      slide + page
```

The third field is the one people skip and it is the most valuable. "Both words start
with the same syllable", "the book uses the same phrase in two places", "the option list
contains three plausible answers" — naming the mechanism is what stops the error
recurring.

Expect 8–14 patches for a chapter.

## PART 07 — All numbers together

Every figure in the source: counts, percentages, sizes, temperatures, years, species
counts, chromosome numbers, durations, dosages.

| সংখ্যা | কীসের সংখ্যা | Context | Organism/Topic | Memory hook |

Use `class="num"` so digits align. Then a NUMBER CONFUSION ZONE: `.box` cards grouping
figures that are numerically close or share a digit, with the discriminator spelled out.
Nearly-equal numbers in different units are the richest trap — flag them in a `.warn`.

## PART 08 — One feature → all organisms

Bidirectional tables, one per feature family the source uses to organise things
(shape, reserve food, pigment, cell wall, body plan, disease, economic use).

Each table reads left-to-right as feature→organism and right-to-left as
organism→feature. Where the organism's own name encodes the answer, say so in a
`.hook` — those are the entries the reader never has to memorise.

## PART 09 — Reproduction network

The reproduction tree (vegetative / asexual / sexual), then one table per branch per
organism-group giving method, definition, example, special structure, and the memory
hook. Close with a method → organism table that inverts everything above, with one
column per organism group so the parallels between them are visible.

## PART 10 — Disease network

Each disease the source treats in depth gets a full table: causative organism, its
type, host, symptoms, transmission, control, MCQ clue. Then a combined
Disease ↔ Organism table covering every disease mentioned anywhere, so the reader can
scan it in either direction.

## PART 11 — Economic importance network

Beneficial and harmful, in the source's own numbering, with the reference numbers
preserved. Where a second book in the deck gives an overlapping list, show both
side by side in a `.two` grid rather than merging them — the differences between the
two lists are themselves examinable.

Close with a table of organisms that appear on *both* sides. Those are the highest-yield
names in the chapter.

## PART 12 — MCQ clue → answer network

Every question in the source — in-deck quizzes and past-year questions alike. For each:
the question, the answer, the year, which options are traps and why, and the chain of
linked facts the question sits inside.

Then a **clue-word → chain** table: given a distinctive term, what should surface. This
is the part the reader drills.

## PART 13 — Memory hooks

Hooks as `.box` cards in a `.two` grid. Use acronyms, word association, contrast,
chains, and if-this-then-that logic — whatever the material suggests.

Two rules that matter. First, never bend a fact to make a hook work; a memorable wrong
answer is worse than no hook. Second, prefer hooks that are *derivations* over hooks
that are arbitrary — "the name contains the answer" or "2 + 2 = 4" removes a fact from
memory entirely, which beats making it easier to hold.

Close with a FACT → LOGIC → HOOK table for the hardest items, where LOGIC explains why
the fact is true. A fact understood needs no hook.

## PART 14 — Rapid revision sheet

Eight blocks, in this order:

1. TOP 50 MUST-KNOW FACTS (numbered, each with a ref)
2. All pigments — `.stat` rows
3. All reserve foods — `.stat` rows
4. All confusion pairs — one line each, `A ↔ B` with the discriminator
5. All disease → organism, as one dense running paragraph
6. All organism → special feature, as one dense running paragraph
7. All reproduction methods, in a `.two` grid
8. Most likely MCQ traps — a two-column "ট্র্যাপ | সঠিক উত্তর" table

Blocks 5 and 6 are deliberately paragraphs rather than tables: at this stage the reader
is skimming for recognition, not looking things up.

## PART 15 — Master memory graph + one-page map + last-minute sheet

Three things:

- **The graph** — the chain (Group → Division → Colour → Pigment → Reserve food →
  Example → Structure → Reproduction → Disease/Economic → MCQ clue) rendered as a wide
  table with a final "connected nodes" column, plus a `.tree` per major topic.
- **ONE-PAGE MASTER MAP** — one table, topics as columns, ~11 attribute rows. The
  whole chapter at a glance.
- **LAST-MINUTE REVISION SHEET** — exactly 20 numbered lines, framed as "if you can
  read nothing else, read these". Ruthless: only facts that decide a question.

Finish with the quality-control checklist and, crucially, a `.gap` box listing what the
source did **not** contain, with slide numbers — plus a note on spellings you preserved
rather than corrected.
