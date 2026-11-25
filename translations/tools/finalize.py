#!/usr/bin/env python3
"""Harmonise translated parts, copy them into the book folder, build the book
and run sanity checks.

usage: finalize.py WORK_BN_DIR BOOK_DIR OUT_BASENAME N_PARTS
"""
import re
import subprocess
import sys
from pathlib import Path

BL = 'ঀ-৿'
SUBS = [
    ('আয়িশা', 'আয়েশা'), ('হুরাইরা', 'হুরায়রা'), ('হাদীস', 'হাদিস'), ('সাহাবী', 'সাহাবি'),
    ('ফযীলত', 'ফযিলত'), ('দুআ', 'দোয়া'), ('আলিম', 'আলেম'), ('তাওকানী', 'নূকানী'), ('তূকানী', 'নূকানী'),
    ('নামাযী', 'সালাত আদায়কারী'), ('নামায পড়', 'সালাত আদায় কর'), ('নামায', 'সালাত'),
    ('সাল্লাম-এর', 'সাল্লামের'), ('সাল্লাম-কে', 'সাল্লামকে'),
    ('আনহুমা-এর', 'আনহুমার'), ('আনহু-এর', 'আনহুর'), ('আনহা-এর', 'আনহার'), ('আনহুম-এর', 'আনহুমের'),
    ('আনহুমা-কে', 'আনহুমাকে'), ('আনহু-কে', 'আনহুকে'), ('আনহা-কে', 'আনহাকে'),
    ('রাহিমাহুল্লাহ-এর', 'রাহিমাহুল্লাহর'), ('রাহিমাহুল্লাহ-কে', 'রাহিমাহুল্লাহকে'),
    ('সালাম-এর', 'সালামের'), ('সালাম-কে', 'সালামকে'),
]


def swap_quotes(t):
    """Curly single-primary / double-nested  ->  double-primary / single-nested."""
    t = re.sub('(?<=[' + BL + '])’(?=[' + BL + '])', '\x00', t)
    t = (t.replace('‘', '\x01').replace('’', '\x02').replace('“', '‘').replace('”', '’')
          .replace('\x01', '“').replace('\x02', '”').replace('\x00', '’'))
    return t


def main():
    work, book, out, n = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], int(sys.argv[4])
    (book / 'bn').mkdir(parents=True, exist_ok=True)
    files, counts = [], {}
    for i in range(1, n + 1):
        t = (work / f'part{i}.txt').read_text(encoding='utf-8')
        if t.count('‘') > 3 * max(1, t.count('“') + t.count('"')):
            t = swap_quotes(t)
            counts[f'part{i} quotes swapped'] = 1
        for a, b in SUBS:
            c = t.count(a)
            if c:
                counts[a] = counts.get(a, 0) + c
                t = t.replace(a, b)
        dest = book / 'bn' / f'part{i}.txt'
        dest.write_text(t.rstrip('\n') + '\n', encoding='utf-8')
        files.append(str(dest))
        body = '\n'.join(l for l in t.split('\n') if not l.startswith('%'))
        lat = sorted(set(re.findall(r'[A-Za-z]{2,}', re.sub(r'\[\^[^\]]+\]|@(?:ar|center|sub):', '', body))))
        if lat:
            print(f'part{i}: latin words:', lat[:15])
        if '**' in body or '__' in body:
            print(f'part{i}: markdown emphasis found')
        refs = set(re.findall(r'\[\^([^\]]+)\](?!:)', body))
        defs = set(re.findall(r'^\[\^([^\]]+)\]:', body, flags=re.M))
        if refs != defs:
            print(f'part{i}: footnote mismatch', sorted(refs ^ defs)[:10])
    print('harmonised:', counts)
    tools = Path(__file__).resolve().parent
    subprocess.run([sys.executable, str(tools / 'build_book.py'), str(book / out),
                    str(tools / 'quran-simple.json')] + files, check=True)
    (book / (out + '.fodt')).unlink()
    r = subprocess.run(['pdfinfo', str(book / (out + '.pdf'))], capture_output=True, text=True)
    print([l for l in r.stdout.split('\n') if l.startswith('Pages')])


if __name__ == '__main__':
    main()
