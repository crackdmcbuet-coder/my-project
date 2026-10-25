# -*- coding: utf-8 -*-
"""blocks.json -> HTML (PDF তৈরির জন্য)।"""
import html, json, os, re, sys

FONTS = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "fonts"))
B = json.load(open("blocks.json"))

def esc(s): return html.escape(s, quote=False)

def bntext(s):
    """বাংলা লেখা; ﷺ ও আরবি অক্ষর আলাদা ফন্টে।"""
    s = esc(s)
    s = s.replace("ﷺ", '<span class="saw">ﷺ</span>')
    return s

def artext(s):
    s = esc(s)
    s = re.sub(r"([٠-٩]+)", r'<span class="dg">\1</span>', s)
    s = s.replace("۞", '<span class="sep">۞</span>')
    return s

def ayah(n): return f'<span class="ayn">﴿<span class="dg">{n}</span>﴾</span>'

def item(b):
    nverses = sum(len(q["verses"]) for q in b["quran"])
    short = nverses <= 11 and sum(len(a["text"]) for a in b["ar"]) < 1400 and not (b["quran"] and len(b["quran"]) > 1)
    o = [f'<section class="item g-{b["grade"]}{' short' if short else ''}">']
    o.append(f'<div class="ihead"><span class="no">{b["no"]}</span><h3>{bntext(b["title"])}</h3></div>')
    o.append('<div class="meta">')
    if b["when"]: o.append(f'<span class="chip"><b>সময়:</b> {bntext(b["when"])}</span>')
    if b["count"]: o.append(f'<span class="chip"><b>কতবার:</b> {bntext(b["count"])}</span>')
    o.append(f'<span class="grade {b["grade"]}">{b["grade_label"]}</span></div>')
    if b["ar"]:
        o.append('<div class="arbox">')
        for a in b["ar"]:
            if a["label"]: o.append(f'<div class="arlabel">{a["label"]}</div>')
            o.append(f'<p class="ar">{artext(a["text"])}</p>')
        o.append('</div>')
    for q in b["quran"]:
        o.append('<div class="qbox">')
        o.append(f'<div class="sname">{bntext(q["name"])}</div>')
        if q["bismillah"]: o.append(f'<p class="ar bism">{artext(q["bismillah"])}</p>')
        o.append('<p class="ar">' + " ".join(f'{artext(v["ar"])} {ayah(v["nar"])}' for v in q["verses"]) + '</p>')
        o.append('<p class="qbn"><b>অর্থ:</b> ' + " ".join(f'<span class="vn">({v["nbn"]})</span> {bntext(v["bn"])}' for v in q["verses"]) + '</p>')
        o.append('</div>')
    if b["bn"]:
        label = "করণীয়:" if b["text_only"] else "অর্থ:"
        o.append(f'<p class="mean"><b>{label}</b> {bntext(b["bn"])}</p>')
    if b["bn_eve"]: o.append(f'<p class="mean eve">{bntext(b["bn_eve"])}</p>')
    if b["fadl"]:
        o.append('<div class="fadl"><div class="ftitle">ফযীলত ও বর্ণনা</div>')
        for f in b["fadl"]: o.append(f'<p>{bntext(f)}</p>')
        o.append('</div>')
    if b["note"]: o.append(f'<p class="note"><b>দ্রষ্টব্য:</b> {bntext(b["note"])}</p>')
    ref = f'<b>সূত্র:</b> {bntext(b["ref"])}'
    if b["grade_note"]: ref += f'<br><b>সনদের মান:</b> {bntext(b["grade_note"])}'
    o.append(f'<p class="ref">{ref}</p>')
    o.append('</section>')
    return "\n".join(o)

