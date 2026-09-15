# Qur'an Topic Ayah Extractor & Ruqyah Ayah Knowledge System

Give it a topic in Bangla (জাদু, কুকুর, শয়তান, ভয়, ...) and it scans the **entire**
Qur'an — all 6,236 ayahs across all 114 surahs, every time, no shortcuts — and
returns the ayahs that are genuinely related to that topic: direct mentions,
the narrative events tied to it, and looser-but-real related concepts —
each with a stated reason, a confidence score, and a full audit trail of
*why* it was (or wasn't) included.

Built from scratch (this repo had no prior code, dataset, or UI) per the
project brief's two hard rules:

- **NEVER MISS** — a topic's real ayahs should be found even without the
  exact keyword (root/morphology, synonyms, narrative context).
- **NEVER INVENT** — nothing is included on vibes. Every inclusion has a
  traceable reason; every Arabic search term was verified to actually occur
  in the authoritative text before being added to a topic; the Arabic and
  Bangla text themselves are never generated, paraphrased, or altered.

## Quick start

```bash
npm install
npm run dev              # http://localhost:3000 — search UI
npm test                 # unit + regression test suite
npm run extract-topic জাদু   # CLI: run the pipeline for one topic
npm run generate-examples   # runs all 7 seed topics, writes data/exports + data/review
```

## Data sources (see `data/quran/SOURCES.md` for full detail)

| | Source | License |
|---|---|---|
| Arabic text (Uthmani script) | [The Noble Qur'an Encyclopedia](https://quranenc.com) | via `quran-json@3.1.2`, CC-BY-SA 4.0 |
| Bangla translation | Dr. Muhiuddin Khan, via [tanzil.net](https://tanzil.net/trans/bn.bengali) | via `quran-json@3.1.2`, CC-BY-SA 4.0 |

The source files are vendored under `vendor/quran-json/` (not a runtime
dependency — just the raw per-surah JSON, so the corpus can be rebuilt
reproducibly offline with `npm run merge-quran`). `data/quran/ayahs.json` and
`surahs.json` are the resulting authoritative corpus — 6,236 ayahs, 114
surahs, verified counts, never overwritten by the extractor itself.

`SOURCES.md` also documents a data-quality issue found and fixed during this
build: 25 ayahs in the upstream Bangla translation had a mojibake artifact
(a mangled HTML entity) that was mechanically decoded back to the intended
character — not rewritten. 3 ayahs have an unrecoverable version of the same
artifact and are flagged, left untouched, rather than guessed at.

## Architecture

```
data/quran/ayahs.json (6236 ayahs, authoritative, immutable)
        │
data/topics/topic-map.json  ── curated Topic Knowledge Map (per topic:
        │                       verified Arabic terms, synonym concept groups,
        │                       curated narrative passages)
        ▼
lib/pipeline/keywordSearch.ts   → Layer 1+2: exact + root/morphological surface-form
                                   search, and Layer 3: synonym/concept search —
                                   both run against the FULL 6236-ayah corpus
lib/pipeline/narrativeSearch.ts → Layer 5+6: context/narrative-event search
                                   (curated passage ranges, e.g. the Musa vs.
                                   Pharaoh's-sorcerers contest)
lib/pipeline/dedupe.ts          → merges all layers, one entry per ayah,
                                   every discovery reason kept for audit
lib/pipeline/classifier.ts      → DIRECT / STRONG_CONTEXT / RELATED / WEAK /
                                   IRRELEVANT + confidence + Bangla reason,
                                   derived only from which layer(s) found it
lib/pipeline/audit.ts           → completeness report + full audit trail
lib/pipeline/extractTopic.ts    → orchestrates all of the above
        │
        ├─ scripts/extract-topic.ts  (CLI)          → data/exports/<topic>.json
        │                                              data/review/<topic>.json
        └─ app/api/extract/route.ts (live API)      → app/page.tsx (search UI)
```

### Why not a generic Arabic morphology engine / embeddings model?

Two deliberate scope decisions, both documented here rather than hidden:

1. **Surface forms are curated per topic, not derived by a generic stemmer.**
   Arabic root-and-pattern morphology is genuinely hard to get right
   generically, and a wrong guess here means either a missed ayah or (worse)
   a false positive presented as authoritative. Instead, `scripts/discover-forms.ts`
   lists every real token in the corpus containing a candidate root, and each
   one was manually reviewed against its actual ayah before being added to
   `topic-map.json` — see the `note` field on each topic's `arabic_terms` for
   the false positives that were caught and excluded this way (e.g. "سحر"
   the noun *magic* vs. "سَحَر" *dawn*, an exact homonym once diacritics are
   stripped; or "مرض" *disease* vs. unrelated words like "مرضاة" *pleasure*
   that happen to contain the same three letters).
2. **No embeddings-based semantic search.** The "semantic" layer required by
   the spec is implemented as curated `narrative_refs` (named, reviewable
   event boundaries — e.g. Al-A'raf 7:106-126 for the magic-contest
   narrative) rather than a generic "top-K nearest neighbor" search. A vector
   search would satisfy NEVER MISS more automatically, but makes NEVER
   INVENT much harder to guarantee without a human-reviewed relevance model
   in front of it. This is a conscious trade-off toward precision and
   auditability, documented as a limitation below.

Both are easy to extend without changing the pipeline's shape — see "Adding
a new topic" below.

## Relevance classification

| Relevance | Meaning | Included by default? |
|---|---|---|
| `DIRECT` | Direct keyword/root match, or a genuine lexical synonym | Yes |
| `STRONG_CONTEXT` | No literal keyword, but part of a curated narrative event | Yes |
| `RELATED` | Real but looser relationship (e.g. healing vs. disease) | Shown in its own section |
| `WEAK` / `IRRELEVANT` | Not surfaced by this pipeline at all (nothing is force-classified into these — a deterministic pipeline only ever proposes candidates it can justify) | No |

Every classified ayah carries `confidence` (0-1) and `review_required`
(true when confidence is below 0.65 — an orthogonal flag, so a `RELATED`
or even `DIRECT` item can still be marked for human review rather than
silently trusted).

## Adding a new topic

New topics are **not** accepted as free text against an un-curated Arabic
term list — that would mean guessing Arabic vocabulary on the fly, which
this project's rule 34 explicitly forbids ("BLOCKED: <missing item>", never
fabricate). To add one:

1. Use `scripts/discover-forms.ts <arabic root>` to list every real
   corpus token containing that root, with sample ayah refs.
2. Review each token's ayah(s) — Arabic roots frequently collide with
   unrelated words (see the two examples above). Keep only the tokens that
   are genuinely about the topic.
3. Add an entry to `data/topics/topic-map.json` with the verified
   `arabic_terms.terms` list, any genuine synonym `concept_terms`, and any
   curated `narrative_refs`. Mark AI-curated fields (`related_entities`,
   `narrative_refs`, and any concept expansion beyond the primary root) with
   `"generated": true` per rule 24 — they still only ever point at real
   ayahs, never invented text.
4. Run `npm run extract-topic <টপিক>` and sanity-check the output, then
   `npm test` to make sure nothing else broke.

## Example outputs & completeness reports

`data/exports/<topic>.json` — website-ready export for each of the 7 seed
topics (জাদু, কুকুর, শয়তান, পানি, আগুন, ভয়, রোগ), each including its
`completeness_report` (ayahs scanned, candidates per layer, final counts,
and a self-audit checklist per project rule 16).

`data/review/<topic>.json` — the review queue (low-confidence candidates)
and the full per-ayah audit trail (which layer found it, why, what decision
was made) per project rule 17-18.

## Test suite

- `__tests__/normalize.test.ts` — Arabic normalization, including the
  dagger-alif fix that distinguishes سَاحِر (sorcerer) from سِحْر (magic).
- `__tests__/keywordSearch.test.ts`, `classifier.test.ts` — unit tests
  against synthetic ayahs, isolated from the real corpus.
- `__tests__/regression.test.ts` — runs the real pipeline against the real
  corpus for all 7 seed topics and locks in known-correct results (e.g. that
  2:102 is found for জাদু, that 54:34 is *not*, that কুকুর never balloons
  past its 4 verified direct ayahs) — this is the regression suite required
  by project rule 31, so a future pipeline change that reintroduces a missed
  ayah or a false positive fails CI instead of shipping silently.

## Limitations (stated plainly, not hidden)

- Arabic text is the Uthmani script from The Noble Qur'an Encyclopedia, not
  a Tanzil-branded XML file specifically (the user's original preference)
  — both are standard unmodified Uthmani mus-haf text; see `SOURCES.md` for
  how to swap the source if a specific file is required.
- 3 ayahs (3:33, 20:59, 30:18) carry an unrecoverable upstream encoding
  artifact in the Bangla translation (a stray character with no surviving
  data to reconstruct it from) — flagged in `SOURCES.md`, left untouched
  rather than guessed.
- New topics require manual curation (see above) — this is intentional, not
  a missing feature; see "Why not a generic morphology engine" above.
- The "semantic" layer is curated narrative passages, not a general vector
  search — see the same section.
