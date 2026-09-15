import { describe, expect, it } from 'vitest';
import { classifyCandidate } from '../lib/pipeline/classifier';
import type { Ayah } from '../lib/quran/types';
import type { Candidate } from '../lib/pipeline/types';

const ayah: Ayah = {
  global_ayah_number: 1,
  surah_number: 2,
  surah_name_ar: 'البقرة',
  surah_name_transliteration: 'Al-Baqarah',
  surah_name_bn: 'বকনা-বাছুর',
  ayah_number: 102,
  arabic: 'سحر',
  bangla: 'জাদু',
};

describe('classifyCandidate', () => {
  it('classifies a keyword match as DIRECT with high confidence and no review flag', () => {
    const candidate: Candidate = {
      ayah,
      discoveries: [{ found_by: 'keyword', matched_term: 'سحر' }],
    };
    const result = classifyCandidate('জাদু', candidate);
    expect(result.relevance).toBe('DIRECT');
    expect(result.decision).toBe('include');
    expect(result.confidence).toBeGreaterThanOrEqual(0.9);
    expect(result.review_required).toBe(false);
  });

  it('classifies a narrative-only match as STRONG_CONTEXT', () => {
    const candidate: Candidate = {
      ayah,
      discoveries: [{ found_by: 'narrative', matched_term: '7:106-126', narrative_note: 'test event' }],
    };
    const result = classifyCandidate('জাদু', candidate);
    expect(result.relevance).toBe('STRONG_CONTEXT');
    expect(result.decision).toBe('include');
  });

  it('classifies a RELATED concept match as related but keeps it flagged for review if below threshold', () => {
    const candidate: Candidate = {
      ayah,
      discoveries: [
        { found_by: 'concept', matched_term: 'شفاء', concept_group: 'healing', concept_classification: 'RELATED' },
      ],
    };
    const result = classifyCandidate('রোগ', candidate);
    expect(result.relevance).toBe('RELATED');
    expect(result.decision).toBe('related');
    expect(result.review_required).toBe(true); // 0.6 confidence < 0.65 threshold
  });

  it('takes the highest-ranked relevance when multiple discoveries disagree', () => {
    const candidate: Candidate = {
      ayah,
      discoveries: [
        { found_by: 'narrative', matched_term: 'x', narrative_note: 'event' },
        { found_by: 'keyword', matched_term: 'سحر' },
      ],
    };
    const result = classifyCandidate('জাদু', candidate);
    expect(result.relevance).toBe('DIRECT');
    expect(result.found_by).toEqual(expect.arrayContaining(['narrative', 'keyword']));
  });

  it('never duplicates matched_concepts for the same term found twice', () => {
    const candidate: Candidate = {
      ayah,
      discoveries: [
        { found_by: 'keyword', matched_term: 'سحر' },
        { found_by: 'keyword', matched_term: 'سحر' },
      ],
    };
    const result = classifyCandidate('জাদু', candidate);
    expect(result.matched_concepts).toEqual(['سحر']);
  });
});
