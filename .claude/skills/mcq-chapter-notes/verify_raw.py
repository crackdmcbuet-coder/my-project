#!/usr/bin/env python3
"""Check that a chapter's data still matches the verified raw OCR file exactly.

usage: python3 verify_raw.py <raw.md> <chapter-dir>

Compares, per question number: question text, options, answer index and the marked flag.
Writers may add teaching content but must never change these four.
"""
import json, pathlib, re, subprocess, sys


def parse_raw(path):
    qs = {}
    for line in pathlib.Path(path).read_text().splitlines():
        if not re.match(r"^\d+ \|", line):
            continue
        parts = [p.strip() for p in line.split("|")]
        n, src, m, q, opts, ans = parts[:6]
        qs[int(n)] = {"q": q, "o": [o.strip() for o in opts.split("‖")],
                      "a": "abcde".index(ans), "m": m == "M"}
    return qs


def load_chapter(chdir):
    root = pathlib.Path(chdir).resolve().parent.parent / "roots" / "roots.js"
    js = (root.read_text() if root.exists() else "const ROOTS={};") + "\n" + \
        "\n".join(p.read_text() for p in sorted(pathlib.Path(chdir).glob("*.js")))
    js += "\nconsole.log(JSON.stringify(CHAPTER.questions.map(q=>({n:q.n,q:q.q,o:q.o,a:q.a,m:!!q.m}))));"
    out = subprocess.run(["node", "-"], input=js, capture_output=True, text=True)
    if out.returncode:
        sys.exit(out.stderr)
    return {q["n"]: q for q in json.loads(out.stdout)}


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def main():
    raw, data = parse_raw(sys.argv[1]), load_chapter(sys.argv[2])
    errs = []
    for n in sorted(set(raw) | set(data)):
        r, d = raw.get(n), data.get(n)
        if not r or not d:
            errs.append(f"{n}: {'missing in data' if r else 'extra in data'}")
            continue
        if norm(r["q"]) != norm(d["q"]):
            errs.append(f"{n}: question text differs\n   raw : {r['q']}\n   data: {d['q']}")
        if [norm(o) for o in r["o"]] != [norm(o) for o in d["o"]]:
            errs.append(f"{n}: options differ\n   raw : {r['o']}\n   data: {d['o']}")
        if r["a"] != d["a"]:
            errs.append(f"{n}: answer {r['a']} in raw, {d['a']} in data")
        if r["m"] != d["m"]:
            errs.append(f"{n}: marked flag {r['m']} in raw, {d['m']} in data")
    print(f"{len(raw)} raw, {len(data)} data, {len(errs)} problems")
    for e in errs:
        print(" -", e)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
