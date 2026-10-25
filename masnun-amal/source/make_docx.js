// blocks.json -> DOCX
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel, ShadingType, BorderStyle,
  Table, TableRow, TableCell, WidthType, Footer, PageNumber, PageBreak, Bookmark, InternalHyperlink,
  LevelFormat, TableLayoutType, VerticalAlign, LineRuleType,
} = require('docx');

const B = JSON.parse(fs.readFileSync('blocks.json', 'utf8'));
const BN = 'Hind Siliguri', AR = 'AlQuran IndoPak by QuranWBW', DG = 'Amiri';
const G = '1D5A45', GOLD = 'B08A3E', CREAM = 'FCF9F2', GOLDL = 'F7EFDC', GL = 'E8F1EC', MUT = '5B6660';
const W = 10206; // A4 content width (DXA) with 1.5 cm margins
const GRADE_COL = { sahih: '2E7D4F', hasan: '2B7A8A', mixed: 'B7791F', quran: '5B4BB0' };

const f = (name) => ({ ascii: name, hAnsi: name, cs: name, eastAsia: name });

// বাংলা টেক্সট রান; ﷺ আলাদা ফন্টে
function bnRuns(text, o = {}) {
  const size = o.size || 22;
  return text.split(/(ﷺ)/).filter(Boolean).map((t) => new TextRun({
    text: t, font: f(t === 'ﷺ' ? DG : BN), size, sizeComplexScript: size,
    bold: o.bold, boldComplexScript: o.bold, color: o.color, italics: o.italics,
  }));
}
// আরবি রান; আরবি সংখ্যা Amiri ফন্টে
function arRuns(text, o = {}) {
  const size = o.size || 40;
  return text.split(/([٠-٩]+|۞)/).filter(Boolean).map((t) => {
    const isDg = /^[٠-٩]+$/.test(t);
    return new TextRun({
      text: t, font: f(isDg ? DG : AR), rightToLeft: true,
      size: isDg ? Math.round(size * 0.6) : size, sizeComplexScript: isDg ? Math.round(size * 0.6) : size,
      color: t === '۞' ? GOLD : (o.color || '14231C'),
    });
  });
}
function ayahRuns(n, size = 40) {
  return [
    new TextRun({ text: ' ﴿', font: f(AR), rightToLeft: true, size, sizeComplexScript: size, color: GOLD }),
    new TextRun({ text: n, font: f(DG), rightToLeft: true, size: Math.round(size * 0.55), sizeComplexScript: Math.round(size * 0.55), color: '5A4310' }),
    new TextRun({ text: '﴾ ', font: f(AR), rightToLeft: true, size, sizeComplexScript: size, color: GOLD }),
  ];
}

const box = (color, sz = 4) => ({ style: BorderStyle.SINGLE, size: sz, color, space: 4 });
const shade = (fill) => ({ type: ShadingType.CLEAR, color: 'auto', fill });
const P = (children, o = {}) => new Paragraph({ children, ...o });

function arPara(text, o = {}) {
  return P(arRuns(text, o), {
    bidirectional: true, alignment: AlignmentType.CENTER, spacing: { before: 40, after: 40, line: 700, lineRule: LineRuleType.AT_LEAST },
    shading: shade(CREAM), indent: { left: 200, right: 200 }, keepLines: false,
    border: o.border || {}, keepNext: o.keepNext,
  });
}

