import type { ClassifiedAyah } from '@/lib/pipeline/types';
import { RelevanceBadge } from './RelevanceBadge';

export function AyahCard({ ayah }: { ayah: ClassifiedAyah }) {
  return (
    <article className="rounded-xl border border-brand-100 bg-white p-4 shadow-sm sm:p-6">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm text-gray-500">
          <span className="font-semibold text-brand-700">
            সূরা {ayah.surah_name_bn ?? ayah.surah_name_transliteration}
          </span>{' '}
          ({ayah.surah_name_transliteration}) — আয়াত {ayah.ayah_number}
        </div>
        <RelevanceBadge relevance={ayah.relevance} />
      </div>

      <p className="arabic-text mb-4">{ayah.arabic}</p>
      <p className="bangla-text mb-3 text-gray-800">{ayah.bangla}</p>

      <details className="bangla-text text-sm text-gray-500">
        <summary className="cursor-pointer select-none text-brand-600">কেন এই আয়াত?</summary>
        <p className="mt-2 leading-relaxed">{ayah.reason_bn}</p>
        <p className="mt-1 text-xs text-gray-400">
          মিলকৃত শব্দ/সূত্র: {ayah.matched_concepts.join(', ')} · আস্থা: {Math.round(ayah.confidence * 100)}%
          {ayah.review_required && ' · পর্যালোচনা প্রয়োজন'}
        </p>
      </details>
    </article>
  );
}
