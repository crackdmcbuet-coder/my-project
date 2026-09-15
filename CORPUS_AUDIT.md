# Qur'an Corpus Audit

Generated: 2026-09-15T00:28:38.524Z

## Verdict: COMPLETE (per the checks below)

- Total Surahs: 114
- Total Ayahs: 6236
- Errors: 0
- Warnings: 0

## Counting convention used by this dataset

This corpus uses the standard Hafs-'an-'Asim mus-haf numbering (114 surahs, 6236 ayahs total) — the convention used by the vast majority of printed and digital Qur'ans worldwide, including the one this dataset was sourced from (The Noble Qur'an Encyclopedia via `quran-json`).

Bismillah handling observed in the actual data (documented, not assumed):

- Al-Fatihah ayah 1 IS the Bismillah, counted as its own numbered ayah: **true**
- Al-Baqarah ayah 1 (a surah where Bismillah is NOT separately numbered) starts with the Bismillah text prepended: **false**
- At-Tawbah (the one surah with no Bismillah at all) ayah 1 has no Bismillah text: **true**

(If Al-Baqarah 1 starts with the Bismillah text, that means the printed Bismillah before each surah is folded into the surah's first ayah's text rather than removed — verify this matches the convention your website already uses elsewhere, since some Bangla print editions omit the repeated Bismillah from ayah 1's text.)

## Spot-checks against well-documented single-surah counts

| Surah | Expected (undisputed) | Actual in dataset | OK |
|---|---|---|---|
| 1 | 7 | 7 | ✅ |
| 108 | 3 | 3 | ✅ |
| 112 | 4 | 4 | ✅ |
| 113 | 5 | 5 | ✅ |
| 114 | 6 | 6 | ✅ |

## Internal consistency checks

- Surah numbers 1-114 all present, no duplicates: ✅
- Every surah's ayah numbers are contiguous 1..N with no gaps/duplicates: ✅
- global_ayah_number spans 1..6236 with no gaps/duplicates: ✅
- Every ayah has non-empty Arabic text: ✅
- Every ayah has non-empty Bangla translation: ✅
- Surah name fields consistent across all of a surah's ayahs: ✅
- Merged total_verses matches the vendored upstream source file, per surah: ✅

## Per-surah issues

None — all 114 surahs pass every check.

## All findings

No errors or warnings.

## Known upstream translation-text issues (not corpus structure — see data/quran/SOURCES.md)

25 ayahs had a mechanically-repaired mojibake artifact in the Bangla translation; 3 ayahs have an unrecoverable version of the same artifact and are flagged as-is. These do not affect ayah counts, numbering, or Arabic text — only the cosmetic rendering of a few Bangla words. Full before/after list in `data/quran/SOURCES.md`.
