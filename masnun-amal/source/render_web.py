# -*- coding: utf-8 -*-
"""blocks.json -> ওয়েবসাইটের জন্য রেসপন্সিভ HTML।

ব্যবহার: python3 render_web.py <out_dir> [--single]
  out_dir/index.html + out_dir/assets/fonts/*.woff2   (ফোল্ডার সংস্করণ)
  --single দিলে ফন্টসহ সবকিছু একটি HTML ফাইলের ভেতরে (base64)
"""
import base64, os, sys
from fontTools import subset
from fontTools.ttLib import TTFont
import render_html as R

FONTS = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts"))
WEBFONTS = [  # (css family, weight, source ttf, subset text or None)
    ("IndoPak", 400, "IndoPak.ttf", None),
    ("Hind", 400, "HindSiliguri-Regular.ttf", None),
    ("Hind", 600, "HindSiliguri-SemiBold.ttf", None),
    ("Hind", 700, "HindSiliguri-Bold.ttf", None),
    ("AmiriD", 400, "Amiri-Regular.ttf", "٠١٢٣٤٥٦٧٨٩ﷺ"),
]

def make_woff2(src, dst, text):
    if text:
        opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]
        f = TTFont(src); s = subset.Subsetter(opts); s.populate(text=text); s.subset(f)
        f.flavor = "woff2"; f.save(dst)
    else:
        f = TTFont(src); f.flavor = "woff2"; f.save(dst)

def font_css(out_dir, single):
    os.makedirs(os.path.join(out_dir, "assets", "fonts"), exist_ok=True)
    rules = []
    for fam, w, ttf, text in WEBFONTS:
        name = os.path.splitext(ttf)[0] + ".woff2"
        path = os.path.join(out_dir, "assets", "fonts", name)
        make_woff2(os.path.join(FONTS, ttf), path, text)
        if single:
            url = "data:font/woff2;base64," + base64.b64encode(open(path, "rb").read()).decode()
        else:
            url = "assets/fonts/" + name
        rules.append(f"@font-face{{font-family:{fam};src:url({url}) format('woff2');font-weight:{w};font-display:swap}}")
    if single:
        import shutil; shutil.rmtree(os.path.join(out_dir, "assets"))
    return "\n".join(rules)

