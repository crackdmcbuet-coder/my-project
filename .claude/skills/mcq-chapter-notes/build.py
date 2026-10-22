#!/usr/bin/env python3
"""Build the self-contained HTML versions of one chapter.

usage: python3 build.py <chapter-dir> <output-dir>

<chapter-dir> holds numbered *.js data files (00-meta.js defines CHAPTER, later files push
sections / questions / cheats). Each template in ./templates gets the CSS, data and shared
JS inlined, so every output file opens offline on a phone with no other files.
"""
import json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
TPL = HERE / "templates"
VERSIONS = ["study", "quiz", "cheatsheet"]


def check(chapter_js: str) -> None:
    """Sanity-check the data with node: answer index valid, sections exist, no duplicate numbers."""
    probe = chapter_js + r"""
const errs = [], ids = new Set(CHAPTER.sections.map(s => s.id)), seen = new Set();
for (const q of CHAPTER.questions) {
  if (seen.has(q.n)) errs.push(`duplicate question ${q.n}`); seen.add(q.n);
  if (!Array.isArray(q.o) || q.a < 0 || q.a >= q.o.length) errs.push(`bad answer index in ${q.n}`);
  if (!ids.has(q.s)) errs.push(`unknown section ${q.s} in ${q.n}`);
}
const H = CHAPTER.hints || {};
for (const q of CHAPTER.questions) {
  const h = H[q.n];
  if (!h) { errs.push(`no 🔑 hint for ${q.n}`); continue; }
  if (![q.q, ...q.o].some(t => t.includes(h[0]))) errs.push(`cue "${h[0]}" not found in question ${q.n}`);
}
const R = typeof ROOTS === "undefined" ? {} : ROOTS;
for (const t of CHAPTER.terms || []) {
  if (!ids.has(t.s)) errs.push(`term ${t.t}: unknown section ${t.s}`);
  for (const k of t.p) if (!R[k]) errs.push(`term ${t.t}: root "${k}" missing in roots.js`);
}
for (const s of CHAPTER.sections) if (!CHAPTER.topics.some(t => t.id === s.topic)) errs.push(`unknown topic in ${s.id}`);
// 🖼️ ছবি-কার্ড (optional per question): known kind, required fields, pin target exists in the figure
const NEED = {pin: ["el"], count: ["n", "icon", "label"], chain: ["steps"], scale: ["max", "marks", "unit"],
  cal: [], odd: ["odd", "group"], scene: ["art"]};
for (const [n, v] of Object.entries(CHAPTER.visuals || {})) {
  const q = CHAPTER.questions.find(x => x.n === +n);
  if (!q) { errs.push(`visual for unknown question ${n}`); continue; }
  if (!NEED[v.t]) { errs.push(`visual ${n}: unknown kind "${v.t}"`); continue; }
  for (const k of NEED[v.t]) if (v[k] === undefined) errs.push(`visual ${n}: ${v.t} needs "${k}"`);
  if (v.t === "pin") {
    const sec = CHAPTER.sections.find(s => s.id === (v.sec || q.s));
    const svg = sec && sec.figure ? sec.figure.svg : "";
    if (!new RegExp(`data-p="[^"]*\\b${v.el}\\b`).test(svg)) errs.push(`visual ${n}: no data-p="${v.el}" in the figure of ${v.sec || q.s}`);
  }
  if (v.t === "odd" && !((v.items || q.o)[v.odd])) errs.push(`visual ${n}: odd index out of range`);
  if (v.t === "cal" && !v.on && !v.seasons) errs.push(`visual ${n}: cal needs "on" or "seasons"`);
}
console.log(JSON.stringify({errs, q: CHAPTER.questions.length, s: CHAPTER.sections.length,
  marked: CHAPTER.questions.filter(q => q.m).length, vis: Object.keys(CHAPTER.visuals || {}).length, id: CHAPTER.id, title: CHAPTER.title,
  terms: (CHAPTER.terms || []).map(t => Object.assign({}, t, {chapter: CHAPTER.title, chapterId: CHAPTER.id}))}));
"""
    out = subprocess.run(["node", "-"], input=probe, capture_output=True, text=True)
    if out.returncode:
        sys.exit("data error:\n" + out.stderr)
    r = json.loads(out.stdout)
    if r["errs"]:
        sys.exit("data errors:\n  " + "\n  ".join(r["errs"]))
    print(f"ok: {r['q']} questions, {r['s']} sections, {r['marked']} marked, {len(r['terms'])} terms, {r['vis']} visuals")
    return r


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    roots_file = src.resolve().parent.parent / "roots" / "roots.js"
    if not roots_file.exists():  # first chapter of a new project: start from the shared seed dictionary
        roots_file.parent.mkdir(parents=True, exist_ok=True)
        roots_file.write_text((HERE / "roots-seed.js").read_text())
    roots = roots_file.read_text()
    data = roots + "\n" + "\n".join(p.read_text() for p in sorted(src.glob("*.js")))
    info = check(data)
    css = (TPL / "base.css").read_text()
    common = "\n".join((TPL / f).read_text() for f in ("common.js", "terms.js", "visual.js"))
    dst.mkdir(parents=True, exist_ok=True)
    for v in VERSIONS:
        html = (TPL / f"{v}.html").read_text()
        # str.replace, not re.sub: the data contains backslashes and $ signs
        for key, val in {"{{BASE_CSS}}": css, "{{DATA_JS}}": data, "{{COMMON_JS}}": common,
                         "{{TITLE}}": info["title"]}.items():
            html = html.replace(key, val)
        out = dst / f"{info['id']}-{v}.html"
        out.write_text(html)
        print(f"wrote {out} ({out.stat().st_size // 1024} KB)")

    # 🔤 one shared root dictionary across every chapter in chapters/
    all_terms, chapters = [], []
    for ch in sorted(src.resolve().parent.iterdir()):
        if ch.is_dir() and any(ch.glob("*.js")):
            try:  # another chapter may be half-written; don't let it block this build
                r = check(roots + "\n" + "\n".join(p.read_text() for p in sorted(ch.glob("*.js"))))
                all_terms += r["terms"]
                chapters.append(r)
            except SystemExit as e:
                print(f"skipped {ch.name} in roots.html: {str(e).splitlines()[0]}")
    html = (TPL / "roots.html").read_text()
    for key, val in {"{{BASE_CSS}}": css, "{{ROOTS_JS}}": roots, "{{TERMS_JSON}}": json.dumps(all_terms, ensure_ascii=False),
                     "{{TERMS_UI}}": (TPL / "terms.js").read_text()}.items():
        html = html.replace(key, val)
    out = dst / "roots.html"
    out.write_text(html)
    print(f"wrote {out} ({len(all_terms)} terms from all chapters)")

    # 🏠 home page: every chapter that has been built into this output folder
    rows = "".join(
        f'<a class="ch" href="{c["id"]}-study.html"><b>{c["title"]}</b><span>{c["q"]}টি প্রশ্ন · 🔴 {c["marked"]} · 🔤 {len(c["terms"])}</span>'
        f'<span class="links"><object><a href="{c["id"]}-quiz.html">⏱️ মক টেস্ট</a> <a href="{c["id"]}-cheatsheet.html">📄 রিভিশন</a></object></span></a>'
        for c in chapters if (dst / f'{c["id"]}-study.html').exists())
    html = (TPL / "index.html").read_text().replace("{{BASE_CSS}}", css).replace("{{ROWS}}", rows)
    (dst / "index.html").write_text(html)
    print(f"wrote {dst / 'index.html'}")


if __name__ == "__main__":
    main()
