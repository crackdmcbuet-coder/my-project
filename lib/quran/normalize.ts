/**
 * Text normalization for Arabic and Bangla matching.
 *
 * IMPORTANT: normalization is only ever used to *match* against the authoritative
 * Arabic/Bangla text — the stored `arabic` / `bangla` fields on an Ayah are never
 * touched, altered, or replaced. See data/quran/SOURCES.md.
 */

// Arabic diacritics (tashkeel) + quranic annotation marks — excludes U+0670
// (dagger alif), which is handled separately below because it represents a
// real letter (a long "a" sound), not a discardable diacritic.
const ARABIC_DIACRITICS_RE =
  /[ؐ-ًؚ-ٟۖ-ۜ۟-۪ۨ-ۭـ࣓-ࣿ]/g;

/**
 * Normalizes Arabic text for search matching:
 * - strips tashkeel/diacritics and tatweel (but NOT dagger alif, see below)
 * - unifies alef variants (أ إ آ ٱ ٰ(dagger alif) -> ا)
 * - unifies alef maksura / ya (ى -> ي)
 * - unifies ta marbuta / ha (ة -> ه) for looser matching
 * - unifies hamza carriers (ؤ ئ -> ء ... kept simple: drop standalone hamza differences)
 * - collapses whitespace
 */
export function normalizeArabic(input: string): string {
  return input
    .replace(ARABIC_DIACRITICS_RE, '')
    .replace(/[آأإٱٰ]/g, 'ا') // آ أ إ ٱ ٰ -> ا
    .replace(/ى/g, 'ي') // ى -> ي
    .replace(/ة/g, 'ه') // ة -> ه
    .replace(/[ؤئ]/g, 'ء') // ؤ ئ -> ء
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Normalizes Bangla text for search matching (used only for matching topic
 * aliases against user input / topic-map content — never against the Arabic
 * ayah text itself, and never mutates the stored translation).
 */
export function normalizeBangla(input: string): string {
  return input
    .normalize('NFC')
    .replace(/[্]?\s+/g, ' ')
    .trim()
    .toLowerCase();
}

/** Tokenizes normalized Arabic text into words, for whole-word matching. */
export function arabicWords(normalizedText: string): string[] {
  return normalizedText.split(/\s+/).filter(Boolean);
}
