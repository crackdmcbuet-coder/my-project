/* 🖼️ ছবি-কার্ড: one small picture per question, drawn from data (CHAPTER.visuals[n] = {t, …}).
   VIS.render(q, "hint" | "full") returns a <figure>. "hint" points the way without giving the
   answer away; "full" shows it. Kinds: pin, count, chain, scale, cal, odd, scene (see SKILL.md). */
const VIS = (() => {
  const W = 420;
  const BN = s => String(s).replace(/\d/g, d => "০১২৩৪৫৬৭৮৯"[d]);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  // rough width of a label so long words shrink instead of spilling out of their box
  const fit = (s, w, size = 13) => Math.max(9, Math.min(size, Math.floor(w / (String(s).length * 0.56))));
  const svg = (h, body) => `<svg viewBox="0 0 ${W} ${h}" xmlns="http://www.w3.org/2000/svg" role="img">${body}</svg>`;
  const txt = (x, y, s, size = 13, cls = "", anchor = "middle") =>
    `<text x="${x}" y="${y}" font-size="${size}" text-anchor="${anchor}" class="${cls}">${esc(s)}</text>`;
  const delay = i => `style="animation-delay:${(i * 0.35).toFixed(2)}s"`;

  let styled = false;
  function addStyle() {
    if (styled || typeof document === "undefined") return;
    styled = true;
    const st = document.createElement("style");
    st.textContent = `
figure.vz{margin:10px 0;background:var(--fig);border:1px solid var(--line);border-radius:12px;padding:8px 8px 6px;color:#1f2328}
figure.vz svg{display:block;width:100%;height:auto;font-family:inherit}
figure.vz figcaption{font-size:.85rem;line-height:1.5;margin-top:4px;color:#37474f;text-align:center}
figure.vz.hint figcaption{color:#8a4b00}
figure.vz text{fill:#1f2328}
figure.vz .mut{fill:#5f6670}
figure.vz .hl{fill:#bf360c;font-weight:700}
figure.vz .bx{fill:#ffffff;stroke:#b0bec5;stroke-width:1.2}
figure.vz .bx.on{fill:#ffe0b2;stroke:#e65100;stroke-width:2}
figure.vz .bx.q{fill:#fff8e1;stroke:#f9a825;stroke-dasharray:4 3}
figure.vz .bx.ok{fill:#e8f5e9;stroke:#2e7d32}
figure.vz .bx.no{fill:#fdecec;stroke:#c62828}
figure.vz .ln{stroke:#78909c;stroke-width:1.5;fill:none}
figure.vz .ar{fill:#78909c}
figure.vz .band{fill:#e6f4f2}
figure.vz .band.on{fill:#ffcc80}
figure.vz .x{stroke:#c62828;stroke-width:4;stroke-linecap:round}
figure.vz .in{animation:vzin .5s ease-out both}
figure.vz .bob{animation:vzbob 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
figure.vz .swim{animation:vzswim 4s ease-in-out infinite alternate;transform-box:fill-box}
figure.vz .pulse{animation:vzpulse 1.4s ease-in-out infinite}
figure.vz [data-vzpin]{stroke:#d84315 !important;stroke-width:3px !important;animation:vzpulse 1.2s ease-in-out infinite}
@keyframes vzin{from{opacity:.15;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes vzbob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes vzswim{from{transform:translateX(-14px)}to{transform:translateX(14px)}}
@keyframes vzpulse{0%,100%{opacity:1}50%{opacity:.45}}
@media (prefers-reduced-motion: reduce){figure.vz *{animation:none !important}}`;
    document.head.appendChild(st);
  }

  // 📍 pin: the section's own figure (or v.sec's) with one part glowing. Mark parts with data-p="name".
  function pin(v, q, mode) {
    const sec = CHAPTER.sections.find(s => s.id === (v.sec || q.section));
    const raw = sec && sec.figure && (sec.figure.raw || sec.figure.svg);
    if (!raw) return "";
    let s = scopeSvg(raw, `vz-${q.n}-${mode}`);
    if (mode === "full") s = s.replace(new RegExp(`data-p="([^"]*\\b${v.el}\\b[^"]*)"`, "g"), 'data-p="$1" data-vzpin');
    return s;
  }

  // 🔢 count: n icons (emoji) popping in one by one; v.extra = a second, contrasting group
  function count(v, q, mode) {
    const per = Math.min(10, Math.max(v.n, (v.extra || {}).n || 0)), sz = per > 6 ? 30 : 38, gap = Math.min(70, (W - 40) / per);
    const unit = n => `${BN(n)}${v.unit === undefined ? "টি" : v.unit}`;
    // each row is centred, so one egg sits in the middle instead of the left edge
    const row = (n, icon, y, start) => Array.from({ length: n }, (_, i) =>
      `<text x="${(W - gap * Math.min(n - Math.floor(i / per) * per, per)) / 2 + gap * (i % per) + gap / 2}" y="${y + Math.floor(i / per) * (sz + 8)}" font-size="${sz}" text-anchor="middle" class="in" ${delay(start + i)}>${icon}</text>`).join("");
    if (mode === "hint")
      return svg(90, `<text x="150" y="60" font-size="44" text-anchor="middle" class="bob">${v.icon}</text>` +
        txt(250, 58, "× ?", 30, "hl") + txt(W / 2, 84, v.label, 13, "mut"));
    const rows1 = Math.ceil(v.n / per), y1 = sz + 6, h1 = rows1 * (sz + 8);
    let body = row(v.n, v.icon, y1, 0) + txt(W / 2, h1 + 26, `${unit(v.n)} ${v.label}`, 16, "hl");
    let h = h1 + 40;
    if (v.extra) {
      const rows2 = Math.ceil(v.extra.n / per);
      body += row(v.extra.n, v.extra.icon, h + sz, v.n) + txt(W / 2, h + rows2 * (sz + 8) + 22, `${unit(v.extra.n)} ${v.extra.label}`, 13, "mut");
      h += rows2 * (sz + 8) + 34;
    }
    return svg(h, body);
  }

  // ➡️ chain: steps in order (two rows when long). Hint hides the middle steps (or v.hide).
  function chain(v, q, mode) {
    const n = v.steps.length, per = n <= 4 ? n : Math.ceil(n / 2), rows = Math.ceil(n / per);
    const gap = 22, bw = (W - 16 - gap * (per - 1)) / per, bh = 40, rh = 74;
    const hide = v.hide || v.steps.map((_, i) => i).filter(i => i > 0 && i < n - 1);
    let body = "";
    v.steps.forEach((s, i) => {
      const r = Math.floor(i / per), c = i % per, x = 8 + c * (bw + gap), y = 14 + r * rh;
      const hidden = mode === "hint" && hide.includes(i), label = hidden ? "?" : s;
      const cls = hidden ? "bx q" : (v.on || []).includes(i) && mode === "full" ? "bx on" : "bx";
      body += `<g class="in" ${delay(i)}><rect class="${cls}" x="${x}" y="${y}" width="${bw}" height="${bh}" rx="9"/>` +
        txt(x + bw / 2, y + bh / 2 + 5, label, hidden ? 18 : fit(label, bw - 8), hidden ? "hl" : "") + `</g>`;
      if (i < n - 1) {
        if (c < per - 1) body += `<path class="ar" d="M${x + bw + 4} ${y + bh / 2 - 5} l${gap - 8} 5 l${-(gap - 8)} 5z"/>`;
        else body += `<path class="ln" d="M${x + bw / 2} ${y + bh + 2} V${y + bh + 14} H${8 + bw / 2} V${y + rh - 4}"/><path class="ar" d="M${8 + bw / 2 - 5} ${y + rh - 6} l5 6 l5 -6z"/>`;
      }
    });
    let h = 14 + rows * rh - 18;
    if (v.note) { body += txt(W / 2, h + 14, v.note, 13, mode === "full" ? "hl" : "mut"); h += 24; }
    return svg(h, body);
  }

  // 📏 scale: a ruler 0..max with marks {v: number | [from, to], l: label}; v.hl = the asked mark
  function scale(v, q, mode) {
    const x0 = 24, x1 = W - 24, X = n => x0 + (x1 - x0) * n / v.max, y = 70;
    let body = `<line class="ln" x1="${x0}" y1="${y}" x2="${x1}" y2="${y}" stroke-width="3"/>`;
    const step = v.step || Math.ceil(v.max / 10);
    for (let t = 0; t <= v.max; t += step)
      body += `<line class="ln" x1="${X(t)}" y1="${y - 6}" x2="${X(t)}" y2="${y + 6}"/>` + txt(X(t), y + 22, BN(t), 11, "mut");
    body += txt(x1, y + 40, v.unit, 12, "mut", "end");
    v.marks.forEach((m, i) => {
      const asked = i === (v.hl || 0), hideVal = mode === "hint" && asked;
      const [a, b] = Array.isArray(m.v) ? m.v : [m.v, m.v];
      const val = hideVal ? "?" : BN(a === b ? a : `${a}–${b}`), top = i % 2 ? 50 : 26;
      body += `<g class="in" ${delay(i)}>` + (a === b
        ? `<circle cx="${X(a)}" cy="${y}" r="${asked ? 8 : 6}" class="${asked ? "bx on" : "bx"}"/>`
        : `<rect x="${X(a)}" y="${y - 7}" width="${Math.max(6, X(b) - X(a))}" height="14" rx="5" class="${asked ? "bx on" : "bx"}"/>`) +
        txt(Math.min(x1 - 20, Math.max(x0 + 20, X((a + b) / 2))), top, `${m.l}: ${val}`, asked ? 14 : 12, asked ? "hl" : "") + `</g>`;
    });
    return svg(118, body);
  }

  // 📅 cal: 12 months with the Bangla six seasons above (each season starts mid-month).
  // v.on = month numbers 1–12 (hint hides them, shows v.season if given); v.seasons = season names to light up
  const MON = ["জানু", "ফেব্রু", "মার্চ", "এপ্রি", "মে", "জুন", "জুলা", "আগ", "সেপ্টে", "অক্টো", "নভে", "ডিসে"];
  const SEA = [["গ্রীষ্ম", "☀️", 3.5], ["বর্ষা", "🌧️", 5.5], ["শরৎ", "☁️", 7.5], ["হেমন্ত", "🌾", 9.5], ["শীত", "❄️", 11.5], ["বসন্ত", "🌸", 1.5]];
  function cal(v, q, mode) {
    const cw = (W - 16) / 12, x = m => 8 + m * cw;
    let body = "";
    SEA.forEach(([name, icon, start], i) => {
      const on = mode === "full" ? (v.seasons || []).includes(name) : v.season === name;
      const parts = start + 2 > 12 ? [[start, 12], [0, start + 2 - 12]] : [[start, start + 2]];
      parts.forEach(([a, b]) => body += `<rect class="band${on ? " on" : ""}" x="${x(a) + 1}" y="10" width="${(b - a) * cw - 2}" height="40" rx="6"/>`);
      const mid = start + 1 > 12 ? start + 1 - 12 : start + 1;
      body += txt(x(mid), 28, icon, 15) + txt(x(mid), 45, name, 11, on ? "hl" : "mut");
    });
    MON.forEach((m, i) => {
      const on = mode === "full" && (v.on || []).includes(i + 1), on2 = mode === "full" && (v.on2 || []).includes(i + 1);
      body += `<g class="${on ? "in" : ""}" ${delay(i % 4)}><rect class="bx${on ? " on" : on2 ? " ok" : ""}" x="${x(i) + 1}" y="58" width="${cw - 2}" height="34" rx="5"/>` +
        txt(x(i) + cw / 2, 80, m, fit(m, cw - 2, 11), on ? "hl" : "") + `</g>`;
    });
    let h = 100;
    const lab = mode === "full" ? v.label : v.season ? `কোন মাস? ঋতুটা দেখো` : "";
    if (lab) { body += txt(W / 2, h + 14, lab, 13, mode === "full" ? "hl" : "mut"); h += 22; }
    if (mode === "full" && v.label2) { body += txt(W / 2, h + 12, v.label2, 12, "mut"); h += 20; }
    return svg(h + 4, body);
  }

  // ❌ odd: four tiles that belong together except one (v.odd = index; items default to the options).
  // v.good = the odd one is the RIGHT pick ("কোনটি স্ত্রী জননতন্ত্রের অংশ?"): it gets ✓ instead of ✗.
  function odd(v, q, mode) {
    const items = v.items || q.options, tw = (W - 30) / 2, th = 46;
    let body = txt(W / 2, 18, v.group, 13, "mut");
    items.forEach((s, i) => {
      const x = 10 + (i % 2) * (tw + 10), y = 28 + Math.floor(i / 2) * (th + 10), isOdd = i === v.odd;
      const cls = mode !== "full" ? "bx" : v.good ? (isOdd ? "bx on" : "bx") : isOdd ? "bx no" : "bx ok";
      const mark = mode !== "full" ? "" : v.good ? (isOdd ? txt(x + tw - 14, y + 18, "✓", 16, "hl") : "")
        : isOdd ? `<path class="x" d="M${x + 10} ${y + 10} l${tw - 20} ${th - 20} M${x + tw - 10} ${y + 10} l${-(tw - 20)} ${th - 20}"/>` : txt(x + tw - 14, y + 18, "✓", 14, "");
      body += `<g class="in" ${delay(i)}><rect class="${cls}" x="${x}" y="${y}" width="${tw}" height="${th}" rx="10"/>` +
        txt(x + tw / 2, y + th / 2 + 5, s, fit(s, tw - 34, 14), mode === "full" && v.good && !isOdd ? "mut" : "") + mark + `</g>`;
    });
    let h = 28 + 2 * (th + 10);
    if (mode === "full" && v.why) { body += txt(W / 2, h + 12, v.why, 13, "hl"); h += 22; }
    return svg(h + 2, body);
  }

  // 🎬 scene: emoji placed on a small stage — art: [[emoji, x, y, size?, anim?]], lines: [[text, x, y, size?]].
  // v.key is blanked out ("____") in the hint.
  function scene(v, q, mode) {
    const h = v.h || 170;
    let body = v.ground ? `<rect x="0" y="${h - (v.ground[1] || 40)}" width="${W}" height="${v.ground[1] || 40}" rx="10" fill="${v.ground[0]}"/>` : "";
    v.art.forEach(([e, x, y, size = 40, anim = ""], i) =>
      body += `<g class="${anim}" ${anim ? `style="animation-delay:${(i * 0.3).toFixed(1)}s"` : ""}><text x="${x}" y="${y}" font-size="${size}" text-anchor="middle">${e}</text></g>`);
    (v.lines || []).forEach(([s, x, y, size = 13], i) => {
      const shown = mode === "hint" && v.key ? s.split(v.key).join("____") : s;
      body += txt(x, y, shown, size, i === 0 ? "hl" : "");
    });
    return svg(h, body);
  }

  const T = { pin, count, chain, scale, cal, odd, scene };
  function render(q, mode) {
    const v = q.v;
    if (!v || !T[v.t]) return "";
    addStyle();
    const art = T[v.t](v, q, mode);
    if (!art) return "";
    const cap = mode === "hint" ? (v.hook || "ছবিটা দেখে উত্তরটা চোখে ভাসাও") : v.cap;
    return `<figure class="vz vz-${v.t} ${mode}">${art}${cap ? `<figcaption>${mode === "hint" ? "🔍 " : "🖼️ "}${cap}</figcaption>` : ""}</figure>`;
  }
  return { render, kinds: Object.keys(T) };
})();