function item(b) {
  const out = [];
  out.push(P([
    new TextRun({ text: ` ${b.no} `, font: f(BN), size: 22, sizeComplexScript: 22, bold: true, boldComplexScript: true, color: 'FFFFFF', shading: shade(GOLD) }),
    new TextRun({ text: '  ', size: 22 }),
    ...bnRuns(b.title, { size: 26, bold: true, color: 'FFFFFF' }),
  ], { shading: shade(G), spacing: { before: 280, after: 0 }, keepNext: true, keepLines: true, indent: { left: 0 } }));
  const meta = [];
  if (b.when) meta.push(...bnRuns('সময়: ', { size: 19, bold: true, color: G }), ...bnRuns(b.when + '     ', { size: 19 }));
  if (b.count) meta.push(...bnRuns('কতবার: ', { size: 19, bold: true, color: G }), ...bnRuns(b.count + '     ', { size: 19 }));
  meta.push(new TextRun({ text: ` ${b.grade_label} `, font: f(BN), size: 19, sizeComplexScript: 19, bold: true, boldComplexScript: true, color: 'FFFFFF', shading: shade(GRADE_COL[b.grade]) }));
  out.push(P(meta, { spacing: { before: 80, after: 80 }, keepNext: true, shading: shade('F2F5F3') }));

  b.ar.forEach((a, i) => {
    if (a.label) out.push(P(bnRuns(a.label, { size: 18, bold: true, color: GOLD }), { keepNext: true, spacing: { before: 60, after: 0 }, shading: shade(CREAM), indent: { left: 200, right: 200 } }));
    out.push(arPara(a.text));
  });
  for (const q of b.quran) {
    out.push(P(bnRuns(q.name, { size: 22, bold: true, color: G }), { alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 100, after: 0 }, shading: shade(CREAM), indent: { left: 200, right: 200 } }));
    if (q.bismillah) out.push(arPara(q.bismillah, { color: G, size: 36, keepNext: true }));
    const runs = [];
    q.verses.forEach((v) => { runs.push(...arRuns(v.ar + ' ')); runs.push(...ayahRuns(v.nar)); });
    out.push(P(runs, { bidirectional: true, alignment: AlignmentType.CENTER, spacing: { before: 40, after: 60, line: 700, lineRule: LineRuleType.AT_LEAST }, shading: shade(CREAM), indent: { left: 200, right: 200 } }));
    const mr = [...bnRuns('অর্থ: ', { size: 20, bold: true, color: G })];
    q.verses.forEach((v) => { mr.push(...bnRuns(`(${v.nbn}) `, { size: 20, bold: true, color: GOLD }), ...bnRuns(v.bn + ' ', { size: 20 })); });
    out.push(P(mr, { alignment: AlignmentType.JUSTIFIED, spacing: { before: 60, after: 60 }, indent: { left: 200, right: 200 } }));
  }
  if (b.bn) out.push(P([...bnRuns(b.text_only ? 'করণীয়: ' : 'অর্থ: ', { bold: true, color: G }), ...bnRuns(b.bn)],
    { alignment: AlignmentType.JUSTIFIED, spacing: { before: 100, after: 40 }, indent: { left: 120, right: 120 } }));
  if (b.bn_eve) out.push(P(bnRuns(b.bn_eve, { size: 19, color: MUT }), { spacing: { after: 40 }, indent: { left: 120, right: 120 } }));
  if (b.fadl.length) {
    const fb = { left: box(GOLD, 18) };
    out.push(P(bnRuns('ফযীলত ও বর্ণনা', { size: 20, bold: true, color: '7A5A17' }), { shading: shade(GOLDL), border: fb, keepNext: true, spacing: { before: 100, after: 0 }, indent: { left: 200, right: 120 } }));
    b.fadl.forEach((t) => out.push(P(bnRuns(t, { size: 20 }), { shading: shade(GOLDL), border: fb, alignment: AlignmentType.JUSTIFIED, spacing: { after: 0 }, indent: { left: 200, right: 120 } })));
  }
  if (b.note) out.push(P([...bnRuns('দ্রষ্টব্য: ', { size: 19, bold: true }), ...bnRuns(b.note, { size: 19 })],
    { shading: shade('F3F6F9'), border: { left: box('6B8AA6', 18) }, spacing: { before: 80 }, indent: { left: 200, right: 120 }, alignment: AlignmentType.JUSTIFIED }));
  out.push(P([...bnRuns('সূত্র: ', { size: 18, bold: true, color: '38463F' }), ...bnRuns(b.ref, { size: 18, color: MUT })], { spacing: { before: 80, after: b.grade_note ? 0 : 120 }, indent: { left: 120 } }));
  if (b.grade_note) out.push(P([...bnRuns('সনদের মান: ', { size: 18, bold: true, color: '38463F' }), ...bnRuns(b.grade_note, { size: 18, color: MUT })], { spacing: { after: 120 }, indent: { left: 120 } }));
  return out;
}

function cell(children, width, o = {}) {
  return new TableCell({ children, width: { size: width, type: WidthType.DXA }, shading: o.fill ? shade(o.fill) : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 }, verticalAlign: o.v });
}
function table(head, rows, widths, opts = {}) {
  const hr = new TableRow({ tableHeader: true, children: head.map((h, i) => cell([P(bnRuns(h, { size: 20, bold: true, color: 'FFFFFF' }), { alignment: opts.centerHead && i ? AlignmentType.CENTER : AlignmentType.LEFT })], widths[i], { fill: G })) });
  const body = rows.map((r, ri) => new TableRow({ cantSplit: true, height: opts.rowH ? { value: opts.rowH, rule: 'atLeast' } : undefined, children: r.map((c, i) => cell(
    [P(bnRuns(c, { size: opts.size || (i === r.length - 1 && r.length > 1 && !opts.tracker ? 18 : 20), bold: opts.boldFirst && i === 0, color: opts.boldFirst && i === 0 ? G : (i === r.length - 1 && !opts.tracker ? '4A5650' : undefined) }))],
    widths[i], { fill: ri % 2 ? 'F6F9F7' : undefined, v: VerticalAlign.CENTER })) }));
  return new Table({ columnWidths: widths, width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, layout: TableLayoutType.FIXED, rows: [hr, ...body] });
}

