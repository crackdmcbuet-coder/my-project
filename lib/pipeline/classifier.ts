import type { Candidate, ClassifiedAyah, Decision, Discovery, Relevance } from './types';

const REVIEW_THRESHOLD = 0.65;

const QURAN_SOURCE = "Uthmani script, The Noble Qur'an Encyclopedia (quranenc.com)";
const TRANSLATION_SOURCE = 'Bangla translation by Dr. Muhiuddin Khan (via tanzil.net)';
const DATASET_VERSION = 'quran-json@3.1.2 / merged 2026';

function baseConfidence(d: Discovery): number {
  switch (d.found_by) {
    case 'keyword':
    case 'root':
      return 0.95;
    case 'concept':
      return d.concept_classification === 'DIRECT' ? 0.8 : 0.6;
    case 'narrative':
      return 0.75;
    case 'context':
      return 0.5;
    default:
      return 0.5;
  }
}

function relevanceOf(d: Discovery): Relevance {
  switch (d.found_by) {
    case 'keyword':
    case 'root':
      return 'DIRECT';
    case 'concept':
      return d.concept_classification ?? 'RELATED';
    case 'narrative':
      return 'STRONG_CONTEXT';
    case 'context':
      return 'RELATED';
    default:
      return 'WEAK';
  }
}

const RELEVANCE_RANK: Record<Relevance, number> = {
  DIRECT: 4,
  STRONG_CONTEXT: 3,
  RELATED: 2,
  WEAK: 1,
  IRRELEVANT: 0,
};

function reasonFor(topic: string, discoveries: Discovery[], relevance: Relevance): string {
  const parts: string[] = [];

  const keywordTerms = discoveries.filter((d) => d.found_by === 'keyword').map((d) => d.matched_term);
  if (keywordTerms.length > 0) {
    const unique = [...new Set(keywordTerms)];
    parts.push(
      `এই আয়াতে সরাসরি "${topic}" সম্পর্কিত আরবি শব্দ ব্যবহৃত হয়েছে ("${unique.join('", "')}")।`
    );
  }

  const conceptDiscoveries = discoveries.filter((d) => d.found_by === 'concept');
  for (const d of conceptDiscoveries) {
    if (d.concept_classification === 'DIRECT') {
      parts.push(`এই আয়াতে "${topic}"-এর একটি সমার্থক শব্দ ("${d.matched_term}", ${d.concept_group}) ব্যবহৃত হয়েছে।`);
    } else {
      parts.push(
        `এই আয়াতে "${d.matched_term}" (${d.concept_group}) শব্দটি রয়েছে, যা "${topic}"-এর সাথে প্রাসঙ্গিকভাবে সম্পর্কিত হলেও মূল বিষয় নয় — তাই RELATED হিসেবে চিহ্নিত।`
      );
    }
  }

  const narrativeDiscoveries = discoveries.filter((d) => d.found_by === 'narrative');
  for (const d of narrativeDiscoveries) {
    parts.push(
      `এই আয়াতটি ${d.narrative_note} এই ঘটনার অংশ; সরাসরি "${topic}" শব্দ না থাকলেও এটি ঘটনার গুরুত্বপূর্ণ প্রাসঙ্গিক অংশ (STRONG_CONTEXT)।`
    );
  }

  if (parts.length === 0) {
    parts.push(`এই আয়াতটি "${topic}"-এর সাথে সম্পর্কিত বলে চিহ্নিত হয়েছে, তবে কারণ স্পষ্টভাবে নথিভুক্ত করা যায়নি — পর্যালোচনা প্রয়োজন।`);
  }

  return parts.join(' ');
}

/**
 * Classifies one candidate ayah for one topic. Deterministic and fully
 * traceable: relevance/confidence/reason are derived only from which
 * verified search layers found the ayah and why — never from an
 * unexplained model judgment call. See lib/pipeline/types.ts Discovery.
 */
export function classifyCandidate(topic: string, candidate: Candidate): ClassifiedAyah {
  const { ayah, discoveries } = candidate;

  let relevance: Relevance = 'IRRELEVANT';
  let confidence = 0;
  for (const d of discoveries) {
    const r = relevanceOf(d);
    if (RELEVANCE_RANK[r] > RELEVANCE_RANK[relevance]) {
      relevance = r;
    }
    confidence = Math.max(confidence, baseConfidence(d));
  }

  // Small corroboration boost when independent layers agree (capped).
  const distinctFoundBy = new Set(discoveries.map((d) => d.found_by));
  if (distinctFoundBy.size > 1) {
    confidence = Math.min(0.99, confidence + 0.03 * (distinctFoundBy.size - 1));
  }

  const reviewRequired = confidence < REVIEW_THRESHOLD;
  // Decision reflects the classification itself; review_required is an
  // orthogonal flag (a RELATED or DIRECT item can still need human review —
  // see project rule 18, borderline cases apply across every category).
  const decision: Decision =
    relevance === 'RELATED' ? 'related' : relevance === 'WEAK' || relevance === 'IRRELEVANT' ? 'reject' : 'include';

  const matchedConcepts = [...new Set(discoveries.map((d) => d.matched_term))];

  return {
    surah_number: ayah.surah_number,
    surah_name_ar: ayah.surah_name_ar,
    surah_name_transliteration: ayah.surah_name_transliteration,
    surah_name_bn: ayah.surah_name_bn,
    ayah_number: ayah.ayah_number,
    arabic: ayah.arabic,
    bangla: ayah.bangla,
    topic,
    relevance,
    decision,
    reason_bn: reasonFor(topic, discoveries, relevance),
    matched_concepts: matchedConcepts,
    found_by: [...distinctFoundBy],
    confidence: Math.round(confidence * 100) / 100,
    review_required: reviewRequired,
    quran_source: QURAN_SOURCE,
    translation_source: TRANSLATION_SOURCE,
    dataset_version: DATASET_VERSION,
  };
}
