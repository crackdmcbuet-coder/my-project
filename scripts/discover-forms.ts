/**
 * Dev utility: given a root substring, lists every DISTINCT normalized word
 * token in the whole corpus that contains it, with occurrence count and one
 * sample ayah ref each — so topic-map surface forms are curated from what
 * actually exists in the text, not guessed.
 *
 * Usage: npx tsx scripts/discover-forms.ts سحر
 */
import { loadAyahs } from '../lib/quran/loadCorpus';
import { normalizeArabic, arabicWords } from '../lib/quran/normalize';

const root = process.argv[2];
if (!root) {
  console.error('Usage: tsx scripts/discover-forms.ts <arabic substring>');
  process.exit(1);
}
const normRoot = normalizeArabic(root);

const ayahs = loadAyahs();
const found = new Map<string, { count: number; sample: string }>();

for (const a of ayahs) {
  const words = arabicWords(normalizeArabic(a.arabic));
  for (const w of words) {
    if (w.includes(normRoot)) {
      const entry = found.get(w) || { count: 0, sample: `${a.surah_number}:${a.ayah_number}` };
      entry.count++;
      found.set(w, entry);
    }
  }
}

const sorted = [...found.entries()].sort((a, b) => b[1].count - a[1].count);
console.log(`Root "${root}" (normalized "${normRoot}") -> ${sorted.length} distinct tokens:\n`);
for (const [token, info] of sorted) {
  console.log(`${token}\tx${info.count}\te.g. ${info.sample}`);
}
