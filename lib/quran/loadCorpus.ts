import fs from 'node:fs';
import path from 'node:path';
import type { Ayah, Surah } from './types';

const DATA_DIR = path.join(process.cwd(), 'data', 'quran');

let cachedAyahs: Ayah[] | null = null;
let cachedSurahs: Surah[] | null = null;

/**
 * Loads the full, authoritative Qur'an corpus (all 6236 ayahs / 114 surahs).
 * Cached in-process after the first call — the underlying file is never
 * written by the extractor, so this cache can never silently hide a new
 * candidate (per project rule: caching must not drop candidates).
 */
export function loadAyahs(): Ayah[] {
  if (!cachedAyahs) {
    const raw = fs.readFileSync(path.join(DATA_DIR, 'ayahs.json'), 'utf8');
    const ayahs: Ayah[] = JSON.parse(raw);
    if (ayahs.length !== 6236) {
      throw new Error(
        `Qur'an corpus integrity check failed: expected 6236 ayahs, found ${ayahs.length}. ` +
          `Refusing to run topic extraction on an incomplete corpus.`
      );
    }
    cachedAyahs = ayahs;
  }
  return cachedAyahs;
}

export function loadSurahs(): Surah[] {
  if (!cachedSurahs) {
    const raw = fs.readFileSync(path.join(DATA_DIR, 'surahs.json'), 'utf8');
    const surahs: Surah[] = JSON.parse(raw);
    if (surahs.length !== 114) {
      throw new Error(
        `Qur'an corpus integrity check failed: expected 114 surahs, found ${surahs.length}.`
      );
    }
    cachedSurahs = surahs;
  }
  return cachedSurahs;
}

export function ayahKey(surah: number, ayah: number): string {
  return `${surah}:${ayah}`;
}