function body() {
  const out = [];
  for (const b of B) {
    switch (b.t) {
      case 'toc':
        out.push(P(bnRuns('সূচিপত্র', { size: 40, bold: true, color: G }), { alignment: AlignmentType.CENTER, spacing: { after: 240 }, border: { bottom: box(GOLD, 12) } }));
        b.rows.forEach(([name, id]) => out.push(P([new InternalHyperlink({ anchor: id, children: bnRuns(name, { size: 24, color: '1F2522' }) })],
          { border: { left: box(GOLD, 24) }, shading: shade('FBFCFB'), spacing: { before: 100, after: 100 }, indent: { left: 160 } })));
        out.push(P(bnRuns('হাদীসের মান-চিহ্ন', { bold: true, color: G }), { spacing: { before: 400, after: 60 } }));
        [['sahih', 'সহীহ', 'বিশুদ্ধ সনদে প্রমাণিত'], ['hasan', 'হাসান', 'গ্রহণযোগ্য সনদে প্রমাণিত'], ['mixed', 'সনদে মতভেদ', 'কিছু মুহাদ্দিস গ্রহণযোগ্য বলেছেন, কেউ কেউ দুর্বল বলেছেন']].forEach(([k, l, d]) =>
          out.push(P([new TextRun({ text: ` ${l} `, font: f(BN), size: 20, sizeComplexScript: 20, bold: true, boldComplexScript: true, color: 'FFFFFF', shading: shade(GRADE_COL[k]) }), ...bnRuns('  ' + d, { size: 20 })], { spacing: { after: 60 } })));
        break;
      case 'h1':
        out.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new Bookmark({ id: b.id, children: bnRuns(b.text, { size: 34, bold: true, color: 'FFFFFF' }) })] }));
        if (b.lead) out.push(P(bnRuns(b.lead, { size: 21, color: '24443A' }), { shading: shade(GL), border: { left: box('2F7A5F', 18) }, spacing: { after: 160 }, indent: { left: 160, right: 80 }, alignment: AlignmentType.JUSTIFIED }));
        break;
      case 'h2':
        out.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: bnRuns(b.text, { size: 28, bold: true, color: G }) }));
        break;
      case 'p':
        out.push(P(bnRuns(b.text), { alignment: AlignmentType.JUSTIFIED, spacing: { after: 120 } }));
        break;
      case 'ul':
        b.items.forEach((x) => out.push(P(bnRuns(x), { numbering: { reference: 'bul', level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { after: 60 } })));
        break;
      case 'item': out.push(...item(b)); break;
      case 'warn': {
        const bd = { top: box('C9542F', 8), left: box('C9542F', 8), bottom: box('C9542F', 8), right: box('C9542F', 8) };
        out.push(P(bnRuns(b.title, { size: 24, bold: true, color: 'A63F1F' }), { shading: shade('FDF1EC'), border: bd, spacing: { before: 240 }, keepNext: true }));
        b.items.forEach((x) => out.push(P(bnRuns('•  ' + x, { size: 20 }), { shading: shade('FDF1EC'), border: bd, indent: { left: 200 }, keepNext: true })));
        out.push(P(bnRuns(b.note, { size: 19, color: '5A3A2E' }), { shading: shade('FDF1EC'), border: bd, spacing: { after: 200 } }));
        break;
      }
      case 'routine': out.push(table(b.head, b.rows, [2200, 4436, 3570], { boldFirst: true })); out.push(P([])); break;
      case 'table2': out.push(table(b.head, b.rows, [5400, 4806], {})); out.push(P([])); break;
      case 'tracker': {
        const dw = 820, first = W - dw * b.days.length;
        out.push(table(['আমল', ...b.days], b.rows.map((r) => [r, ...b.days.map(() => '')]), [first, ...b.days.map(() => dw)], { tracker: true, rowH: 420, centerHead: true, size: 20 }));
        break;
      }
      case 'note':
        out.push(P(bnRuns(b.text, { bold: true, color: '24443A' }), { shading: shade(GL), border: { top: box('C5D9CD'), left: box('C5D9CD'), bottom: box('C5D9CD'), right: box('C5D9CD') }, spacing: { before: 300 }, alignment: AlignmentType.JUSTIFIED }));
        break;
    }
  }
  return out;
}

