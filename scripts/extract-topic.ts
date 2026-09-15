/**
 * CLI: run the full extraction pipeline for one curated topic and write its
 * website export + review queue to disk.
 *
 * Usage: npx tsx scripts/extract-topic.ts জাদু
 */
import fs from 'node:fs';
import path from 'node:path';
import { resolveTopic } from '../lib/pipeline/topicMap';
import { extractTopic } from '../lib/pipeline/extractTopic';

const topicArg = process.argv[2];
if (!topicArg) {
  console.error('Usage: tsx scripts/extract-topic.ts <topic-in-bangla>');
  process.exit(1);
}

const topicEntry = resolveTopic(topicArg);
if (!topicEntry) {
  console.error(
    `BLOCKED: টপিক "${topicArg}" এখনো data/topics/topic-map.json এ যোগ করা হয়নি। ` +
      `নতুন টপিক যোগ করতে README.md এর "Adding a new topic" অংশ দেখুন।`
  );
  process.exit(1);
}

const result = extractTopic(topicEntry);

const exportsDir = path.join(process.cwd(), 'data', 'exports');
const reviewDir = path.join(process.cwd(), 'data', 'review');
fs.mkdirSync(exportsDir, { recursive: true });
fs.mkdirSync(reviewDir, { recursive: true });

const slug = topicEntry.topic;

// Website-facing export: DIRECT + STRONG_CONTEXT by default, RELATED in its own section.
const websiteExport = {
  topic: result.topic,
  generated_at: result.generated_at,
  total_ayahs: result.total_ayahs,
  quran_source: result.quran_source,
  translation_source: result.translation_source,
  dataset_version: result.dataset_version,
  direct: result.direct,
  strong_context: result.strong_context,
  related: result.related,
  completeness_report: result.completeness_report,
};

fs.writeFileSync(path.join(exportsDir, `${slug}.json`), JSON.stringify(websiteExport, null, 2));

const reviewExport = {
  topic: result.topic,
  generated_at: result.generated_at,
  review_queue: result.review_queue,
  excluded_candidates: result.excluded_candidates,
  audit_trail: result.audit_trail,
};
fs.writeFileSync(path.join(reviewDir, `${slug}.json`), JSON.stringify(reviewExport, null, 2));

console.log(`Topic: ${result.topic}`);
console.log(`Total ayahs scanned: ${result.completeness_report.total_ayahs_scanned}`);
console.log(`DIRECT: ${result.direct.length}`);
console.log(`STRONG_CONTEXT: ${result.strong_context.length}`);
console.log(`RELATED: ${result.related.length}`);
console.log(`REVIEW_REQUIRED: ${result.review_queue.length}`);
console.log(`Export written to data/exports/${slug}.json`);
console.log(`Review queue written to data/review/${slug}.json`);
