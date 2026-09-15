import { describe, expect, it } from 'vitest';
import { keywordSearch, conceptSearch } from '../lib/pipeline/keywordSearch';
import type { Ayah } from '../lib/quran/types';
import type { TopicMapEntry } from '../lib/pipeline/types';

const ayahs: Ayah[] = [
  {
    global_ayah_number: 1,
    surah_number: 1,
    surah_name_ar: 'test',
    surah_name_transliteration: 'Test',
    surah_name_bn: 'টেস্ট',
    ayah_number: 1,
    arabic: 'إِنَّ هَٰذَا سِحۡرٞ مُّبِينٞ',
    bangla: 'নিশ্চয় এটি স্পষ্ট জাদু।',
  },
  {
    global_ayah_number: 2,
    surah_number: 1,
    surah_name_ar: 'test',
    surah_name_transliteration: 'Test',
    surah_name_bn: 'টেস্ট',
    ayah_number: 2,
    arabic: 'نَّجَّيۡنَٰهُم بِسَحَرٖ',
    bangla: 'আমি তাদের ভোররাতে উদ্ধার করেছি।',
  },
  {
    global_ayah_number: 3,
    surah_number: 1,
    surah_name_ar: 'test',
    surah_name_transliteration: 'Test',
    surah_name_bn: 'টেস্ট',
    ayah_number: 3,
    arabic: 'وَأَلۡقَيۡنَا فِي قُلُوبِهِمُ ٱلرُّعۡبَ',
    bangla: 'এবং আমি তাদের হৃদয়ে আতঙ্ক সৃষ্টি করেছি।',
  },
];

const magicTopic: TopicMapEntry = {
  topic: 'test-magic',
  generated: false,
  aliases_bn: [],
  english_terms: [],
  arabic_terms: {
    generated: false,
    terms: ['سحر', 'بسحر'],
    excluded_ayahs: [{ surah: 1, ayah: 2, term: 'بسحر', reason: 'homonym: dawn, not magic' }],
  },
  related_entities: { generated: false, entities: [] },
  narrative_refs: { generated: false, refs: [] },
};

const fearTopic: TopicMapEntry = {
  topic: 'test-fear',
  generated: false,
  aliases_bn: [],
  english_terms: [],
  arabic_terms: { generated: false, terms: [] },
  concept_terms: {
    generated: true,
    groups: [{ name: 'terror', classification: 'DIRECT', terms: ['الرعب'] }],
  },
  related_entities: { generated: false, entities: [] },
  narrative_refs: { generated: false, refs: [] },
};

describe('keywordSearch', () => {
  it('finds ayahs containing a verified surface form', () => {
    const results = keywordSearch(ayahs, magicTopic);
    expect(results.has('1:1')).toBe(true);
  });

  it('respects excluded_ayahs to filter out known homonym false positives', () => {
    const results = keywordSearch(ayahs, magicTopic);
    // Ayah 1:2 contains the same normalized token "بسحر" but means "at dawn" —
    // it must be excluded even though the literal token matches.
    expect(results.has('1:2')).toBe(false);
  });

  it('does not match ayahs with no relevant term', () => {
    const results = keywordSearch(ayahs, magicTopic);
    expect(results.has('1:3')).toBe(false);
  });
});

describe('conceptSearch', () => {
  it('finds ayahs via a synonym concept group and tags the group name', () => {
    const results = conceptSearch(ayahs, fearTopic);
    expect(results.has('1:3')).toBe(true);
    const candidate = results.get('1:3')!;
    const discovery = candidate.discoveries[0]!;
    expect(discovery.found_by).toBe('concept');
    expect(discovery.concept_group).toBe('terror');
    expect(discovery.concept_classification).toBe('DIRECT');
  });
});
