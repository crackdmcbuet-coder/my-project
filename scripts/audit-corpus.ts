/**
 * Rigorous corpus audit (Phase 2, project rule 9). Checks internal
 * consistency of the merged corpus against itself and against the vendored
 * upstream source, documents the ayah-counting convention actually used,
 * and writes CORPUS_AUDIT.md. Does NOT invent an external "expected count"
 * table — every check here is either (a) an internal consistency check
 * derivable from the data itself, (b) a cross-check against the vendored
 * upstream source files, or (c) a small number of extremely well-documented,
 * undisputed facts about the standard Hafs-'an-'Asim mus-haf (114 surahs,
 * 6236 ayahs total, and a handful of universally-agreed single-surah counts
 * used only as spot-checks, not as the basis for a pass/fail verdict).
 *
 * Usage: npx tsx scripts/audit-corpus.ts
 */
import fs from 'node:fs';
import path from 'node:path';
import { loadAyahs, loadSurahs } from '../lib/quran/loadCorpus';

const ROOT = path.join(__dirname, '..');
const VENDOR_CH_DIR = path.join(ROOT, 'vendor/quran-json/dist/chapters');

interface Issue {
  severity: 'ERROR' | 'WARNING';
  message: string;
}

const issues: Issue[] = [];
function err(msg: string) {
  issues.push({ severity: 'ERROR', message: msg });
}
function warn(msg: string) {
  issues.push({ severity: 'WARNING', message: msg });
}

const ayahs = loadAyahs();
const surahs = loadSurahs();

// 1. Top-level counts
const totalAyahs = ayahs.length;
const totalSurahs = surahs.length;
if (totalSurahs !== 114) err(`Expected 114 surahs, found ${totalSurahs}.`);
if (totalAyahs !== 6236) err(`Expected 6236 ayahs (standard Hafs mus-haf total), found ${totalAyahs}.`);

// 2. Surah numbers 1..114 present exactly once, in order
const surahNumbers = surahs.map((s) => s.surah_number);
const expectedSurahNumbers = Array.from({ length: 114 }, (_, i) => i + 1);
const missingSurahs = expectedSurahNumbers.filter((n) => !surahNumbers.includes(n));
const duplicateSurahs = surahNumbers.filter((n, i) => surahNumbers.indexOf(n) !== i);
if (missingSurahs.length) err(`Missing surah numbers: ${missingSurahs.join(', ')}`);
if (duplicateSurahs.length) err(`Duplicate surah numbers: ${[...new Set(duplicateSurahs)].join(', ')}`);
const surahsInOrder = surahNumbers.every((n, i) => n === i + 1);
if (!surahsInOrder) warn('surahs.json is not in strict ascending surah_number order.');

// 3. Per-surah ayah numbering: 1..N contiguous, no gaps, no duplicates
const ayahsBySurah = new Map<number, typeof ayahs>();
for (const a of ayahs) {
  if (!ayahsBySurah.has(a.surah_number)) ayahsBySurah.set(a.surah_number, []);
  ayahsBySurah.get(a.surah_number)!.push(a);
}

const perSurahReport: {
  surah: number;
  name: string;
  declared_total_verses: number;
  actual_ayah_count: number;
  vendor_total_verses: number | null;
  ok: boolean;
}[] = [];