def body():
    o = []
    for b in B:
        t = b["t"]
        if t == "cover": continue
        if t == "toc":
            o.append('<section class="toc"><h1 class="toch">সূচিপত্র</h1><ol>')
            for name, i in b["rows"]: o.append(f'<li><a href="#{i}">{bntext(name)}</a></li>')
            o.append('</ol>')
            o.append('<div class="legend"><div class="lt">হাদীসের মান-চিহ্ন</div>'
                     '<p><span class="grade sahih">সহীহ</span> বিশুদ্ধ সনদে প্রমাণিত '
                     '<span class="grade hasan">হাসান</span> গ্রহণযোগ্য সনদে প্রমাণিত '
                     '<span class="grade mixed">সনদে মতভেদ</span> কিছু মুহাদ্দিস গ্রহণযোগ্য বলেছেন, কেউ কেউ দুর্বল বলেছেন</p></div>'
                     '</section>')
        elif t == "h1":
            o.append(f'<h1 id="{b["id"]}" class="part">{bntext(b["text"])}</h1>')
            if b.get("lead"): o.append(f'<p class="lead">{bntext(b["lead"])}</p>')
        elif t == "h2": o.append(f'<h2>{bntext(b["text"])}</h2>')
        elif t == "p": o.append(f'<p class="para">{bntext(b["text"])}</p>')
        elif t == "ul": o.append('<ul>' + "".join(f'<li>{bntext(x)}</li>' for x in b["items"]) + '</ul>')
        elif t == "item": o.append(item(b))
        elif t == "warn":
            o.append(f'<div class="warn"><div class="wt">{bntext(b["title"])}</div><ul>' +
                     "".join(f'<li>{bntext(x)}</li>' for x in b["items"]) + f'</ul><p>{bntext(b["note"])}</p></div>')
        elif t == "routine":
            o.append('<table class="rt"><thead><tr>' + "".join(f'<th>{h}</th>' for h in b["head"]) + '</tr></thead><tbody>')
            for r in b["rows"]:
                o.append(f'<tr><td class="tm">{bntext(r[0])}</td><td>{bntext(r[1])}</td><td class="dl">{bntext(r[2])}</td></tr>')
            o.append('</tbody></table>')
        elif t == "table2":
            o.append('<table class="rt t2"><thead><tr>' + "".join(f'<th>{h}</th>' for h in b["head"]) + '</tr></thead><tbody>')
            for r in b["rows"]: o.append(f'<tr><td>{bntext(r[0])}</td><td class="dl">{bntext(r[1])}</td></tr>')
            o.append('</tbody></table>')
        elif t == "tracker":
            o.append('<table class="trk"><thead><tr><th>আমল</th>' + "".join(f'<th>{d}</th>' for d in b["days"]) + '</tr></thead><tbody>')
            for r in b["rows"]: o.append(f'<tr><td>{bntext(r)}</td>' + '<td></td>' * len(b["days"]) + '</tr>')
            o.append('</tbody></table>')
        elif t == "note": o.append(f'<p class="disc">{bntext(b["text"])}</p>')
    return "\n".join(o)

def cover():
    c = B[0]
    return f'''<section class="cover"><div class="frame">
<p class="ar cbism">{artext(c["bismillah"])}</p>
<div class="orn">۞</div>
<h1 class="ctitle">{esc(c["title"])}</h1>
<p class="csub">{esc(c["sub"])}</p>
<div class="rule"></div>
<p class="csub2">{esc(c["sub2"])}</p>
<p class="csub3">{esc(c["sub3"])}</p>
<p class="ar cayah">وَاذۡكُرُوا اللّٰهَ كَثِيۡرًا لَّعَلَّكُمۡ تُفۡلِحُوۡنَ</p>
<p class="caref">«আর আল্লাহকে বেশি বেশি স্মরণ করো, যাতে তোমরা সফল হও।» (সূরা জুমুআ ৬২:১০)</p>
<p class="cdate">সংকলন: অক্টোবর ২০২৬</p>
</div></section>'''

