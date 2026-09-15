import type { Relevance } from '@/lib/pipeline/types';

const LABELS: Record<Relevance, string> = {
  DIRECT: 'সরাসরি সম্পর্কিত',
  STRONG_CONTEXT: 'প্রাসঙ্গিক ঘটনা',
  RELATED: 'সম্পর্কিত',
  WEAK: 'দুর্বল সম্পর্ক',
  IRRELEVANT: 'অপ্রাসঙ্গিক',
};

const STYLES: Record<Relevance, string> = {
  DIRECT: 'bg-brand-100 text-brand-700 border-brand-500',
  STRONG_CONTEXT: 'bg-amber-50 text-amber-800 border-amber-400',
  RELATED: 'bg-slate-100 text-slate-700 border-slate-400',
  WEAK: 'bg-gray-100 text-gray-500 border-gray-300',
  IRRELEVANT: 'bg-gray-100 text-gray-400 border-gray-300',
};

export function RelevanceBadge({ relevance }: { relevance: Relevance }) {
  return (
    <span
      className={`inline-block rounded-full border px-3 py-0.5 text-xs font-medium ${STYLES[relevance]}`}
    >
      {LABELS[relevance]}
    </span>
  );
}
