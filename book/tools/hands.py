import math, os, sys
OUT = sys.argv[1]
SKIN, LINE, ACC = "#f3d2b5", "#7a4b2a", "#c0392b"
# finger bases on top edge of palm (x, y); palm from x=55..145, y=120..200
BASE = {"thumb": (55, 165), "index": (66, 120), "middle": (89, 118), "ring": (112, 120), "little": (134, 126)}
LEN = {"thumb": 52, "index": 66, "middle": 74, "ring": 68, "little": 52}
W = 19
DEF_ANG = {"thumb": -55, "index": -6, "middle": 0, "ring": 6, "little": 14}

def seg(x, y, ang, L, hl=False):
    a = math.radians(ang)
    ex, ey = x + L*math.sin(a), y - L*math.cos(a)
    col = ACC if hl else LINE
    sw = 3 if hl else 1.6
    return (f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{col}" stroke-width="{W+sw*2}" stroke-linecap="round"/>'
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{SKIN}" stroke-width="{W}" stroke-linecap="round"/>', (ex, ey))

def finger(name, st, hl):
    x, y = BASE[name]; L = LEN[name]; ang = DEF_ANG[name]
    out = []
    if name == "thumb":
        if st in ("out", "up"): ang = -55 if st == "out" else -20
        elif st == "fold":  # across palm
            s, _ = seg(x+4, y+10, 75, 46, hl); return [s]
        elif st == "hidden": return []
        elif st.startswith("between:"):  # tip poking between two folded fingers
            a, b = st.split(":")[1].split("-")
            gx = (BASE[a][0] + BASE[b][0]) / 2
            s, _ = seg(gx, 150, 0, 22, True); return [s]
        s, _ = seg(x, y, ang, L, hl); return [s]
    if st == "up": pass
    elif st == "spread": ang += -22 if name in ("index",) else 24 if name == "little" else 14
    elif st == "wide": ang += -38 if name == "index" else 42
    elif st == "fold":
        s, _ = seg(x, y+4, 0, 12, hl); return [s]
    elif st == "half":
        s, p = seg(x, y, ang, L*0.5, hl); s2, _ = seg(*p, ang+150, 18, hl); return [s, s2]
    elif st == "claw":
        s, p = seg(x, y, ang, L*0.45, hl); s2, _ = seg(*p, ang+135, L*0.3, hl); return [s, s2]
    elif st == "ring":  # curled to meet thumb (OK sign)
        return [f'<circle cx="{x-4}" cy="{y-16}" r="17" fill="none" stroke="{ACC}" stroke-width="{W}"/>'
                f'<circle cx="{x-4}" cy="{y-16}" r="17" fill="none" stroke="{SKIN}" stroke-width="{W-4}"/>']
    elif st == "down":  # pointing downward over palm
        s, _ = seg(x, y+6, 180, L*0.7, hl); return [s]
    s, _ = seg(x, y, ang, L, hl); return [s]

def hand(spec, hl=()):
    parts = []
    order = ["little", "ring", "middle", "index", "thumb"]
    for n in order:
        if n == "thumb": continue
        parts += finger(n, spec.get(n, "up"), n in hl)
    palm = (f'<rect x="50" y="118" width="100" height="86" rx="26" fill="{SKIN}" stroke="{LINE}" stroke-width="1.6"/>'
            f'<rect x="72" y="200" width="56" height="34" fill="{SKIN}" stroke="{LINE}" stroke-width="1.6"/>'
            f'<rect x="73" y="196" width="54" height="10" fill="{SKIN}"/>')
    folded = [n for n in order if spec.get(n) == "fold"]
    th = finger("thumb", spec.get("thumb", "out"), "thumb" in hl)
    # knuckle marks for folded fingers
    kn = "".join(f'<path d="M{BASE[n][0]-9},{BASE[n][1]+14} q9,8 18,0" fill="none" stroke="{LINE}" stroke-width="1.4"/>' for n in folded)
    return "".join(parts) + palm + kn + "".join(th)

def svg(spec, title, sub, hl=()):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 290" width="200" height="290">'
            f'<rect width="200" height="290" fill="#ffffff"/>' + hand(spec, hl) +
            f'<text x="100" y="258" text-anchor="middle" font-family="Noto Sans Bengali, Noto Sans, sans-serif" font-size="13" font-weight="bold" fill="#222">{title}</text>'
            f'<text x="100" y="278" text-anchor="middle" font-family="Noto Sans Bengali, Noto Sans, sans-serif" font-size="10.5" fill="#555">{sub}</text></svg>')

