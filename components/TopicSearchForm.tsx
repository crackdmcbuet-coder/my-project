'use client';

import { useState } from 'react';

export function TopicSearchForm({
  onSearch,
  suggestions,
}: {
  onSearch: (topic: string) => void;
  suggestions: string[];
}) {
  const [value, setValue] = useState('');

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (value.trim()) onSearch(value.trim());
      }}
      className="mx-auto w-full max-w-xl"
    >
      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="যেমন: জাদু, কুকুর, শয়তান, ভয়..."
          className="bangla-text flex-1 rounded-lg border border-brand-100 px-4 py-3 text-base shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
        <button
          type="submit"
          className="rounded-lg bg-brand-600 px-5 py-3 font-medium text-white shadow-sm transition hover:bg-brand-700"
        >
          অনুসন্ধান
        </button>
      </div>

      {suggestions.length > 0 && (
        <div className="mt-3 flex flex-wrap justify-center gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => {
                setValue(s);
                onSearch(s);
              }}
              className="bangla-text rounded-full border border-brand-100 bg-white px-3 py-1 text-sm text-brand-700 transition hover:bg-brand-50"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </form>
  );
}