CSS = f"""
@font-face{{font-family:IndoPak;src:url(file://{FONTS}/IndoPak.ttf)}}
@font-face{{font-family:AmiriD;src:url(file://{FONTS}/Amiri-Regular.ttf)}}
@font-face{{font-family:Hind;src:url(file://{FONTS}/HindSiliguri-Regular.ttf);font-weight:400}}
@font-face{{font-family:Hind;src:url(file://{FONTS}/HindSiliguri-Medium.ttf);font-weight:500}}
@font-face{{font-family:Hind;src:url(file://{FONTS}/HindSiliguri-SemiBold.ttf);font-weight:600}}
@font-face{{font-family:Hind;src:url(file://{FONTS}/HindSiliguri-Bold.ttf);font-weight:700}}
@font-face{{font-family:Tiro;src:url(file://{FONTS}/TiroBangla-Regular.ttf)}}
:root{{--g:#1d5a45;--g2:#2f7a5f;--gl:#e8f1ec;--gold:#b08a3e;--goldl:#f7efdc;--cream:#fcf9f2;--ink:#1f2522;--mut:#5b6660;--line:#d9e2dc}}
@page{{size:A4;margin:16mm 15mm 18mm 15mm}}
html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:Hind,sans-serif;color:var(--ink);font-size:11pt;line-height:1.62;margin:0;background:#fff}}
.saw{{font-family:AmiriD,serif;font-size:1.05em}}
.ar{{font-family:IndoPak,AmiriD,serif;direction:rtl;text-align:center;font-size:20pt;line-height:2.05;margin:.15em 0;color:#14231c;word-spacing:.04em}}
.dg{{font-family:AmiriD,serif;font-size:.62em}}
.sep{{color:var(--gold);padding:0 .25em}}
.ayn{{color:var(--gold);white-space:nowrap}}
.ayn .dg{{color:#5a4310;font-size:.6em;padding:0 .08em}}
h1.part{{font-weight:700;font-size:19pt;color:#fff;background:var(--g);padding:.45em .7em;border-radius:6px;margin:0 0 .6em;break-before:page;border-bottom:4px solid var(--gold)}}
p.lead{{background:var(--gl);border-left:4px solid var(--g2);padding:.55em .8em;border-radius:4px;color:#24443a;margin:0 0 1em}}
h2{{font-weight:700;font-size:14.5pt;color:var(--g);border-bottom:2px solid var(--gold);padding-bottom:.15em;margin:1.2em 0 .6em;break-after:avoid}}
p.para{{text-align:justify;margin:.4em 0 .7em}}
ul{{margin:.3em 0 .8em;padding-left:1.3em}} li{{margin:.25em 0}}
.item{{border:1px solid var(--line);border-radius:8px;padding:0 0 .5em;margin:0 0 1.05em;background:#fff;break-inside:auto}}
.item.short{{break-inside:avoid}}
.ihead,.meta{{break-inside:avoid}}
.ihead{{display:flex;align-items:center;gap:.6em;background:linear-gradient(90deg,var(--g),var(--g2));color:#fff;padding:.38em .75em;border-radius:7px 7px 0 0;break-after:avoid}}
.ihead h3{{margin:0;font-size:13pt;font-weight:600;line-height:1.35}}
.no{{display:inline-flex;align-items:center;justify-content:center;min-width:1.75em;height:1.75em;border-radius:50%;background:var(--gold);color:#fff;font-weight:700;font-size:10.5pt;flex:none}}
.meta{{display:flex;flex-wrap:wrap;gap:.4em;padding:.5em .8em .1em;font-size:9.6pt;break-after:avoid}}
.chip{{background:#f2f5f3;border:1px solid var(--line);border-radius:20px;padding:.05em .7em;color:#33413a}}
.chip b{{color:var(--g);font-weight:600}}
.grade{{border-radius:20px;padding:.05em .75em;font-weight:600;font-size:9.4pt;color:#fff;white-space:nowrap}}
.grade.sahih{{background:#2e7d4f}} .grade.hasan{{background:#2b7a8a}} .grade.mixed{{background:#b7791f}} .grade.quran{{background:#5b4bb0}}
.arbox{{background:var(--cream);border:1px solid #eadfc4;border-radius:6px;margin:.55em .8em;padding:.35em .9em;break-inside:avoid}}
.arlabel{{font-size:9.5pt;color:var(--gold);font-weight:600;margin-top:.2em}}
.qbox{{margin:.55em .8em;border:1px solid #eadfc4;border-radius:6px;background:var(--cream);padding:.3em .9em .4em}}
.sname{{text-align:center;font-weight:700;color:var(--g);font-size:11pt;margin:.2em 0 0;letter-spacing:.02em}}
.bism{{font-size:18pt;color:var(--g)}}
.verse{{border-top:1px dashed #e6dcc3;padding:.15em 0 .3em;break-inside:avoid}}
.verse:first-of-type{{border-top:0}}
.qbn{{margin:.3em 0 .2em;font-size:10.3pt;color:#2e3a34;text-align:justify;border-top:1px dashed #e6dcc3;padding-top:.35em}} .qbn b{{color:var(--g)}}
.vn{{color:var(--gold);font-weight:700}}
p.mean{{margin:.5em .9em .2em;text-align:justify}} p.mean b{{color:var(--g)}}
p.mean.eve{{margin-top:.1em;font-size:10pt;color:var(--mut)}}
.fadl{{margin:.55em .8em .3em;background:var(--goldl);border-left:4px solid var(--gold);border-radius:4px;padding:.35em .8em}}
.ftitle{{font-weight:700;color:#7a5a17;font-size:10.3pt}}
.fadl p{{margin:.2em 0;text-align:justify;font-size:10.4pt}}
p.note{{margin:.4em .9em;font-size:10pt;background:#f3f6f9;border-left:4px solid #6b8aa6;padding:.3em .7em;border-radius:4px}}
p.ref{{margin:.4em .9em 0;font-size:9.4pt;color:var(--mut)}} p.ref b{{color:#38463f}}
.warn{{border:1.5px solid #c9542f;background:#fdf1ec;border-radius:8px;padding:.5em 1em;margin:1em 0;break-inside:avoid}}
.warn .wt{{font-weight:700;color:#a63f1f;font-size:12pt}}
.warn p{{font-size:10pt;margin:.3em 0;color:#5a3a2e}}
table.rt{{width:100%;border-collapse:collapse;font-size:10pt;margin:.3em 0 1em}}
table.rt th{{background:var(--g);color:#fff;font-weight:600;padding:.4em .5em;text-align:left}}
table.rt td{{border:1px solid var(--line);padding:.4em .55em;vertical-align:top}}
table.rt tr:nth-child(even) td{{background:#f6f9f7}}
table.rt td.tm{{font-weight:600;color:var(--g);width:22%}}
table.rt td.dl{{color:#4a5650;font-size:9.4pt;width:36%}}
table.t2 td.dl{{width:45%}}
table.rt tr{{break-inside:avoid}}
table.trk{{width:100%;border-collapse:collapse;font-size:10pt}}
table.trk th{{background:var(--g);color:#fff;font-weight:600;padding:.35em;border:1px solid var(--g)}}
table.trk td{{border:1px solid #b9c7bf;height:1.75em;padding:.1em .5em}}
table.trk td:not(:first-child){{width:9%}}
table.trk tr:nth-child(even) td{{background:#f6f9f7}}
p.disc{{margin-top:1.2em;background:var(--gl);border:1px solid #c5d9cd;padding:.7em 1em;border-radius:6px;font-weight:500;color:#24443a}}
.toc .toch{{color:var(--g);font-size:22pt;text-align:center;margin:.4em 0 .6em;border-bottom:3px double var(--gold);padding-bottom:.3em}}
.toc ol{{list-style:none;padding:0;counter-reset:t;font-size:12.5pt}}
.toc li{{padding:.55em .8em;margin:.35em 0;border:1px solid var(--line);border-left:5px solid var(--gold);border-radius:5px;background:#fbfcfb}}
.toc a{{color:var(--ink);text-decoration:none;font-weight:500}}
.legend{{margin-top:1.4em;border:1px solid var(--line);border-radius:6px;padding:.6em 1em;font-size:10.2pt;line-height:2.1}}
.legend .lt{{font-weight:700;color:var(--g)}}
.cover{{height:258mm;display:flex}}
.cover .frame{{flex:1;border:3px solid var(--g);outline:1.5px solid var(--gold);outline-offset:-9px;border-radius:10px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:14mm;text-align:center;background:radial-gradient(circle at 50% 38%,#fffdf6 0,#f8f2e3 70%)}}
.cbism{{font-size:26pt;color:var(--g)}}
.orn{{font-family:IndoPak;color:var(--gold);font-size:30pt;margin:.2em 0 .1em}}
.ctitle{{font-size:31pt;font-weight:700;color:var(--g);margin:.15em 0 .2em;line-height:1.35}}
.csub{{font-size:15pt;font-weight:600;color:#7a5a17;margin:0}}
.rule{{width:45%;height:2px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:1.1em 0}}
.csub2,.csub3{{font-size:11.5pt;color:#33413a;margin:.25em 0}}
.cayah{{font-size:21pt;margin-top:1.6em;color:#14231c}}
.caref{{font-size:10pt;color:var(--mut);margin:0}}
.cdate{{margin-top:2.2em;font-size:10pt;color:var(--mut)}}
"""

def page(inner):
    return f'<!doctype html><html lang="bn"><head><meta charset="utf-8"><title>সকাল-সন্ধ্যা ও রাতের মাসনূন আমল</title><style>{CSS}</style></head><body>{inner}</body></html>'

if __name__ == "__main__":
    open("cover.html", "w").write(page(cover()))
    open("body.html", "w").write(page(body()))
    print("ok")
