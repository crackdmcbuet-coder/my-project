import fs from 'node:fs';
import path from 'node:path';
import type { TopicMapEntry, TopicMapFile } from './types';

const TOPIC_MAP_PATH = path.join(process.cwd(), 'data', 'topics', 'topic-map.json');

let cached: TopicMapFile | null = null;

export function loadTopicMap(): TopicMapFile {
  if (!cached) {
    cached = JSON.parse(fs.readFileSync(TOPIC_MAP_PATH, 'utf8'));
  }
  return cached!;
}

/**
 * Resolves a user-typed topic string (or one of its Bangla aliases) to a
 * curated TopicMapEntry. Returns null if the topic hasn't been curated yet —
 * per project rule 34/9, we never fabricate Arabic search terms on the fly
 * for an unreviewed topic; new topics must be added to topic-map.json first
 * (see README "Adding a new topic").
 */
export function resolveTopic(input: string): TopicMapEntry | null {
  const normalized = input.trim();
  const map = loadTopicMap();
  return (
    map.topics.find(
      (t) => t.topic === normalized || t.aliases_bn.some((alias) => alias === normalized)
    ) ?? null
  );
}

export function listTopics(): { topic: string; aliases_bn: string[] }[] {
  return loadTopicMap().topics.map((t) => ({ topic: t.topic, aliases_bn: t.aliases_bn }));
}
