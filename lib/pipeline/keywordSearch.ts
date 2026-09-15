import type { Ayah } from '../quran/types';
import { arabicWords, normalizeArabic } from '../quran/normalize';
import type { Candidate, Discovery, TopicMapEntry } from './types';

interface IndexedAyah {
  ayah: Ayah;
  words: Set<string>;
}

function buildIndex(ayahs: Ayah[]): IndexedAyah[] {
  return ayahs.map((ayah) => ({
    ayah,
    words: new Set(arabicWords(normalizeArabic(ayah.arabic))),
  }));
}

function isExcluded(topic: TopicMapEntry, surah: number, ayah: number, term: string): boolean {
  return (topic.arabic_terms.excluded_ayahs ?? []).some(
    (rule) => rule.surah === surah && rule.ayah === ayah && rule.term === term
  );
}

/**
 * Layer 1+2 — exact keyword & Arabic root/morphological surface-form search.
 * Scans the FULL corpus (every ayah passed in) against the topic's verified
 * arabic_terms list. Every term was already checked to actually occur in the
 * corpus at topic-map curation time (see scripts/discover-forms.ts).
 */
export function keywordSearch(ayahs: Ayah[], topic: TopicMapEntry): Map<string, Candidate> {
  const index = buildIndex(ayahs);
  const results = new Map<string, Candidate>();

  for (const { ayah, words } of index) {
    for (const term of topic.arabic_terms.terms) {
      const normTerm = normalizeArabic(term);
      if (!words.has(normTerm)) continue;
      if (isExcluded(topic, ayah.surah_number, ayah.ayah_number, term)) continue;

      const key = `${ayah.surah_number}:${ayah.ayah_number}`;
      const discovery: Discovery = { found_by: 'keyword', matched_term: term };
      const existing = results.get(key);
      if (existing) {
        existing.discoveries.push(discovery);
      } else {
        results.set(key, { ayah, discoveries: [discovery] });
      }
    }
  }

  return results;
}

/**
 * Layer 3 — synonym / concept search. Uses the topic's concept_terms map
 * (distinct Arabic roots that are genuine synonyms of the topic, e.g. رعب
 * for ভয়/fear). Each concept group's terms were individually verified
 * against the corpus, same as the primary arabic_terms.
 */
export function conceptSearch(ayahs: Ayah[], topic: TopicMapEntry): Map<string, Candidate> {
  const results = new Map<string, Candidate>();
  if (!topic.concept_terms) return results;

  const index = buildIndex(ayahs);

  for (const group of topic.concept_terms.groups) {
    for (const { ayah, words } of index) {
      for (const term of group.terms) {
        const normTerm = normalizeArabic(term);
        if (!words.has(normTerm)) continue;

        const key = `${ayah.surah_number}:${ayah.ayah_number}`;
        const discovery: Discovery = {
          found_by: 'concept',
          matched_term: term,
          concept_group: group.name,
          concept_classification: group.classification,
        };
        const existing = results.get(key);
        if (existing) {
          existing.discoveries.push(discovery);
        } else {
          results.set(key, { ayah, discoveries: [discovery] });
        }
      }
    }
  }

  return results;
}