for (const surah of surahs) {
  const list = (ayahsBySurah.get(surah.surah_number) ?? []).sort((a, b) => a.ayah_number - b.ayah_number);
  const ayahNumbers = list.map((a) => a.ayah_number);
  const expected = Array.from({ length: surah.total_verses }, (_, i) => i + 1);

  const missingAyahs = expected.filter((n) => !ayahNumbers.includes(n));
  const duplicateAyahs = ayahNumbers.filter((n, i) => ayahNumbers.indexOf(n) !== i);
  const extraAyahs = ayahNumbers.filter((n) => n < 1 || n > surah.total_verses);

  if (missingAyahs.length) {
    err(`Surah ${surah.surah_number} (${surah.name_transliteration}): missing ayah number(s) ${missingAyahs.join(', ')}`);
  }
  if (duplicateAyahs.length) {
    err(`Surah ${surah.surah_number} (${surah.name_transliteration}): duplicate ayah number(s) ${[...new Set(duplicateAyahs)].join(', ')}`);
  }
  if (extraAyahs.length) {
    err(`Surah ${surah.surah_number} (${surah.name_transliteration}): out-of-range ayah number(s) ${extraAyahs.join(', ')}`);
  }
  if (list.length !== surah.total_verses) {
    err(
      `Surah ${surah.surah_number} (${surah.name_transliteration}): declared total_verses=${surah.total_verses} but ${list.length} ayah records found.`
    );
  }

  // Cross-check against the vendored upstream source file directly.
  let vendorTotal: number | null = null;
  const vendorPath = path.join(VENDOR_CH_DIR, `${surah.surah_number}.json`);
  if (fs.existsSync(vendorPath)) {
    const vendorChapter = JSON.parse(fs.readFileSync(vendorPath, 'utf8'));
    vendorTotal = vendorChapter.total_verses;
    if (vendorTotal !== surah.total_verses) {
      err(
        `Surah ${surah.surah_number}: merged total_verses=${surah.total_verses} does not match vendored source total_verses=${vendorTotal}.`
      );
    }
  } else {
    warn(`Surah ${surah.surah_number}: no vendored source file found at ${vendorPath} to cross-check against.`);
  }

  perSurahReport.push({
    surah: surah.surah_number,
    name: surah.name_transliteration,
    declared_total_verses: surah.total_verses,
    actual_ayah_count: list.length,
    vendor_total_verses: vendorTotal,
    ok: list.length === surah.total_verses && vendorTotal === surah.total_verses,
  });
}

// 4. Global ayah numbering: 1..6236 contiguous, no gaps, no duplicates
const globalNumbers = ayahs.map((a) => a.global_ayah_number).sort((a, b) => a - b);
const globalMissing: number[] = [];
for (let i = 1; i <= totalAyahs; i++) {
  if (!globalNumbers.includes(i)) globalMissing.push(i);
}
const globalDuplicates = globalNumbers.filter((n, i) => globalNumbers[i - 1] === n);
if (globalMissing.length) err(`Missing global_ayah_number(s): ${globalMissing.slice(0, 20).join(', ')}${globalMissing.length > 20 ? '...' : ''}`);
if (globalDuplicates.length) err(`Duplicate global_ayah_number(s): ${[...new Set(globalDuplicates)].join(', ')}`);

// 5. Global numbering must be strictly increasing in (surah, ayah) order
let globalOrderOk = true;
for (let i = 1; i < ayahs.length; i++) {
  if (ayahs[i]!.global_ayah_number !== ayahs[i - 1]!.global_ayah_number + 1) {
    globalOrderOk = false;
    break;
  }
}
if (!globalOrderOk) warn('global_ayah_number is not strictly sequential across the file in stored order.');

// 6. Field completeness: Arabic + Bangla text non-empty for every record
let missingArabic = 0;
let missingBangla = 0;
let missingSurahNameAr = 0;
let missingSurahNameTranslit = 0;
const missingArabicRefs: string[] = [];
const missingBanglaRefs: string[] = [];
for (const a of ayahs) {
  if (!a.arabic || a.arabic.trim().length === 0) {
    missingArabic++;
    missingArabicRefs.push(`${a.surah_number}:${a.ayah_number}`);
  }
  if (!a.bangla || a.bangla.trim().length === 0) {
    missingBangla++;
    missingBanglaRefs.push(`${a.surah_number}:${a.ayah_number}`);
  }
  if (!a.surah_name_ar) missingSurahNameAr++;
  if (!a.surah_name_transliteration) missingSurahNameTranslit++;
}
if (missingArabic) err(`${missingArabic} ayah(s) with empty/missing Arabic text: ${missingArabicRefs.slice(0, 20).join(', ')}`);
if (missingBangla) err(`${missingBangla} ayah(s) with empty/missing Bangla translation: ${missingBanglaRefs.slice(0, 20).join(', ')}`);
if (missingSurahNameAr) err(`${missingSurahNameAr} ayah(s) missing surah_name_ar.`);
if (missingSurahNameTranslit) err(`${missingSurahNameTranslit} ayah(s) missing surah_name_transliteration.`);

