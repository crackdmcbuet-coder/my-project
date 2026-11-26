#!/usr/bin/env python3
"""Join a header and the per-part translator notes into one notes file.

usage: make_notes.py HEADER.txt WORK_BN_DIR N_PARTS OUT.txt
"""
import sys
from pathlib import Path

head, work, n, out = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
text = head.read_text(encoding='utf-8').rstrip() + '\n'
for i in range(1, n + 1):
    f = work / f'part{i}.notes.txt'
    text += f'\n\n---------------- অংশ {i} ----------------\n\n'
    text += (f.read_text(encoding='utf-8').strip() if f.exists() else '(এই অংশের জন্য আলাদা নোট লেখা হয়নি।)') + '\n'
out.write_text(text, encoding='utf-8')
print(out.name, len(text.split()), 'words; missing:', [i for i in range(1, n + 1) if not (work / f'part{i}.notes.txt').exists()])
