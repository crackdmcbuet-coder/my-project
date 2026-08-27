# The anchor book

A memory map organises facts. It does not, on its own, make a list of unfamiliar
names stick. A student can read "ঊর্ধ্বমুখী — বিষকাটালী, গোলমরিচ, পান" ten times and still
blank in the exam hall, because nothing in their head is already attached to those
three words.

The anchor book is the companion document that fixes that. It is built from the same
scratch notes as the map, saved as `memory-maps/<chapter-slug>-anchors.html`, and it
binds each examinable example to something the student already knows — a vegetable in
their kitchen, a Bengali idiom, the shape of an English word, the layout of their house.

Build it only when asked, or when the chapter is example-heavy and the map is already done.

---

## The card

Every anchor card has exactly seven fields, in this order. Skipping one leaves the
binding half-tied.

```
মূল তথ্য        what the book actually says, with the slide/page reference
অ্যাঙ্কর         the familiar thing
বাইন্ডিং         পরিচিত জিনিস → নতুন তথ্য, one line, in a monospace box
দৃশ্য            a 5–10 second scene. Exaggerated, absurd, funny. Not a description.
শব্দখেলা         only where a natural one exists — see below
কেন কাজ করে      one line: why this particular anchor holds
উল্টো দিক        the reverse cue — hear the fact, retrieve the name
```

The last field is the one that decides whether the card is worth anything. An anchor
that only runs name → fact is half a memory. The exam asks it the other way round.

Give each card a priority: ★★★★★ down to ★. Weight follows the source's own emphasis
and its past-question labels, not your sense of what is interesting.

---

## Where anchors come from, and when not to force one

Prefer, in this order:

1. **The name already contains the answer.** *Parthenium* → parthenogenesis.
   *Nicotiana* → andro-. *Hier*acium ≈ heir → offspring identical to the mother.
   *E*phedra → Exception. These cost nothing to remember because there is nothing to
   remember — they are derivations.
2. **A thing the student handles.** Ginger, onion and turmeric sit in one basket, so
   they belong to one card. A shim hangs down from the trellis. Chilli makes you tilt
   your face up.
3. **A Bengali word that falls out of the initials on its own.** খেজুর-পটল-তাল → খে-প-তা →
   খেপাটা, and খেপাটা means "the odd one who lives apart" — which is what ভিন্নবাড়ী means.

**If no strong natural link exists, do not manufacture one.** Write out two or three
candidate associations, say plainly which is the most memorable and why, and use that —
or say the item has no good anchor and belongs in rote drill instead. A forced mnemonic
is worse than none: the student remembers the strain of it and not the fact.

---

## Common systems before individual mnemonics

When a chapter has many similar examples — five suckers, five root-propagators, twelve
rice varieties — do **not** give each one its own mnemonic. Twelve arbitrary hooks is
twelve more things to forget.

Build one **common memory system** instead: a single scene or rhyme that holds the whole
group, from which each member is recoverable. "মাটির নিচে দুই ভাই, গাছের উপরে দুই ভাই" holds
four near-identical potato names in four different categories. "কলা-পুদিনা-আনারস খেয়ে চন্দ্র
বাঁশি বাজায়" holds all five sucker plants in one sentence.

Put these systems in their own part, before the individual cards, and refer back to them
from the cards rather than repeating them.

---

## Contrastive memory

Examples are rarely lost. They are **swapped**. So wherever two items are confusable,
build a contrast block rather than two separate cards:

```
A → this familiar thing
B → that familiar thing
তারপর: "A আর B যেন গুলিয়ে না যায় — মনে রাখবে ..."
```

The two anchors must come from *different* worlds; two anchors that both live in the
kitchen will themselves get swapped. The closing line is the actual deliverable: it must
name the single discriminator that decides the answer, not restate both definitions.

Where the source itself puts one example in two lists, say so and give the practical
rule (usually: read the options, both are defensible).

---

## Two rules that are never bent

- **The fact is not adjusted to fit the anchor.** The anchor is a handle attached to the
  fact; it never reshapes it. Keep the book's terminology and meaning exactly — including
  spellings you would otherwise correct.
- **Anything from outside the source is tagged** `[Extra explanation — PDF-এর বাইরে]`
  (in HTML, `<span class="extra">PDF-এর বাইরে</span>`). Etymology, a shop-name for a
  vegetable, the meaning of a Greek prefix — all useful as ladders, none of it examinable.
  The student must be able to see at a glance which sentences they may write in the exam.

Where a mnemonic could plant a wrong idea, explain the underlying science in the
"কেন কাজ করে" line. "মায়োসিস অর্ধেক করে, মাইটোসিস করে না" is both the reason the hook works
and the reason the fact is true — a fact understood needs no hook at all.

---

## The five closing deliverables

The book ends with five sections, in this order. They are what the student actually
opens the night before.

1. **Top 20 must-remember examples** — a table: example · what it exemplifies · a
   one-line anchor · priority. Ranked by the source's exam-weight table and its
   past-question labels.
2. **One-page memory map** — the examples clustered by anchor-world (kitchen, fruit
   stall, pond, garden, "the shelf of foreign names"), closing with a single
   `.link-chain` that walks the whole chapter in one breath.
3. **Confusing examples comparison** — the contrast blocks above.
4. **Rapid recall** — no explanations at all. Two lists: example → fact, then fact →
   example. Both directions, because only one of them is what the exam asks.
5. **Exam-style reverse recall questions** — the fact is given, the name is the answer.
   Use `<details class="qq">` so the answer hides until tapped. Include the source's own
   past questions with their real distractors, and say why each distractor is tempting.
