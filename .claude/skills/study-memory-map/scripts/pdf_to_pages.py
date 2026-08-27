#!/usr/bin/env python3
"""Render every page of a PDF to PNG so a scanned class-note deck can be read visually.

Most Bengali coaching-centre class notes are screenshots of lecture slides with
handwritten annotations on top — there is no text layer at all, so text extraction
returns empty strings and OCR loses the handwriting. Rendering each page to an image
and reading it with vision is the only approach that captures highlights, circles,
arrows and margin notes, which is exactly where the teacher's emphasis lives.

Usage:
    python pdf_to_pages.py <input.pdf> <output_dir> [--scale 1.6] [--check-only]

--check-only prints the page count and whether a text layer exists, then exits.
Run that first: if the PDF *does* have real text, extracting it is far cheaper
than reading ~1500 image tokens per page.
"""

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("out_dir", nargs="?", default="pages")
    ap.add_argument(
        "--scale",
        type=float,
        default=1.6,
        help="Render scale. 1.6 turns a 1280x720 slide into 2048x1152, which is "
        "the sweet spot: Bengali conjuncts and handwriting stay legible without "
        "wasting tokens. Raise to 2.0 only if a page comes back unreadable.",
    )
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    try:
        import pymupdf
    except ImportError:
        print("pymupdf missing. Install with: pip install pymupdf", file=sys.stderr)
        return 1

    doc = pymupdf.open(args.pdf)
    n = len(doc)

    text_chars = sum(len(doc[i].get_text().strip()) for i in range(min(5, n)))
    has_text = text_chars > 200

    print(f"pages: {n}")
    print(f"text layer: {'YES' if has_text else 'NO (scanned images — render needed)'}")
    if has_text:
        print("  -> Extract text directly instead; rendering would waste tokens.")
    if args.check_only:
        return 0

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    matrix = pymupdf.Matrix(args.scale, args.scale)
    for i, page in enumerate(doc):
        page.get_pixmap(matrix=matrix).save(str(out / f"p{i + 1:03d}.png"))

    print(f"rendered {n} pages -> {out}/p001.png … p{n:03d}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