F = "fold"
G = {
 "01-open-spread": ({"index":"spread","ring":"spread","little":"wide","thumb":"out"}, "সব আঙুল ফাঁক", "খোলা হাত", ()),
 "02-fist": ({"index":F,"middle":F,"ring":F,"little":F,"thumb":"fold"}, "মুষ্টি", "সব আঙুল ভাঁজ", ()),
 "03-index-up": ({"middle":F,"ring":F,"little":F,"thumb":"fold"}, "তর্জনী উঁচু", "তাওহীদের ইশারা", ("index",)),
 "04-v-sign": ({"index":"spread","ring":F,"little":F,"thumb":"fold"}, "তর্জনী-মধ্যমা (V)", "বাকি আঙুল ভাঁজ", ("index","middle")),
 "05-horns": ({"middle":F,"ring":F,"little":"spread","thumb":"fold"}, "শিং (তর্জনী+কড়ে)", "মধ্যমা-অনামিকা ভাঁজ", ("index","little")),
 "06-ok-ring": ({"index":"ring","thumb":"hidden","little":"spread"}, "বুড়ো-তর্জনী বৃত্ত", "বাকি তিন আঙুল খোলা", ("index",)),
 "07-l-shape": ({"middle":F,"ring":F,"little":F,"thumb":"out"}, "L আকার", "তর্জনী উঁচু, বুড়ো আঙুল বাইরে", ("index","thumb")),
 "08-little-slight": ({"little":"spread"}, "কড়ে আঙুল সামান্য ফাঁক", "বাকি আঙুল জোড়া", ("little",)),
 "09-little-wide": ({"little":"wide"}, "কড়ে আঙুল অনেক ফাঁক", "বাকি আঙুল জোড়া", ("little",)),
 "10-little-ring-spread": ({"ring":"spread","little":"wide"}, "কড়ে+অনামিকা ফাঁক", "মধ্যমা থেকে আলাদা", ("ring","little")),
 "11-index-little-spread": ({"index":"spread","little":"spread"}, "তর্জনী+কড়ে ফাঁক", "দুই প্রান্তের আঙুল", ("index","little")),
 "12-middle-ring-gap": ({"index":"up","middle":"up","ring":"spread","little":"spread"}, "মধ্যমা-অনামিকার মাঝে ফাঁক", "হাত দুই ভাগে", ("ring","little")),
 "13-index-wide": ({"index":"wide"}, "তর্জনী অনেক ফাঁক", "বাকি আঙুল জোড়া", ("index",)),
 "14-middle-down": ({"middle":F}, "মধ্যমা নিচে নামা", "বাকি আঙুল খোলা", ("middle",)),
 "15-middle-up-alone": ({"index":F,"ring":F,"little":F,"thumb":"fold"}, "শুধু মধ্যমা উঁচু", "বাকি আঙুল ভাঁজ", ("middle",)),
 "16-thumb-index-middle": ({"index":F,"middle":F,"ring":F,"little":F,"thumb":"between:index-middle"}, "বুড়ো আঙুল তর্জনী-মধ্যমার মাঝে", "মুষ্টির ভেতর দিয়ে", ("thumb",)),
 "17-thumb-middle-ring": ({"index":F,"middle":F,"ring":F,"little":F,"thumb":"between:middle-ring"}, "বুড়ো আঙুল মধ্যমা-অনামিকার মাঝে", "মুষ্টির ভেতর দিয়ে", ("thumb",)),
 "18-claw": ({"index":"claw","middle":"claw","ring":"claw","little":"claw","thumb":"out"}, "থাবা", "সব আঙুল বাঁকানো", ()),
 "19-three-fingers": ({"index":"spread","ring":F,"little":F,"thumb":"up"}, "তিন আঙুল", "বুড়ো+তর্জনী+মধ্যমা", ("thumb","index","middle")),
 "20-thumb-little": ({"index":F,"middle":F,"ring":F,"little":"wide","thumb":"out"}, "বুড়ো+কড়ে খোলা", "বাকি আঙুল ভাঁজ", ("thumb","little")),
 "21-ily": ({"middle":F,"ring":F,"little":"spread","thumb":"out"}, "বুড়ো+তর্জনী+কড়ে", "মধ্যমা-অনামিকা ভাঁজ", ("thumb","index","little")),
 "22-index-half": ({"index":"half"}, "তর্জনী অর্ধেক বাঁকা", "বাকি আঙুল খোলা", ("index",)),
}
for k, (spec, t, s, hl) in G.items():
    open(os.path.join(OUT, k + ".svg"), "w").write(svg(spec, t, s, hl))
print(len(G))
