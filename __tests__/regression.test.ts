/**
 * Regression suite (project rule 31): once the extractor works, this locks
 * in known-correct results for the seed topics so future pipeline changes
 * can't silently reintroduce a missed ayah (NEVER MISS) or a false positive
 * (NEVER INVENT) without a test failing.
 */
import { describe, expect, it } from 'vitest';
import { resolveTopic } from '../lib/pipeline/topicMap';
import { extractTopic } from '../lib/pipeline/extractTopic';

function surahAyahSet(list: { surah_number: number; ayah_number: number }[]): Set<string> {
  return new Set(list.map((a) => `${a.surah_number}:${a.ayah_number}`));
}

describe('regression: জাদু (magic)', () => {
  const topic = resolveTopic('জাদু')!;
  const result = extractTopic(topic);
  const directKeys = surahAyahSet(result.direct);
  const strongKeys = surahAyahSet(result.strong_context);

  it('scans the full corpus every time', () => {
    expect(result.completeness_report.total_ayahs_scanned).toBe(6236);
  });

  it('finds the Harut and Marut ayah as DIRECT', () => {
    expect(directKeys.has('2:102')).toBe(true);
  });

  it('finds Musa-vs-Pharaoh sorcerer-contest ayahs as DIRECT via keyword', () => {
    expect(directKeys.has('7:109')).toBe(true);
    expect(directKeys.has('20:69')).toBe(true);
    expect(directKeys.has('26:34')).toBe(true);
  });

  it('finds the staff-swallows-the-illusion climax as STRONG_CONTEXT even without the keyword', () => {
    expect(strongKeys.has('7:117')).toBe(true);
  });

  it('excludes the dawn/sihr homonym at 54:34 (NEVER INVENT / false-positive control)', () => {
    expect(directKeys.has('54:34')).toBe(false);
    expect(strongKeys.has('54:34')).toBe(false);
  });
});

describe('regression: কুকুর (dog) — false-positive control', () => {
  const topic = resolveTopic('কুকুর')!;
  const result = extractTopic(topic);
  const directKeys = surahAyahSet(result.direct);

  it('finds the Ashab al-Kahf dog ayahs', () => {
    expect(directKeys.has('18:18')).toBe(true);
    expect(directKeys.has('18:22')).toBe(true);
  });

  it('finds the dog parable and the hunting-dogs ayah', () => {
    expect(directKeys.has('7:176')).toBe(true);
    expect(directKeys.has('5:4')).toBe(true);
  });

  it('does NOT pull in other Ashab al-Kahf ayahs just because they share the cave narrative', () => {
    // 18:9 opens the cave narrative but never mentions the dog — must not be included.
    expect(directKeys.has('18:9')).toBe(false);
    expect(result.strong_context.length).toBe(0);
  });

  it('total direct matches stay at exactly the 4 verified dog ayahs', () => {
    expect(result.direct.length).toBe(4);
  });
});

describe('regression: রোগ (disease)', () => {
  const topic = resolveTopic('রোগ')!;
  const result = extractTopic(topic);
  const directKeys = surahAyahSet(result.direct);
  const relatedKeys = surahAyahSet(result.related);

  it('finds Ibrahim (AS) declaring his own illness', () => {
    expect(directKeys.has('26:80')).toBe(true);
  });

  it('finds "the sick" (al-mardaa) exemption ayah', () => {
    expect(directKeys.has('9:91')).toBe(true);
  });

  it('classifies healing (shifa) mentions as RELATED, not DIRECT (rule 15: Ruqyah usefulness != topic relevance)', () => {
    expect(relatedKeys.has('16:69')).toBe(true);
    expect(directKeys.has('16:69')).toBe(false);
  });

  it('does not treat "pleasing to Allah" (mardaatillah, unrelated root) as disease-related', () => {
    // 9:1 area / mardaat-Allah phrasing must never surface here.
    const allKeys = new Set([...directKeys, ...relatedKeys]);
    for (const key of allKeys) {
      const [s, a] = key.split(':').map(Number);
      const item = [...result.direct, ...result.related].find(
        (x) => x.surah_number === s && x.ayah_number === a
      )!;
      expect(item.matched_concepts.join(' ')).not.toMatch(/مرضات|مرضاة/);
    }
  });
});

describe('regression: every seed topic runs cleanly', () => {
  const topics = ['জাদু', 'কুকুর', 'শয়তান', 'পানি', 'আগুন', 'ভয়', 'রোগ'];

  it.each(topics)('%s produces a non-empty, fully-sourced result', (topicName) => {
    const topic = resolveTopic(topicName)!;
    expect(topic).toBeTruthy();
    const result = extractTopic(topic);
    expect(result.direct.length + result.strong_context.length).toBeGreaterThan(0);
    expect(result.completeness_report.total_ayahs_scanned).toBe(6236);
    for (const ayah of [...result.direct, ...result.strong_context, ...result.related]) {
      expect(ayah.quran_source).toMatch(/Uthmani/);
      expect(ayah.translation_source).toMatch(/Muhiuddin Khan/);
      expect(ayah.arabic.length).toBeGreaterThan(0);
      expect(ayah.bangla.length).toBeGreaterThan(0);
    }
  });
});