CSS = """
:root{--g:#1d5a45;--g2:#2f7a5f;--gl:#e8f1ec;--gold:#b08a3e;--goldl:#f7efdc;--cream:#fcf9f2;--ink:#1f2522;--mut:#5b6660;--line:#d9e2dc;--bg:#f5f3ec;--card:#fff;--arink:#14231c}
@media (prefers-color-scheme:dark){:root{--g:#7cc4a4;--g2:#3f8f70;--gl:#1d2a25;--gold:#d2ab5c;--goldl:#2b2518;--cream:#1d1f1a;--ink:#e6ebe8;--mut:#9aa7a0;--line:#2f3a35;--bg:#121614;--card:#181d1b;--arink:#f1ede2}}
*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Hind,'Noto Sans Bengali',sans-serif;font-size:17px;line-height:1.7}
a{color:var(--g)}
.wrap{max-width:880px;margin:0 auto;padding:0 16px}
.saw{font-family:AmiriD,serif}
.ar{font-family:IndoPak,AmiriD,serif;direction:rtl;text-align:center;font-size:clamp(1.45rem,5vw,1.9rem);line-height:2.15;margin:.2em 0;color:var(--arink);word-spacing:.04em}
.dg{font-family:AmiriD,serif;font-size:.62em}
.sep{color:var(--gold);padding:0 .25em}
.ayn{color:var(--gold);white-space:nowrap}
.ayn .dg{font-size:.6em;padding:0 .08em}
/* hero */
.hero{background:linear-gradient(160deg,#1d5a45 0%,#2f7a5f 100%);color:#fff;text-align:center;padding:40px 16px 34px;border-bottom:5px solid #b08a3e}
.hero .ar{color:#fff;font-size:clamp(1.6rem,6vw,2.2rem)}
.hero h1{font-size:clamp(1.8rem,6.5vw,2.8rem);margin:.2em 0 .15em;line-height:1.3}
.hero .sub{font-size:clamp(1rem,3.6vw,1.2rem);color:#f3e2b5;margin:0 0 .6em;font-weight:600}
.hero .sub2{font-size:.95rem;opacity:.92;margin:.2em auto;max-width:640px}
.by{margin:1.1em auto 0;display:inline-block;border-top:1px solid rgba(243,226,181,.6);padding-top:.7em}
.by small{display:block;opacity:.85;font-size:.85rem}
.by b{display:block;font-size:1.25rem}
.by span{color:#f3e2b5;font-weight:600}
.dl{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:1.2em}
.dl a{background:#fff;color:#1d5a45;text-decoration:none;font-weight:600;padding:.45em 1.1em;border-radius:30px;font-size:.95rem}
.dl a.o{background:transparent;color:#fff;border:1.5px solid #f3e2b5}
/* sections */
main{padding:22px 0 40px}
h1.part{font-size:clamp(1.25rem,4.4vw,1.6rem);color:#fff;background:var(--g);padding:.55em .8em;border-radius:8px;margin:2.2em 0 .7em;border-bottom:4px solid var(--gold);scroll-margin-top:12px;line-height:1.4}
@media (prefers-color-scheme:dark){h1.part{background:#1f4a3b}}
p.lead{background:var(--gl);border-left:4px solid var(--g2);padding:.6em .9em;border-radius:6px;margin:0 0 1.1em}
h2{font-size:1.25rem;color:var(--g);border-bottom:2px solid var(--gold);padding-bottom:.15em;margin:1.6em 0 .7em}
p.para{margin:.4em 0 .8em}
ul{padding-left:1.3em} li{margin:.3em 0}
.item{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:0 0 18px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.ihead{display:flex;align-items:center;gap:.6em;background:linear-gradient(90deg,#1d5a45,#2f7a5f);color:#fff;padding:.55em .9em}
.ihead h3{margin:0;font-size:1.1rem;font-weight:600;line-height:1.4}
.no{display:inline-flex;align-items:center;justify-content:center;min-width:1.9em;height:1.9em;border-radius:50%;background:#b08a3e;color:#fff;font-weight:700;font-size:.9rem;flex:none}
.meta{display:flex;flex-wrap:wrap;gap:.4em;padding:.7em .9em .2em;font-size:.85rem}
.chip{background:var(--gl);border:1px solid var(--line);border-radius:20px;padding:.05em .75em}
.chip b{color:var(--g);font-weight:600}
.grade{border-radius:20px;padding:.05em .8em;font-weight:600;font-size:.85rem;color:#fff;white-space:nowrap}
.grade.sahih{background:#2e7d4f}.grade.hasan{background:#2b7a8a}.grade.mixed{background:#b7791f}
.arbox,.qbox{background:var(--cream);border:1px solid #eadfc4;border-radius:8px;margin:.7em .9em;padding:.4em .9em}
@media (prefers-color-scheme:dark){.arbox,.qbox{border-color:#3a3427}}
.arlabel{font-size:.85rem;color:var(--gold);font-weight:600;margin-top:.3em}
.sname{text-align:center;font-weight:700;color:var(--g);margin-top:.3em}
.bism{font-size:clamp(1.3rem,4.5vw,1.6rem)!important;color:var(--g)!important}
.qbn{margin:.4em 0 .3em;font-size:.95rem;border-top:1px dashed #e6dcc3;padding-top:.45em}
.qbn b{color:var(--g)} .vn{color:var(--gold);font-weight:700}
p.mean{margin:.6em .95em .2em} p.mean b{color:var(--g)}
p.mean.eve{font-size:.9rem;color:var(--mut);margin-top:.1em}
.fadl{margin:.7em .9em .3em;background:var(--goldl);border-left:4px solid var(--gold);border-radius:6px;padding:.45em .9em}
.ftitle{font-weight:700;color:#8a6a24;font-size:.95rem}
@media (prefers-color-scheme:dark){.ftitle{color:var(--gold)}}
.fadl p{margin:.25em 0;font-size:.95rem}
p.note{margin:.5em .95em;font-size:.9rem;background:var(--gl);border-left:4px solid #6b8aa6;padding:.35em .8em;border-radius:6px}
p.ref{margin:.5em .95em .8em;font-size:.85rem;color:var(--mut)}
.warn{border:1.5px solid #c9542f;background:#fdf1ec;color:#3a2a24;border-radius:10px;padding:.6em 1.1em;margin:1.2em 0}
@media (prefers-color-scheme:dark){.warn{background:#2a1c17;color:#ecd9d1}}
.warn .wt{font-weight:700;color:#c25a35;font-size:1.05rem}
.tw{overflow-x:auto;margin:.4em 0 1.2em;border-radius:8px;border:1px solid var(--line)}
table{width:100%;border-collapse:collapse;font-size:.92rem;background:var(--card)}
th{background:var(--g);color:#fff;font-weight:600;padding:.5em .6em;text-align:left;white-space:nowrap}
@media (prefers-color-scheme:dark){th{background:#1f4a3b}}
td{border-top:1px solid var(--line);padding:.5em .6em;vertical-align:top}
table.rt{min-width:620px} table.rt td.tm{font-weight:600;color:var(--g);width:22%}
table.rt td.dl{color:var(--mut);font-size:.85rem;width:36%}
table.trk{min-width:560px} table.trk td{height:2em} table.trk td+td{border-left:1px solid var(--line);width:9%}
p.disc{margin-top:1.4em;background:var(--gl);border:1px solid var(--line);padding:.8em 1em;border-radius:8px;font-weight:600}
.toc{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:1em 1.1em;margin-top:6px}
.toc .toch{font-size:1.4rem;color:var(--g);margin:0 0 .4em;text-align:center}
.toc ol{list-style:none;padding:0;margin:0}
.toc li{margin:.35em 0;border-left:4px solid var(--gold);background:var(--gl);border-radius:6px}
.toc a{display:block;padding:.5em .8em;text-decoration:none;color:var(--ink);font-weight:600}
.legend{margin-top:1em;font-size:.9rem;line-height:2.1}
.legend .lt{font-weight:700;color:var(--g)}
footer{background:#1d5a45;color:#e8f1ec;text-align:center;padding:24px 16px;font-size:.9rem;border-top:4px solid #b08a3e}
footer b{color:#fff}
.top{position:fixed;right:16px;bottom:16px;width:46px;height:46px;border-radius:50%;background:#b08a3e;color:#fff;display:flex;align-items:center;justify-content:center;text-decoration:none;font-size:1.3rem;box-shadow:0 2px 8px rgba(0,0,0,.25)}
@media print{.top,.dl{display:none}body{background:#fff}.item{break-inside:avoid}}
"""

