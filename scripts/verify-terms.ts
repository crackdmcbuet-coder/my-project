/**
 * Dev utility (not part of the production pipeline): given a list of raw Arabic
 * surface forms, reports how many times each occurs as a WHOLE WORD in the
 * authoritative corpus (after normalization), with a couple of sample refs.
 * Used while curating data/topics/topic-map.json so that only forms that
 * actually occur in the real text are ever added to a topic map.
 *
 * Usage: npx tsx scripts/verify-terms.ts سحر ساحر سحرة ...
 */
import { loadAyahs } from '../lib/quran/loadCorpus';
import { normalizeArabic, arabicWords } from '../lib/quran/normalize';

const terms = process.argv.slice(2);
if (terms.length === 0) {
  console.error('Usage: tsx scripts/verify-terms.ts <arabic term> [more terms...]');
  process.exit(1);
}

const ayahs = loadAyahs();
const indexed = ayahs.map((a) => ({
  ayah: a,
  words: new Set(arabicWords(normalizeArabic(a.arabic))),
}));

for (const term of terms) {
  const normTerm = normalizeArabic(term);
  const matches = indexed.filter((e) => e.words.has(normTerm));
  console.log(`\n"${term}" (normalized: "${normTerm}") -> ${matches.length} whole-word matches`);
  matches.slice(0, 5).forEach((m) => {
    console.log(`  ${m.ayah.surah_number}:${m.ayah.ayah_number}  ${m.ayah.arabic}`);
  });
  if (matches.length > 5) console.log(`  ... and ${matches.length - 5} more`);
}
