/**
 * Runs the extraction pipeline for every curated test topic and writes
 * exports/review files for each — used to produce the example outputs and
 * completeness reports required by the project spec (section 12, 30).
 *
 * Usage: npx tsx scripts/generate-examples.ts
 */
import { execFileSync } from 'node:child_process';
import { loadTopicMap } from '../lib/pipeline/topicMap';

const map = loadTopicMap();

for (const entry of map.topics) {
  console.log(`\n=== ${entry.topic} ===`);
  execFileSync('npx', ['tsx', 'scripts/extract-topic.ts', entry.topic], { stdio: 'inherit' });
}
