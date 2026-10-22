#!/usr/bin/env python3
"""Convert EXTRACT-*.md files (### Qn / **স্টেম:** / - ক. … / **উত্তর:** …) into the raw format.

usage: python3 extract_to_raw.py out.md "<title>" extract1.md [extract2.md …] [--wrong 3,7,13]

- Uses no images and no model, so the conversion is free and exact.
- Every "## উপশিরোনাম:" becomes a topic heading. "অনুশীলনীর প্রশ্ন" banners are not topics;
  their questions stay in the topic above. The writer may merge small topics later.
- "--wrong" lists the questions the student got wrong (→ M). Without it nothing is marked; the
  student can also mark questions on the phone with the "➕ ভুল করি" button.
- "⚠ দ্বন্দ্ব" lines and answers the extract read from a cut-off column become ⚠ notes, so the
  writer checks them on the web.
"""
import re, sys

LET = {"ক": "a", "খ": "b", "গ": "c", "ঘ": "d", "ঙ": "e"}


def parse(path):
    topic, out = None, []
    cur = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = re.match(r"^## উপশিরোনাম:\s*(.+)", line)
        if m:
            name = re.sub(r"\s*\(Q.*$", "", m.group(1)).strip()
            if not name.startswith("অনুশীলনীর প্রশ্ন"):
                topic = name
            continue
        if line.startswith("## "):          # count/entity/conflict summaries
            cur = None
            continue
        m = re.match(r"^### Q0*(\d+)", line)
        if m:
            cur = {"n": int(m.group(1)), "topic": topic, "o": [], "notes": [], "tag": "", "src": ""}
            out.append(cur)
            continue
        if cur is None:
            continue
        if line.startswith("**স্টেম:**"):
            cur["q"] = line.split("**স্টেম:**", 1)[1].strip()
        elif re.match(r"^- [কখগঘঙ]\. ", line):
            cur["o"].append(line[5:].strip())
        elif line.startswith("**উত্তর:**"):
            v = line.split("**উত্তর:**", 1)[1].strip()
            cur["a"] = LET.get(v[:1], "?")
            if "কাটা" in v:
                cur["notes"].append("⚠ answer read from a cut-off column — verify on the web")
        elif line.startswith("**ট্যাগ:**"):
            cur["tag"] = line.split("**ট্যাগ:**", 1)[1].strip().strip("[]")
        elif line.startswith("**উৎস-চিহ্ন:**"):
            cur["src"] = line.split("**উৎস-চিহ্ন:**", 1)[1].strip()
        elif line.startswith("**ব্যাখ্যা:**"):
            cur["notes"].append("ব্যাখ্যা (বই): " + line.split("**ব্যাখ্যা:**", 1)[1].strip())
        elif line.startswith("**⚠ দ্বন্দ্ব:**"):
            cur["notes"].append("⚠ " + line.split("**⚠ দ্বন্দ্ব:**", 1)[1].strip() + " — verify on the web")
        elif line.startswith("**ভুল:**"):
            cur["wrong"] = True
    return out


def main():
    args = sys.argv[1:]
    wrong = set()
    if "--wrong" in args:
        i = args.index("--wrong")
        wrong = {int(x) for x in re.split(r"[,\s]+", args[i + 1]) if x}
        args = args[:i] + args[i + 2:]
    out_path, title, files = args[0], args[1], args[2:]
    qs = {}
    for f in files:
        for q in parse(f):
            qs[q["n"]] = q                  # later files win on duplicates
    lines = [f"# {title} — raw (converted from EXTRACT files, no OCR)",
             "Format: n | src | M | question | options ‖ | book answer letter | note", ""]
    topic, tid = None, 0
    problems = []
    for n in sorted(qs):
        q = qs[n]
        if q["topic"] != topic:
            topic, tid = q["topic"], tid + 1
            lines.append(f"\n## topic: t{tid} — {topic}")
        if len(q["o"]) < 2 or q.get("a", "?") == "?" or "q" not in q:
            problems.append(n)
        src = q["tag"] or "অনুশীলনী"
        if q["src"]:
            src += f" ({q['src']})"
        m = "M" if (n in wrong or q.get("wrong")) else ""
        note = " ".join(q["notes"]).replace("|", "/")
        lines.append(f"{n} | {src.replace('|', '/')} | {m} | {q.get('q', '').replace('|', '/')} | "
                     f"{' ‖ '.join(o.replace('|', '/') for o in q['o'])} | {q.get('a', '?')} | {note}")
    open(out_path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    flagged = [n for n in qs if any("⚠" in x for x in qs[n]["notes"])]
    print(f"{len(qs)} questions, {tid} topics, {len(wrong)} marked wrong")
    print("needs web check (⚠):", flagged)
    if problems:
        print("PROBLEMS (missing stem/options/answer):", problems)
    missing = [n for n in range(1, max(qs) + 1) if n not in qs]
    if missing:
        print("missing numbers:", missing)


if __name__ == "__main__":
    main()
