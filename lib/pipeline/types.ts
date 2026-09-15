import type { Ayah } from '../quran/types';

export type Relevance = 'DIRECT' | 'STRONG_CONTEXT' | 'RELATED' | 'WEAK' | 'IRRELEVANT';

export type FoundBy = 'keyword' | 'root' | 'concept' | 'context' | 'narrative';

export type Decision = 'include' | 'related' | 'reject' | 'review';

export interface NarrativeRef {
  surah: number;
  ayah_start: number;
  ayah_end: number;
  note: string;
}

export interface ExcludedAyahRule {
  surah: number;
  ayah: number;
  term: string;
  reason: string;
}

export interface TopicMapEntry {
  topic: string;
  generated: boolean;
  aliases_bn: string[];
  english_terms: string[];
  arabic_terms: {
    generated: boolean;
    note?: string;
    terms: string[];
    excluded_ayahs?: ExcludedAyahRule[];
    context_verified_terms?: { token: string; surah: number; ayah: number; meaning: string }[];
  };
  concept_terms?: {
    generated: boolean;
    note?: string;
    groups: { name: string; classification: Relevance; terms: string[] }[];
  };
  related_entities: {
    generated: boolean;
    entities: string[];
  };
  narrative_refs: {
    generated: boolean;
    refs: NarrativeRef[];
    note?: string;
  };
}

export interface TopicMapFile {
  schema_version: number;
  note: string;
  topics: TopicMapEntry[];
}

/**
 * One discovery event for a single ayah. A candidate can have several: the
 * same ayah may be found by more than one layer (e.g. both a keyword match
 * and a narrative-passage match), and every reason is kept for the audit
 * trail even though the final output never duplicates the ayah itself.
 */
export interface Discovery {
  found_by: FoundBy;
  matched_term: string;
  /** For 'concept' discoveries: which named synonym group the term belongs to. */
  concept_group?: string;
  /** For 'concept' discoveries: the relevance that concept group is configured to imply. */
  concept_classification?: Relevance;
  /** For 'narrative' discoveries: which narrative_ref matched. */
  narrative_note?: string;
}

export interface Candidate {
  ayah: Ayah;
  discoveries: Discovery[];
}

export interface ClassifiedAyah {
  surah_number: number;
  surah_name_ar: string;
  surah_name_transliteration: string;
  surah_name_bn: string | null;
  ayah_number: number;
  arabic: string;
  bangla: string;
  topic: string;
  relevance: Relevance;
  decision: Decision;
  reason_bn: string;
  matched_concepts: string[];
  found_by: FoundBy[];
  confidence: number;
  review_required: boolean;
  quran_source: string;
  translation_source: string;
  dataset_version: string;
}

export interface CompletenessReport {
  topic: string;
  generated_at: string;
  total_ayahs_scanned: number;
  keyword_candidates: number;
  narrative_candidates: number;
  total_candidates_before_dedup: number;
  total_candidates_after_dedup: number;
  final_direct: number;
  final_strong_context: number;
  final_related: number;
  rejected: number;
  needs_human_review: number;
  audit_checklist: { question: string; answer: string }[];
}

export interface AuditTrailEntry {
  surah_number: number;
  ayah_number: number;
  found_by: FoundBy[];
  matched_concepts: string[];
  decision: Decision;
  relevance: Relevance;
  reason_bn: string;
  confidence: number;
}

export interface TopicExtractionResult {
  topic: string;
  generated_at: string;
  total_ayahs: number;
  quran_source: string;
  translation_source: string;
  dataset_version: string;
  direct: ClassifiedAyah[];
  strong_context: ClassifiedAyah[];
  related: ClassifiedAyah[];
  review_queue: ClassifiedAyah[];
  excluded_candidates: { surah_number: number; ayah_number: number; term: string; reason: string }[];
  completeness_report: CompletenessReport;
  audit_trail: AuditTrailEntry[];
}