// 7. Surah name consistency: every ayah in a given surah must carry the same surah name fields
const nameInconsistencies: string[] = [];
for (const [surahNum, list] of ayahsBySurah) {
  const arNames = new Set(list.map((a) => a.surah_name_ar));
  const translitNames = new Set(list.map((a) => a.surah_name_transliteration));
  if (arNames.size > 1 || translitNames.size > 1) {
    nameInconsistencies.push(`Surah ${surahNum}: inconsistent name fields across its ayahs.`);
  }
}
nameInconsistencies.forEach((m) => err(m));

// 8. Bismillah-handling convention documentation (not a pass/fail check — just
// records how this specific dataset represents it, since conventions vary).
const fatiha1 = ayahs.find((a) => a.surah_number === 1 && a.ayah_number === 1);
const baqarah1 = ayahs.find((a) => a.surah_number === 2 && a.ayah_number === 1);
const tawbah1 = ayahs.find((a) => a.surah_number === 9 && a.ayah_number === 1);
const bismillahConvention = {
  al_fatihah_ayah_1_is_bismillah: fatiha1?.arabic.includes('بِسۡمِ') ?? null,
  al_baqarah_ayah_1_starts_with_bismillah: baqarah1?.arabic.startsWith('بِسۡمِ') ?? null,
  at_tawbah_has_no_leading_bismillah_ayah: tawbah1 ? !tawbah1.arabic.includes('بِسۡمِ') : null,
};

// 9. Well-known, undisputed spot-checks (NOT invented — these are among the
// most universally agreed facts about the standard mus-haf; used only as a
// sanity spot-check on a handful of surahs, not as the basis for the overall
// pass/fail verdict, which rests entirely on internal + vendor-source
// cross-checks above).
const KNOWN_SPOT_CHECKS: Record<number, number> = {
  1: 7, // Al-Fatihah
  112: 4, // Al-Ikhlas
  108: 3, // Al-Kawthar
  114: 6, // An-Nas
  113: 5, // Al-Falaq
};
const spotCheckResults = Object.entries(KNOWN_SPOT_CHECKS).map(([surahStr, expectedCount]) => {
  const surahNum = Number(surahStr);
  const surah = surahs.find((s) => s.surah_number === surahNum);
  const ok = surah?.total_verses === expectedCount;
  if (!ok) {
    err(`Spot-check failed: surah ${surahNum} expected ${expectedCount} ayahs (well-documented), dataset has ${surah?.total_verses}.`);
  }
  return { surah: surahNum, expected: expectedCount, actual: surah?.total_verses ?? null, ok };
});

// ---- Write CORPUS_AUDIT.md ----
const errorCount = issues.filter((i) => i.severity === 'ERROR').length;
const warningCount = issues.filter((i) => i.severity === 'WARNING').length;
const verdict = errorCount === 0 ? 'COMPLETE (per the checks below)' : 'INCOMPLETE / ISSUES FOUND';

