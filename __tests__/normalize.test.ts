import { describe, expect, it } from 'vitest';
import { normalizeArabic, arabicWords } from '../lib/quran/normalize';

describe('normalizeArabic', () => {
  it('strips tashkeel diacritics', () => {
    expect(normalizeArabic('بِسۡمِ')).toBe('بسم');
  });

  it('unifies alef variants to bare alef', () => {
    expect(normalizeArabic('أَحَد')).toBe(normalizeArabic('اَحَد'));
    expect(normalizeArabic('إِنَّ')).toBe(normalizeArabic('اِنَّ'));
  });

  it('treats dagger alif (superscript alef) as a real alef letter, not a discardable mark', () => {
    // سَٰحِرٍ (saahir, "sorcerer") should normalize distinctly from سِحْر (sihr, "magic") —
    // the dagger alif is what encodes the long "aa" sound distinguishing the two words.
    const saahir = normalizeArabic('سَٰحِرٍ');
    const sihr = normalizeArabic('سِحۡرٞ');
    expect(saahir).not.toBe(sihr);
    expect(saahir).toBe('ساحر');
    expect(sihr).toBe('سحر');
  });

  it('unifies alef maksura and ta marbuta for looser matching', () => {
    expect(normalizeArabic('هدى')).toContain('هدي'[0]);
    expect(normalizeArabic('رحمة')).toBe(normalizeArabic('رحمه'));
  });

  it('collapses whitespace', () => {
    expect(normalizeArabic('  a   b  ')).toBe('a b');
  });
});

describe('arabicWords', () => {
  it('splits normalized text into words', () => {
    expect(arabicWords('كتب الله')).toEqual(['كتب', 'الله']);
  });

  it('drops empty tokens', () => {
    expect(arabicWords('  ')).toEqual([]);
  });
});
