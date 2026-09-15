import type { Ayah } from '../quran/types';
import type { Candidate, Discovery, TopicMapEntry } from './types';

/**
 * Layer 5+6 — contextual / narrative-event search. Scans the FULL corpus for
 * ayahs that fall inside a curated narrative_ref passage range (e.g. the
 * Musa-vs-Pharaoh's-sorcerers contest for জাদু). These passages are
 * hand-curated (see data/topics/topic-map.json, generated:true) precisely
 * because a keyword search alone would miss ayahs that are clearly part of
 * the same event but don't contain the topic's literal vocabulary — e.g.
 * "so We cast down what was in his right hand and it swallowed up what they
 * had fabricated" (7:117) never says "magic" but is the climax of the magic
 * contest.
 *
 * This layer intentionally does NOT do generic "N ayahs before/after any
 * direct match" expansion — that would reintroduce exactly the kind of
 * loose, un-traceable association (e.g. pulling in every Ashab al-Kahf ayah
 * for কুকুর just because they mention the same cave) the project's
 * false-positive-control rule forbids. Every narrative_ref is a specific,
 * named, reviewable event boundary.
 */
export function narrativeSearch(ayahs: Ayah[], topic: TopicMapEntry): Map<string, Candidate> {
  const results = new Map<string, Candidate>();
  const refs = topic.narrative_refs.refs;
  if (!refs || refs.length === 0) return results;

  for (const ayah of ayahs) {
    for (const ref of refs) {
      if (
        ayah.surah_number === ref.surah &&
        ayah.ayah_number >= ref.ayah_start &&
        ayah.ayah_number <= ref.ayah_end
      ) {
        const key = `${ayah.surah_number}:${ayah.ayah_number}`;
        const discovery: Discovery = {
          found_by: 'narrative',
          matched_term: `${ref.surah}:${ref.ayah_start}-${ref.ayah_end}`,
          narrative_note: ref.note,
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
