'use client';

import { useEffect, useState } from 'react';
import { TopicSearchForm } from '@/components/TopicSearchForm';
import { AyahCard } from '@/components/AyahCard';
import type { TopicExtractionResult } from '@/lib/pipeline/types';

interface TopicListItem {
  topic: string;
  aliases_bn: string[];
}

type ApiError = { error: string; message: string; available_topics: TopicListItem[] };

export default function HomePage() {
  const [topics, setTopics] = useState<TopicListItem[]>([]);
  const [result, setResult] = useState<TopicExtractionResult | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/api/extract')
      .then((r) => r.json())
      .then((d) => setTopics(d.topics ?? []));
  }, []);

  async function handleSearch(topic: string) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`/api/extract?topic=${encodeURIComponent(topic)}`);
      const data = await res.json();
      if (!res.ok) {
        setError(data as ApiError);
      } else {
        setResult(data as TopicExtractionResult);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-4 py-10 sm:px-6">
      <header className="mb-8 text-center">
        <h1 className="bangla-text mb-2 text-2xl font-bold text-brand-700 sm:text-3xl">
          কুরআন বিষয়ভিত্তিক আয়াত অনুসন্ধান
        </h1>
        <p className="bangla-text text-sm text-gray-500">
          একটি Topic লিখুন — সম্পূর্ণ কুরআন (৬২৩৬ আয়াত) থেকে প্রাসঙ্গিক আয়াত খুঁজে বের করা হবে।
        </p>
      </header>

      <TopicSearchForm onSearch={handleSearch} suggestions={topics.map((t) => t.topic)} />

      <div className="mt-10 space-y-6">
        {loading && <p className="bangla-text text-center text-gray-500">অনুসন্ধান চলছে…</p>}

        {error && (
          <div className="bangla-text rounded-lg border border-amber-300 bg-amber-50 p-4 text-amber-800">
            <p className="font-medium">{error.message}</p>
            {error.available_topics?.length > 0 && (
              <p className="mt-2 text-sm">
                বর্তমানে উপলব্ধ টপিক: {error.available_topics.map((t) => t.topic).join(', ')}
              </p>
            )}
          </div>
        )}

        {result && (
          <>
            <section className="bangla-text rounded-lg border border-brand-100 bg-white p-4 text-sm text-gray-600">
              <p>
                মোট স্ক্যান করা আয়াত: <b>{result.completeness_report.total_ayahs_scanned}</b> · সরাসরি:{' '}
                <b>{result.direct.length}</b> · প্রাসঙ্গিক ঘটনা: <b>{result.strong_context.length}</b> ·
                সম্পর্কিত: <b>{result.related.length}</b>
                {result.review_queue.length > 0 && (
                  <>
                    {' '}
                    · পর্যালোচনা প্রয়োজন: <b>{result.review_queue.length}</b>
                  </>
                )}
              </p>
              <p className="mt-1 text-xs text-gray-400">
                {result.quran_source} · {result.translation_source}
              </p>
            </section>

            {result.direct.length > 0 && (
              <section>
                <h2 className="bangla-text mb-3 text-lg font-semibold text-brand-700">সরাসরি সম্পর্কিত আয়াত</h2>
                <div className="space-y-4">
                  {result.direct.map((a) => (
                    <AyahCard key={`d-${a.surah_number}-${a.ayah_number}`} ayah={a} />
                  ))}
                </div>
              </section>
            )}

            {result.strong_context.length > 0 && (
              <section>
                <h2 className="bangla-text mb-3 text-lg font-semibold text-amber-700">প্রাসঙ্গিক ঘটনার আয়াত</h2>
                <div className="space-y-4">
                  {result.strong_context.map((a) => (
                    <AyahCard key={`s-${a.surah_number}-${a.ayah_number}`} ayah={a} />
                  ))}
                </div>
              </section>
            )}

            {result.related.length > 0 && (
              <section>
                <h2 className="bangla-text mb-3 text-lg font-semibold text-slate-700">সম্পর্কিত আয়াত</h2>
                <div className="space-y-4">
                  {result.related.map((a) => (
                    <AyahCard key={`r-${a.surah_number}-${a.ayah_number}`} ayah={a} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </main>
  );
}
