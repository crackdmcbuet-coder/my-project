/* 🔤 Word-root rendering, shared by every page (needs ROOTS). */
const isBn = k => k.startsWith("bn_");
function rootChip(k) {
  const r = ROOTS[k]; if (!r) return "";
  return `<span class="rc${isBn(k) ? " bn" : ""}"><b>${r.w}</b><small>${r.lang}</small><i>${r.m}</i></span>`;
}
function termHTML(t, id) {
  const fx = t.p.filter(k => !isBn(k)), bn = t.p.filter(isBn);
  const extra = t.p.filter(k => ROOTS[k] && (ROOTS[k].med.length || ROOTS[k].also.length));
  return `<div class="term" ${id ? `id="${id}"` : ""}>
    <div class="tt">${t.t} <span class="bnname">${t.bn}</span></div>
    ${fx.length ? `<div class="eq">${fx.map(rootChip).join('<span class="plus">+</span>')}</div>` : ""}
    <div class="lit">= “${t.lit}”</div>
    ${t.bnp || bn.length ? `<div class="bnp">🇧🇩 ${t.bnp || ""} ${bn.map(rootChip).join(" ")}</div>` : ""}
    <div class="fact">💡 তাই মনে রাখো: ${t.fact}</div>
    ${extra.length ? `<details><summary>এই মূলগুলো আর কোথায় পাবে (মেডিকেলেও)</summary><ul>${extra.map(k => {
      const r = ROOTS[k]; return `<li><b>${r.w}</b> (${r.m}): ${r.also.concat(r.med.map(m => "🩺 " + m)).join(" · ")}</li>`; }).join("")}</ul></details>` : ""}
  </div>`;
}
const TERM_CSS = `
.term{border:1px solid var(--line);border-radius:12px;padding:12px;margin:10px 0;background:var(--card)}
.term .tt{font-weight:700;font-size:1.08rem}
.term .bnname{font-weight:500;color:var(--muted);font-size:.92rem}
.eq{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:8px 0}
.plus{font-weight:700;color:var(--muted)}
.rc{display:inline-flex;flex-direction:column;align-items:center;border-radius:10px;padding:4px 10px;background:#e3f2fd;color:#0d47a1;line-height:1.25;text-align:center}
.rc.bn{background:#fce4ec;color:#880e4f}
.rc b{font-size:.98rem}.rc small{font-size:.66rem;opacity:.75}.rc i{font-style:normal;font-size:.8rem;font-weight:600}
.lit{font-weight:600;color:var(--accent)}
.bnp{margin-top:6px;font-size:.92rem}
.fact{margin-top:6px;font-size:.92rem;background:var(--accent-soft);border-radius:8px;padding:6px 8px}
.term details{margin-top:6px;font-size:.85rem;color:var(--muted)}
.term summary{cursor:pointer}
.termchips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.termchips .chip{font-size:.8rem}
`;
document.head.insertAdjacentHTML("beforeend", `<style>${TERM_CSS}</style>`);
