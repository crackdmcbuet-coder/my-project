"""Turn a book file (PDF, DOCX, HTML) into labelled text units."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Unit:
    label: str  # e.g. "পৃষ্ঠা 12"
    text: str


class NoTextLayerError(Exception):
    """PDF has pages but no extractable text (scanned images)."""


def _pdf(path: Path) -> list[Unit]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    units = [Unit(f"পৃষ্ঠা {i}", (page.extract_text() or "").strip()) for i, page in enumerate(reader.pages, 1)]
    if reader.pages and not any(u.text for u in units):
        raise NoTextLayerError(
            f"{path.name}: PDF-এ কোনো টেক্সট পাওয়া যায়নি (স্ক্যান করা ছবি)। আগে OCR করতে হবে।"
        )
    return [u for u in units if u.text]


def _docx(path: Path) -> list[Unit]:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(str(path))
    units, i = [], 0
    for child in doc.element.body.iterchildren():
        if child.tag.endswith("}p"):
            text = Paragraph(child, doc).text.strip()
        elif child.tag.endswith("}tbl"):
            rows = Table(child, doc).rows
            text = "\n".join(" | ".join(c.text.strip() for c in row.cells) for row in rows)
        else:
            continue
        if text:
            i += 1
            units.append(Unit(f"অনুচ্ছেদ {i}", text))
    return units


def _html(path: Path) -> list[Unit]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    lines = [ln.strip() for ln in soup.get_text("\n").splitlines()]
    return [Unit(f"অংশ {i}", ln) for i, ln in enumerate((ln for ln in lines if ln), 1)]


_READERS = {".pdf": _pdf, ".docx": _docx, ".html": _html, ".htm": _html}


def extract_units(path: Path) -> list[Unit]:
    path = Path(path)
    reader = _READERS.get(path.suffix.lower())
    if reader is None:
        raise ValueError(f"unsupported file type: {path.suffix} (use PDF, DOCX or HTML)")
    return reader(path)


@dataclass(frozen=True)
class Chunk:
    labels: tuple[str, ...]
    marked: str  # text with [label] markers, sent to the model
    plain: str  # text without markers, used to verify verbatim copies


def chunk_units(units: list[Unit], max_chars: int = 6000, overlap_units: int = 1) -> list[Chunk]:
    """Group units into chunks of about `max_chars`; repeat the last unit(s) at the next
    chunk's start so entries cut at a boundary are still seen whole once."""
    chunks: list[Chunk] = []
    i = 0
    while i < len(units):
        j, size = i, 0
        while j < len(units) and (size == 0 or size + len(units[j].text) <= max_chars):
            size += len(units[j].text) + 1
            j += 1
        group = units[i:j]
        chunks.append(
            Chunk(
                labels=tuple(u.label for u in group),
                marked="\n".join(f"[{u.label}]\n{u.text}" for u in group),
                plain="\n".join(u.text for u in group),
            )
        )
        if j >= len(units):
            break
        i = max(j - overlap_units, i + 1)
    return chunks
