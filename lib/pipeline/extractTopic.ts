import { loadAyahs } from '../quran/loadCorpus';
import { keywordSearch, conceptSearch } from './keywordSearch';
import { narrativeSearch } from './narrativeSearch';
import { mergeCandidates } from './dedupe';
import { classifyCandidate } from './classifier';
import { buildAuditTrail, buildCompletenessReport } from './audit';
import type { ClassifiedAyah, TopicMapEntry, TopicExtractionResult } from './types';

const QURAN_SOURCE = "Uthmani script, The Noble Qur'an Encyclopedia (quranenc.com)";
const TRANSLATION_SOURCE = 'Bangla translation by Dr. Muhiuddin Khan (via tanzil.net)';
const DATASET_VERSION = 'quran-json@3.1.2 / merged 2026';

/**
 * Runs the full extraction pipeline for one topic against the FULL Qur'an
 * corpus (all 6236 ayahs, every time — see project rule "search ALL 114
 * surahs", no pre-filtering by surah, no early return).
 *
 * Pipeline: full corpus -> keyword/root search -> concept/synonym search ->
 * narrative/context search -> merge & dedupe -> classify -> audit.
 */
export function extractTopic(topicEntry: TopicMapEntry): TopicExtractionResult {
  const ayahs = loadAyahs();

  const keywordCandidates = keywordSearch(ayahs, topicEntry);
  const conceptCandidates = conceptSearch(ayahs, topicEntry);
  const narrativeCandidates = narrativeSearch(ayahs, topicEntry);

  const merged = mergeCandidates(keywordCandidates, conceptCandidates, narrativeCandidates);

  const classified: ClassifiedAyah[] = [...merged.values()]
    .map((candidate) => classifyCandidate(topicEntry.topic, candidate))
    .sort((a, b) => a.surah_number - b.surah_number || a.ayah_number - b.ayah_number);

  const direct = classified.filter((c) => c.relevance === 'DIRECT' && c.decision === 'include');
  const strongContext = classified.filter((c) => c.relevance === 'STRONG_CONTEXT' && c.decision === 'include');
  const related = classified.filter((c) => c.decision === 'related');
  const reviewQueue = classified.filter((c) => c.review_required);

  const excludedCandidates = (topicEntry.arabic_terms.excluded_ayahs ?? []).map((rule) => ({
    surah_number: rule.surah,
    ayah_number: rule.ayah,
    term: rule.term,
    reason: rule.reason,
  }));

  const completeness_report = buildCompletenessReport({
    topic: topicEntry.topic,
    totalAyahsScanned: ayahs.length,
    keywordCandidateCount: keywordCandidates.size + conceptCandidates.size,
    narrativeCandidateCount: narrativeCandidates.size,
    mergedCandidates: merged,
    classified,
    hasArabicTerms: topicEntry.arabic_terms.terms.length > 0,
    hasConceptTerms: !!topicEntry.concept_terms && topicEntry.concept_terms.groups.length > 0,
    hasNarrativeRefs: topicEntry.narrative_refs.refs.length > 0,
  });

  const audit_trail = buildAuditTrail(classified);

  return {
    topic: topicEntry.topic,
    generated_at: new Date().toISOString(),
    total_ayahs: ayahs.length,
    quran_source: QURAN_SOURCE,
    translation_source: TRANSLATION_SOURCE,
    dataset_version: DATASET_VERSION,
    direct,
    strong_context: strongContext,
    related,
    review_queue: reviewQueue,
    excluded_candidates: excludedCandidates,
    completeness_report,
    audit_trail,
  };
}