def build(out_dir, single=False):
    os.makedirs(out_dir, exist_ok=True)
    fonts = font_css(out_dir, single)
    c = R.B[0]
    body = R.body()
    body = body.replace('<table class="rt', '<div class="tw"><table class="rt').replace('<table class="trk"', '<div class="tw"><table class="trk"').replace("</table>", "</table></div>")
    dl = "" if single else ('<div class="dl"><a href="downloads/sokal-sondha-rater-masnun-amal.pdf" download>PDF ডাউনলোড</a>'
                            '<a class="o" href="downloads/sokal-sondha-rater-masnun-amal.docx" download>Word (DOCX) ডাউনলোড</a></div>')
    page = f'''<!doctype html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{R.esc(c["title"])} | {R.esc(c["org"])}</title>
<meta name="description" content="{R.esc(c["sub"])}: সকাল-সন্ধ্যা ও রাতের যিকির, দুআ ও সূরা — আরবি (ইন্দো-পাক), বাংলা অর্থ, ফযীলত ও তথ্যসূত্রসহ। সারাদিনের আমলের তালিকা।">
<meta name="author" content="{R.esc(c["author"])} — {R.esc(c["org"])}">
<meta property="og:title" content="{R.esc(c["title"])}">
<meta property="og:description" content="{R.esc(c["sub"])} — {R.esc(c["org"])}">
<meta property="og:type" content="article">
<meta name="theme-color" content="#1d5a45">
<style>
{fonts}
{CSS}
</style>
</head>
<body>
<header class="hero" id="top">
<p class="ar">{R.artext(c["bismillah"])}</p>
<h1>{R.esc(c["title"])}</h1>
<p class="sub">{R.esc(c["sub"])}</p>
<p class="sub2">{R.esc(c["sub2"])}</p>
<p class="sub2">{R.esc(c["sub3"])}</p>
<div class="by"><small>সংকলন ও বিন্যাস</small><b>{R.esc(c["author"])}</b><span>{R.esc(c["org"])}</span></div>
{dl}
</header>
<main class="wrap">
{body}
</main>
<footer><b>{R.esc(c["title"])}</b><br>সংকলন ও বিন্যাস: <b>{R.esc(c["author"])}</b> — {R.esc(c["org"])}</footer>
<a class="top" href="#top" aria-label="উপরে যান">↑</a>
</body>
</html>'''
    name = "masnun-amal.html" if single else "index.html"
    open(os.path.join(out_dir, name), "w").write(page)
    return os.path.join(out_dir, name)

if __name__ == "__main__":
    print(build(sys.argv[1], "--single" in sys.argv))
