# Vendored data: quran-json@3.1.2

Source: https://github.com/risan/quran-json (npm: quran-json@3.1.2)
License: CC-BY-SA 4.0 (see LICENSE.txt) — © Risan Bagja Pradana

Only the per-surah Arabic text files (`dist/chapters/*.json`) and per-surah Bengali
translation files (`dist/chapters/bn/*.json`) are vendored here, verbatim and
unmodified, so `scripts/merge-quran.js` can be re-run reproducibly without a network
call. See `SOURCE_README.md` for the upstream package's own documentation, and
`../../data/quran/SOURCES.md` for full provenance of the Arabic text (The Noble Qur'an
Encyclopedia) and Bangla translation (Dr. Muhiuddin Khan, via tanzil.net).

Do not hand-edit any file under `dist/`. To update the corpus, replace these files with
a newer version of the same upstream package and re-run the merge script.
