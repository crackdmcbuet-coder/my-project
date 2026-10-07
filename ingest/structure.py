"""Turn a dream book into reviewable entries.

    python -m ingest.structure --book data/books/dreams.pdf --title "স্বপ্নের বই"          # dry run
    python -m ingest.structure --book ... --title ... --run --limit-chunks 2               # measure cost
    python -m ingest.structure --book ... --title ... --run                                # whole book

Claude only locates entries. Every `dream` and `interpretation` it returns must appear
character-for-character in the source text, otherwise the entry goes to `needs_review`
instead of `entries`. Nothing is written into the live data file: review the output
and copy what you approve into data/dreams.json.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import anthropic

from app import text as bn

from .extract import Chunk, NoTextLayerError, chunk_units, extract_units

# USD per million tokens (input, output), from Anthropic's price list.
PRICES = {
    "claude-opus-5-5": (4.0, 20.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-haiku-4-5": (1.0, 5.0),
}

SYSTEM_PROMPT = """\
You extract entries from a Bengali dream-interpretation book. The text you receive is a \
slice of the book; labels like [পৃষ্ঠা 12] mark where each page or paragraph starts.

Return every complete entry in the slice. An entry is one dream (the thing dreamt) and \
its interpretation as the book gives it.

Rules:
- Copy `dream` and `interpretation` EXACTLY, character for character, from the text. Do not \
translate, correct spelling, summarize, reorder or add anything. If the book lists several \
interpretations under one dream, keep them together in `interpretation` as written.
- `label` is the marker that precedes the entry (for example "পৃষ্ঠা 12"); copy it exactly.
- Skip introductions, tables of contents, headings that are not dreams, and any entry that \
is cut off at the start or end of the slice (it appears whole in the neighbouring slice).
- If the slice has no entries, return an empty list.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "entries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "dream": {"type": "string"},
                    "interpretation": {"type": "string"},
                    "label": {"type": "string"},
                },
                "required": ["dream", "interpretation", "label"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["entries"],
    "additionalProperties": False,
}


def verify(dream: str, interpretation: str, chunk: Chunk) -> bool:
    """True when both strings occur verbatim in the chunk (whitespace/zero-width tolerant)."""
    haystack = bn.clean(chunk.plain)
    return bn.clean(dream) in haystack and bn.clean(interpretation) in haystack


def entry_id(dream: str, interpretation: str) -> str:
    digest = hashlib.sha1(f"{bn.clean(dream)}|{bn.clean(interpretation)}".encode()).hexdigest()
    return f"d-{digest[:10]}"


def extract_chunk(client, model: str, chunk: Chunk):
    """Returns (raw_entries, usage). Raises RuntimeError if the output is unusable."""
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": chunk.marked}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
    )
    if response.stop_reason != "end_turn":
        raise RuntimeError(f"stop_reason={response.stop_reason} (try a smaller --chunk-chars)")
    block = next(b.text for b in response.content if b.type == "text")
    return json.loads(block)["entries"], response.usage


def process_book(client, model, title, chunks, on_progress=print):
    entries, needs_review, seen = [], [], set()
    tokens_in = tokens_out = 0
    for n, chunk in enumerate(chunks, 1):
        raw, usage = extract_chunk(client, model, chunk)
        tokens_in += usage.input_tokens
        tokens_out += usage.output_tokens
        for item in raw:
            eid = entry_id(item["dream"], item["interpretation"])
            if eid in seen:  # overlap between chunks
                continue
            seen.add(eid)
            label = item["label"].strip("[] ")
            record = {
                "id": eid,
                "dream": item["dream"],
                "interpretation": item["interpretation"],
                "source": f"{title}, {label}" if label else title,
            }
            if verify(item["dream"], item["interpretation"], chunk):
                entries.append(record)
            else:
                needs_review.append({**record, "verified": False})
        on_progress(f"chunk {n}/{len(chunks)}: {len(entries)} verified, {len(needs_review)} to review")
    return entries, needs_review, tokens_in, tokens_out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", required=True, type=Path)
    ap.add_argument("--title", required=True, help="book name shown as the source")
    ap.add_argument("--out", type=Path, default=Path("data/dreams.generated.json"))
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--chunk-chars", type=int, default=6000)
    ap.add_argument("--limit-chunks", type=int, help="only process the first N chunks (to measure cost)")
    ap.add_argument("--run", action="store_true", help="call the API (costs money); default is a dry run")
    args = ap.parse_args(argv)

    try:
        units = extract_units(args.book)
    except NoTextLayerError as exc:
        print(exc, file=sys.stderr)
        return 2
    chunks = chunk_units(units, args.chunk_chars)
    if args.limit_chunks:
        chunks = chunks[: args.limit_chunks]
    chars = sum(len(c.plain) for c in chunks)
    print(f"{args.book.name}: {len(units)} units, {len(chunks)} chunks, {chars:,} characters to send")

    if not args.run:
        print("Dry run: no API calls made. Add --run to extract (use --limit-chunks 2 first to see the real cost).")
        return 0

    client = anthropic.Anthropic(timeout=120.0)
    entries, needs_review, t_in, t_out = process_book(client, args.model, args.title, chunks)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"entries": entries, "needs_review": needs_review}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {args.out}: {len(entries)} verified entries, {len(needs_review)} need review")
    print(f"tokens: {t_in:,} in / {t_out:,} out")
    if args.model in PRICES:
        p_in, p_out = PRICES[args.model]
        print(f"approx cost: ${t_in / 1e6 * p_in + t_out / 1e6 * p_out:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
