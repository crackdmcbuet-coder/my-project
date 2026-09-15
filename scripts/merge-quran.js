#!/usr/bin/env node
/**
 * Rebuilds data/quran/{ayahs,surahs}.json from the vendored quran-json source files.
 * See vendor/quran-json/ATTRIBUTION.md and data/quran/SOURCES.md for provenance.
 *
 * Usage: node scripts/merge-quran.js
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const CH_DIR = path.join(ROOT, 'vendor/quran-json/dist/chapters');
const BN_DIR = path.join(CH_DIR, 'bn');
const OUT_DIR = path.join(ROOT, 'data/quran');

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

// The upstream quran-json@3.1.2 Bengali translation files contain a known
// mojibake artifact in 25 ayahs: an HTML numeric character reference like
// "&#2499;" (a single Bangla vowel sign / conjunct letter) got mangled by
// some step in the redistribution pipeline. The "&#" (and sometimes the
// leading "2" of a 4-digit reference too) gets replaced by one stray glyph
// from an unrelated script — observed markers: ꦣ (Javanese), ߦ (N'Ko),
// ˦ (modifier letter), 栦 (CJK), ۦ (Arabic mark) — followed by the
// surviving digits and a semicolon, e.g. "কর্তꦣ2499;ত্বের" instead of
// "কর্তৃত্বের". This is a mechanical encoding bug, NOT a translation
// choice — decoding it restores Dr. Muhiuddin Khan's actual wording rather
// than altering it. We do NOT hand-edit the translation text itself; we
// only decode this exact, unambiguous byte-level artifact (recovering a
// dropped leading "2" when only 3 digits survived, since every recovered
// codepoint in this dataset falls in the 2400-2559 Bangla-block range). A
// few instances (3:33, 20:59, 30:18) have NO surviving digits at all and
// are therefore NOT algorithmically recoverable — those are left untouched
// and flagged in data/quran/SOURCES.md for human review rather than guessed.
// See data/quran/SOURCES.md for the full before/after list.
const MOJIBAKE_ENTITY_RE = /[ꦣߦ˦栦ۦަ]#?(\d{3,4});/g;
let mojibakeFixCount = 0;

function fixMojibakeEntities(text) {
  return text.replace(MOJIBAKE_ENTITY_RE, (_match, digits) => {
    mojibakeFixCount++;
    const fullDigits = digits.length === 3 ? '2' + digits : digits;
    return String.fromCodePoint(parseInt(fullDigits, 10));
  });
}

function main() {
  const chIndex = readJson(path.join(CH_DIR, 'index.json'));
  const bnIndex = readJson(path.join(BN_DIR, 'index.json'));

  if (chIndex.length !== 114 || bnIndex.length !== 114) {
    throw new Error(`Expected 114 surahs, got ar=${chIndex.length} bn=${bnIndex.length}`);
  }

  const bnNameById = {};
  bnIndex.forEach((c) => {
    bnNameById[c.id] = c.translation;
  });

  let globalId = 0;
  const ayahs = [];
  const surahs = [];

  for (let n = 1; n <= 114; n++) {
    const ar = readJson(path.join(CH_DIR, `${n}.json`));
    const bn = readJson(path.join(BN_DIR, `${n}.json`));

    if (ar.verses.length !== bn.verses.length) {
      throw new Error(`Verse count mismatch in surah ${n}: ar=${ar.verses.length} bn=${bn.verses.length}`);
    }

    surahs.push({
      surah_number: n,
      name_ar: ar.name,
      name_transliteration: ar.transliteration,
      name_bn: bnNameById[n] || null,
      revelation_type: ar.type,
      total_verses: ar.total_verses,
    });

    for (let i = 0; i < ar.verses.length; i++) {
      const av = ar.verses[i];
      const bv = bn.verses[i];
      if (av.id !== bv.id) {
        throw new Error(`Ayah id mismatch in surah ${n} index ${i}: ar.id=${av.id} bn.id=${bv.id}`);
      }
      globalId++;
      ayahs.push({
        global_ayah_number: globalId,
        surah_number: n,
        surah_name_ar: ar.name,
        surah_name_transliteration: ar.transliteration,
        surah_name_bn: bnNameById[n] || null,
        ayah_number: av.id,
        arabic: av.text,
        bangla: fixMojibakeEntities(bv.translation),
      });
    }
  }

  if (ayahs.length !== 6236) {
    throw new Error(`Expected 6236 ayahs total, got ${ayahs.length}`);
  }

  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(path.join(OUT_DIR, 'surahs.json'), JSON.stringify(surahs, null, 2));
  fs.writeFileSync(path.join(OUT_DIR, 'ayahs.json'), JSON.stringify(ayahs));

  console.log(`Wrote ${surahs.length} surahs and ${ayahs.length} ayahs to ${OUT_DIR}`);
  console.log(`Fixed ${mojibakeFixCount} mojibake HTML-entity artifacts in the Bangla translation (see data/quran/SOURCES.md).`);
}

main();
