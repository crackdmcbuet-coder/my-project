import type { Candidate } from './types';

/**
 * Merges candidate maps from every search layer into one map, keyed by
 * "surah:ayah", combining ALL discovery reasons for an ayah that was found
 * by more than one layer (project rule 25: no duplicate ayahs in output,
 * but every discovery reason is kept internally for the audit trail).
 */
export function mergeCandidates(...layers: Map<string, Candidate>[]): Map<string, Candidate> {
  const merged = new Map<string, Candidate>();

  for (const layer of layers) {
    for (const [key, candidate] of layer) {
      const existing = merged.get(key);
      if (existing) {
        existing.discoveries.push(...candidate.discoveries);
      } else {
        merged.set(key, { ayah: candidate.ayah, discoveries: [...candidate.discoveries] });
      }
    }
  }

  return merged;
}
