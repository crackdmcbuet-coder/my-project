# Qur'an Dataset — Source Integrity

This directory contains the **authoritative, unmodified** Qur'an corpus used by the
Topic Ayah Extractor. Nothing in `ayahs.json` / `surahs.json` is generated, paraphrased,
or altered by AI. Every field is copied verbatim from the sources below.

## Arabic Text

- **Script**: Uthmani (Al-Rasm Al-Uthmani)
- **Source**: [The Noble Qur'an Encyclopedia](https://quranenc.com/en/home) (quranenc.com)
- **Retrieved via**: [`quran-json`](https://github.com/risan/quran-json) npm package v3.1.2
  (CC-BY-SA 4.0), which redistributes the QuranEnc Uthmani text verbatim.
- **Verification**: total ayah count = 6236, total surah count = 114 — matches the
  standard Uthmani mus-haf count exactly (cross-checked programmatically at build time,
  see `scripts/merge-quran.js`).

> Note: the user's original preference was Tanzil.net's Uthmani text specifically.
> `quran-json`'s Arabic text comes from The Noble Qur'an Encyclopedia rather than Tanzil
> directly. Both are standard, unmodified Uthmani mus-haf text; the Bangla translation
> paired with it (below) *is* the exact Tanzil-hosted Muhiuddin Khan translation. If a
> byte-for-byte Tanzil Arabic XML is required instead, swap the source in
> `scripts/merge-quran.js` — the rest of the pipeline is source-agnostic.

## Bangla Translation

- **Translator**: Dr. Muhiuddin Khan
- **Source**: [tanzil.net/trans/bn.bengali](https://tanzil.net/trans/bn.bengali)
- **Retrieved via**: `quran-json` npm package v3.1.2, `dist/chapters/bn/*.json`
  (same package, same license, redistributing Tanzil's Muhiuddin Khan text verbatim).

## Dataset Version

- `quran-json@3.1.2` (published to npm, tarball sha of package used: see `package-lock.json`
  entry `quran-json` if the package is kept as a dependency; here it was used only as a
  one-time data source and is not a runtime dependency).
- Merge performed: see `scripts/merge-quran.js`.
- `data/quran/ayahs.json` — 6236 records, flat array, one per ayah, globally numbered.
- `data/quran/surahs.json` — 114 records, one per surah.

## Ayah Record Schema

```jsonc
{
  "global_ayah_number": 1,        // 1..6236, sequential across the whole mus-haf
  "surah_number": 1,              // 1..114
  "surah_name_ar": "الفاتحة",
  "surah_name_transliteration": "Al-Fatihah",
  "surah_name_bn": "সূচনা",
  "ayah_number": 1,               // ayah number within the surah
  "arabic": "بِسۡمِ ٱللَّهِ...",  // authoritative Uthmani text, verbatim
  "bangla": "শুরু করছি আল্লাহর নামে..." // Muhiuddin Khan translation, verbatim
}
```

## Known upstream data-quality fix (documented, mechanical, not a translation edit)

The upstream `quran-json@3.1.2` Bengali translation files contain a mojibake
artifact in 25 ayahs: an HTML numeric character reference such as `&#2499;`
(representing a single Bangla vowel sign or conjunct letter) was corrupted by
some step in the redistribution pipeline — the `&#` (and sometimes the
leading `2` of a 4-digit reference too) was replaced by one stray glyph from
an unrelated script, followed by whichever digits and the semicolon
survived — e.g. `কর্তꦣ2499;ত্বের` instead of `কর্তৃত্বের`.

This is a mechanical encoding bug, not a translation choice, so
`scripts/merge-quran.js` decodes this exact artifact back to the character it
encodes (`fixMojibakeEntities`) — it does **not** hand-edit or rephrase any
translation text. The 25 recoverable ayahs:

| Surah:Ayah | Corrupted fragment | Decoded to |
|---|---|---|
| 2:230  | `কতৃꦣ2453;` | `কতৃক` |
| 3:125  | `চিহিߦ#2468;` | `চিহিত` |
| 5:9    | `তা˦#2503;দরকে` | `তাদেরকে` |
| 6:83   | `সম্প্রަ#2470;ায়ের` | `সম্প্রদায়ের` |
| 10:83  | `কর্তꦣ2499;ত্বের` | `কর্তৃত্বের` |
| 11:40  | `পূর্বহেߦ#2439;` | `পূর্বহইে`* |
| 12:76  | `কিু栦#2438;ল্লাহ` | `কিুআল্লাহ`* |
| 13:4   | `খজ্জꦣ2497;র` | `খজ্জুর` |
| 16:7   | `পরিশ্রۦ#2478;` | `পরিশ্রম` |
| 16:44  | `নিꦣ2503;দশাবলী` | `নিদর্শাবলী` |
| 17:59  | `কতৃꦣ2453;` | `কতৃক` |
| 20:96  | `পদচিহেߦ#2480;` | `পদচিহের`* |
| 22:3   | `সম্পꦣ2503;ক` | `সম্পর্কে`* |
| 23:68  | `সম্পꦣ2503;ক` | `সম্পর্কে`* |
| 23:71  | `মধ্যবর্তꦣ2496;` | `মধ্যবর্তী` |
| 23:88  | `কতৃর্ꦣ2468;্ব` | `কতৃর্ত্ব`* |
| 24:55  | `শাসনকতৃꦣ2468;্ব` | `শাসনকতৃত্ব`* |
| 28:40  | `সমু˦#2503;দ্র` | `সমুদ্র` |
| 28:46  | `পূꦣ2503;ব` | `পূর্বে`* |
| 28:71  | `কর্ণꦣ2474;াত` | `কর্ণপাত` |
| 30:18  | `মধ্যাহেߦ#2404;` | `মধ্যাহে।`* |
| 47:4   | `তা˦#2503;দরকে` | `তাদেরকে` |
| 51:34  | `চিহিߦ#2468;` | `চিহিত` |
| 52:48  | `পালনকর্তꦣ2494;র` | `পালনকর্তার` |
| 82:19  | `কতৃꦣ2468;্ব` | `কতৃত্ব` |

\* A handful of these words still look slightly irregular after decoding
(e.g. a missing conjunct consonant elsewhere in the same word, unrelated to
the entity artifact itself). That residual imperfection was already present
upstream in `quran-json@3.1.2`, and per project rule 9/10 (never invent or
rewrite translation text) it is left as-is and flagged here rather than
"corrected" by guessing — only the unambiguous, byte-level HTML-entity
artifact was decoded.

### Unrecoverable instances (flagged, left untouched — FLAG FOR REVIEW)

Three ayahs have the same kind of stray glyph but with **no surviving digits**
at all, so there is no mechanical way to recover the original character
without guessing. Per project rule 9 ("if the Arabic/translation text is in
doubt, FLAG FOR REVIEW — never change it yourself"), these are left exactly
as received from upstream:

| Surah:Ayah | Text as received (stray character present) |
|---|---|
| 3:33  | `নূহ (আঃ)͠ও ইব্রাহীম (আঃ)` |
| 20:59 | `পূর্বাহেߠলোকজন সমবেত হওয়ার দিন` |
| 30:18 | `এবং অপরাহেߠও মধ্যাহে।` |

If a fully clean Muhiuddin Khan text is later sourced, swap it in
`scripts/merge-quran.js` and re-run — this would resolve both the recoverable
and unrecoverable cases above at once.

## Immutability

This directory is **never** overwritten by the extractor. Topic extraction output is
written only under `data/topics/`, `data/exports/`, and `data/review/`.
