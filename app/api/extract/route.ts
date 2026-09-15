import { NextRequest, NextResponse } from 'next/server';
import { resolveTopic, listTopics } from '@/lib/pipeline/topicMap';
import { extractTopic } from '@/lib/pipeline/extractTopic';

export async function GET(req: NextRequest) {
  const topicParam = req.nextUrl.searchParams.get('topic');

  if (!topicParam) {
    return NextResponse.json({ topics: listTopics() });
  }

  const topicEntry = resolveTopic(topicParam);
  if (!topicEntry) {
    return NextResponse.json(
      {
        error: 'TOPIC_NOT_CURATED',
        message: `"${topicParam}" টপিকটি এখনো Topic Knowledge Map-এ যাচাইকৃত (verified) অবস্থায় যোগ করা হয়নি। ভুল বা অসম্পূর্ণ Arabic term দিয়ে অনুমাননির্ভর ফলাফল দেখানো হয় না — এটি data/topics/topic-map.json এ যোগ করার পর পুনরায় চেষ্টা করুন।`,
        available_topics: listTopics(),
      },
      { status: 404 }
    );
  }

  const result = extractTopic(topicEntry);
  return NextResponse.json(result);
}
