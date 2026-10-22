/* Shared by every version. Runs after the chapter data (CHAPTER) is defined. */
CHAPTER.questions.forEach(q => {
  q.options = q.o; q.answer = q.a; q.marked = !!q.m; q.section = q.s; q.why = q.w || ""; q.elim = q.e || "";
});
CHAPTER.questions.sort((a, b) => a.n - b.n);
// 🔴 marks the student adds on the phone (no rebuild needed), merged with marks from the data
const MARKS = {
  key: "mcqnotes-marks:" + CHAPTER.id,
  load() { try { return JSON.parse(localStorage.getItem(this.key)) || {}; } catch (e) { return {}; } },
  save(v) { try { localStorage.setItem(this.key, JSON.stringify(v)); } catch (e) {} }
};
const OWN = MARKS.load();
CHAPTER.questions.forEach(q => { q.bookMarked = !!q.m; q.marked = q.bookMarked || !!OWN[q.n]; });
// 🔑 clue: the word in the question/options that points to the answer, plus a nudge
CHAPTER.questions.forEach(q => {
  const h = (CHAPTER.hints || {})[q.n];
  q.cue = h ? h[0] : ""; q.hint = h ? h[1] : "";
});
function markCue(text, cue) {
  if (!cue || !text.includes(cue)) return text;
  return text.replace(cue, `<mark class="cue">${cue}</mark>`);
}
// Inline <style> in an SVG is global; prefix its selectors with the figure's id so classes
// like .t/.s in one diagram don't restyle another (or the page). @keyframes are copied as is.
function scopeSvg(svg, id) {
  const scoped = svg.replace(/<style>([\s\S]*?)<\/style>/, (m, css) => {
    let out = "", i = 0;
    while (i < css.length) {
      const open = css.indexOf("{", i);
      if (open < 0) break;
      const sel = css.slice(i, open).trim();
      let depth = 1, j = open + 1;
      while (j < css.length && depth) { if (css[j] === "{") depth++; else if (css[j] === "}") depth--; j++; }
      const body = css.slice(open, j);
      out += sel.startsWith("@") ? sel + body : sel.split(",").map(x => `#${id} ${x.trim()}`).join(",") + body;
      i = j;
    }
    return `<style>${out}</style>`;
  });
  return scoped.replace("<svg ", `<svg id="${id}" `);
}
CHAPTER.sections.forEach(s => { if (s.figure && s.figure.svg) s.figure.svg = scopeSvg(s.figure.svg, "fig-" + s.id); });
const SEC = Object.fromEntries(CHAPTER.sections.map(s => [s.id, s]));
const TOPIC = Object.fromEntries(CHAPTER.topics.map(t => [t.id, t]));
CHAPTER.questions.forEach(q => { q.topic = SEC[q.section] ? SEC[q.section].topic : ""; });

// One progress store shared by all versions: { [qn]: "ok" | "bad" }
const STORE = {
  key: "mcqnotes:" + CHAPTER.id,
  load() { try { return JSON.parse(localStorage.getItem(this.key)) || {}; } catch (e) { return {}; } },
  save(v) { try { localStorage.setItem(this.key, JSON.stringify(v)); } catch (e) {} }
};
const LETTERS = "abcdefgh";
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

function versionNav(current) {
  const v = [["study", "📘 পড়া"], ["quiz", "⏱️ মক টেস্ট / কার্ড"], ["cheatsheet", "📄 এক পাতার রিভিশন"]];
  return `<nav class="versions"><a href="index.html">🏠 সব অধ্যায়</a>${v.map(([f, l]) =>
    `<a href="${CHAPTER.id}-${f}.html" class="${f === current ? "cur" : ""}">${l}</a>`).join("")}<a href="roots.html">🔤 শব্দমূল অভিধান</a></nav>`;
}
function topicChips(active, withAll = true) {
  return (withAll ? [{ id: "all", name: "সব", icon: "📚" }] : []).concat(CHAPTER.topics)
    .map(t => `<button class="chip" data-topic="${t.id}" aria-pressed="${t.id === active}">${t.icon} ${t.name}</button>`).join("");
}
function stripTags(html) { const d = document.createElement("div"); d.innerHTML = html; return d.textContent; }