const lines: string[] = [];
lines.push('# Qur\'an Corpus Audit');
lines.push('');
lines.push(`Generated: ${new Date().toISOString()}`);
lines.push('');
lines.push(`## Verdict: ${verdict}`);
lines.push('');
lines.push(`- Total Surahs: ${totalSurahs}`);
lines.push(`- Total Ayahs: ${totalAyahs}`);
lines.push(`- Errors: ${errorCount}`);
lines.push(`- Warnings: ${warningCount}`);
lines.push('');
lines.push('## Counting convention used by this dataset');
lines.push('');
lines.push(
  'This corpus uses the standard Hafs-\'an-\'Asim mus-haf numbering (114 surahs, 6236 ayahs total) — ' +
    'the convention used by the vast majority of printed and digital Qur\'ans worldwide, including the one ' +
    'this dataset was sourced from (The Noble Qur\'an Encyclopedia via `quran-json`).'
);
lines.push('');
lines.push('Bismillah handling observed in the actual data (documented, not assumed):');
lines.push('');
lines.push(`- Al-Fatihah ayah 1 IS the Bismillah, counted as its own numbered ayah: **${bismillahConvention.al_fatihah_ayah_1_is_bismillah}**`);
lines.push(`- Al-Baqarah ayah 1 (a surah where Bismillah is NOT separately numbered) starts with the Bismillah text prepended: **${bismillahConvention.al_baqarah_ayah_1_starts_with_bismillah}**`);
lines.push(`- At-Tawbah (the one surah with no Bismillah at all) ayah 1 has no Bismillah text: **${bismillahConvention.at_tawbah_has_no_leading_bismillah_ayah}**`);
lines.push('');
lines.push(
  '(If Al-Baqarah 1 starts with the Bismillah text, that means the printed Bismillah before each surah is folded ' +
    'into the surah\'s first ayah\'s text rather than removed — verify this matches the convention your website ' +
    'already uses elsewhere, since some Bangla print editions omit the repeated Bismillah from ayah 1\'s text.)'
);
lines.push('');
lines.push('## Spot-checks against well-documented single-surah counts');
lines.push('');
lines.push('| Surah | Expected (undisputed) | Actual in dataset | OK |');
lines.push('|---|---|---|---|');
for (const r of spotCheckResults) {
  lines.push(`| ${r.surah} | ${r.expected} | ${r.actual} | ${r.ok ? '✅' : '❌'} |`);
}
lines.push('');
lines.push('## Internal consistency checks');
lines.push('');
lines.push(`- Surah numbers 1-114 all present, no duplicates: ${missingSurahs.length === 0 && duplicateSurahs.length === 0 ? '✅' : '❌'}`);
lines.push(`- Every surah's ayah numbers are contiguous 1..N with no gaps/duplicates: ${perSurahReport.every((r) => r.ok) ? '✅' : '❌ (see per-surah table below)'}`);
lines.push(`- global_ayah_number spans 1..6236 with no gaps/duplicates: ${globalMissing.length === 0 && globalDuplicates.length === 0 ? '✅' : '❌'}`);
lines.push(`- Every ayah has non-empty Arabic text: ${missingArabic === 0 ? '✅' : `❌ (${missingArabic} missing)`}`);
lines.push(`- Every ayah has non-empty Bangla translation: ${missingBangla === 0 ? '✅' : `❌ (${missingBangla} missing)`}`);
lines.push(`- Surah name fields consistent across all of a surah's ayahs: ${nameInconsistencies.length === 0 ? '✅' : '❌'}`);
lines.push(`- Merged total_verses matches the vendored upstream source file, per surah: ${perSurahReport.every((r) => r.vendor_total_verses === r.declared_total_verses) ? '✅' : '❌'}`);
lines.push('');

const badSurahs = perSurahReport.filter((r) => !r.ok);
if (badSurahs.length) {
  lines.push('## Per-surah issues');
  lines.push('');
  lines.push('| Surah | Name | Declared total_verses | Actual ayah records | Vendor total_verses |');
  lines.push('|---|---|---|---|---|');
  for (const r of badSurahs) {
    lines.push(`| ${r.surah} | ${r.name} | ${r.declared_total_verses} | ${r.actual_ayah_count} | ${r.vendor_total_verses} |`);
  }
  lines.push('');
} else {
  lines.push('## Per-surah issues');
  lines.push('');
  lines.push('None — all 114 surahs pass every check.');
  lines.push('');
}

lines.push('## All findings');
lines.push('');
if (issues.length === 0) {
  lines.push('No errors or warnings.');
} else {
  for (const issue of issues) {
    lines.push(`- **${issue.severity}**: ${issue.message}`);
  }
}
lines.push('');
lines.push('## Known upstream translation-text issues (not corpus structure — see data/quran/SOURCES.md)');
lines.push('');
lines.push(
  '25 ayahs had a mechanically-repaired mojibake artifact in the Bangla translation; 3 ayahs have an ' +
    'unrecoverable version of the same artifact and are flagged as-is. These do not affect ayah counts, ' +
    'numbering, or Arabic text — only the cosmetic rendering of a few Bangla words. Full before/after list in ' +
    '`data/quran/SOURCES.md`.'
);
lines.push('');

fs.writeFileSync(path.join(ROOT, 'CORPUS_AUDIT.md'), lines.join('\n'));

console.log(`Verdict: ${verdict}`);
console.log(`Errors: ${errorCount}, Warnings: ${warningCount}`);
console.log('Written to CORPUS_AUDIT.md');
if (errorCount > 0) {
  process.exitCode = 1;
}