function cover() {
  const c = B[0];
  const sp = (n) => P([], { spacing: { before: n } });
  return [
    sp(1400),
    P(arRuns(c.bismillah, { size: 52, color: G }), { bidirectional: true, alignment: AlignmentType.CENTER }),
    P([new TextRun({ text: '۞', font: f(AR), size: 56, color: GOLD })], { alignment: AlignmentType.CENTER, spacing: { before: 200, after: 200 } }),
    P(bnRuns(c.title, { size: 64, bold: true, color: G }), { alignment: AlignmentType.CENTER, spacing: { after: 160 } }),
    P(bnRuns(c.sub, { size: 30, bold: true, color: '7A5A17' }), { alignment: AlignmentType.CENTER, spacing: { after: 300 }, border: { bottom: box(GOLD, 8) } }),
    P(bnRuns(c.sub2, { size: 23 }), { alignment: AlignmentType.CENTER, spacing: { before: 200 } }),
    P(bnRuns(c.sub3, { size: 23 }), { alignment: AlignmentType.CENTER }),
    sp(900),
    P(arRuns('وَاذۡكُرُوا اللّٰهَ كَثِيۡرًا لَّعَلَّكُمۡ تُفۡلِحُوۡنَ', { size: 42 }), { bidirectional: true, alignment: AlignmentType.CENTER }),
    P(bnRuns('«আর আল্লাহকে বেশি বেশি স্মরণ করো, যাতে তোমরা সফল হও।» (সূরা জুমুআ ৬২:১০)', { size: 20, color: MUT }), { alignment: AlignmentType.CENTER }),
    sp(700),
    P(bnRuns('সংকলন ও বিন্যাস', { size: 20, color: MUT }), { alignment: AlignmentType.CENTER, border: { top: box(GOLD, 8) }, indent: { left: 2200, right: 2200 } }),
    P(bnRuns(c.author, { size: 34, bold: true, color: G }), { alignment: AlignmentType.CENTER }),
    P(bnRuns(c.org, { size: 27, bold: true, color: '7A5A17' }), { alignment: AlignmentType.CENTER }),
    P(bnRuns('অক্টোবর ২০২৬', { size: 20, color: MUT }), { alignment: AlignmentType.CENTER }),
  ];
}

const footer = new Footer({ children: [P([
  ...bnRuns(`সকাল-সন্ধ্যা ও রাতের মাসনূন আমল   •   ${B[0].org}   •   পৃষ্ঠা `, { size: 16, color: '6B756F' }),
  new TextRun({ children: [PageNumber.CURRENT], font: f(BN), size: 16, color: '6B756F' }),
], { alignment: AlignmentType.CENTER })] });

const page = { size: { width: 11906, height: 16838 }, margin: { top: 850, bottom: 900, left: 850, right: 850 } };
const doc = new Document({
  title: 'সকাল-সন্ধ্যা ও রাতের মাসনূন আমল',
  creator: B[0].author,
  description: B[0].org,
  styles: {
    default: { document: { run: { font: f(BN), size: 22 }, paragraph: { spacing: { line: 300 } } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: f(BN), size: 34, bold: true, color: 'FFFFFF' },
        paragraph: { outlineLevel: 0, spacing: { before: 0, after: 200 }, shading: shade(G), border: { bottom: box(GOLD, 24) }, indent: { left: 0 } } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: f(BN), size: 28, bold: true, color: G },
        paragraph: { outlineLevel: 1, keepNext: true, spacing: { before: 300, after: 140 }, border: { bottom: box(GOLD, 10) } } },
    ],
  },
  numbering: { config: [{ reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] }] },
  sections: [
    { properties: { page: { ...page, borders: { pageBorderTop: { style: BorderStyle.DOUBLE, size: 18, color: G, space: 24 }, pageBorderBottom: { style: BorderStyle.DOUBLE, size: 18, color: G, space: 24 }, pageBorderLeft: { style: BorderStyle.DOUBLE, size: 18, color: G, space: 24 }, pageBorderRight: { style: BorderStyle.DOUBLE, size: 18, color: G, space: 24 } } } }, children: cover() },
    { properties: { page }, footers: { default: footer }, children: body() },
  ],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(process.argv[2] || 'raw.docx', buf); console.log('docx ok'); });
