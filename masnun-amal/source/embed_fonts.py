"""DOCX-এ TrueType ফন্ট এমবেড করা (ECMA-376 §17.8.1 obfuscation)।"""
import sys, uuid, zipfile, os

FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
FONTS = [  # (font name, {kind: file})
    ("AlQuran IndoPak by QuranWBW", {"Regular": "IndoPak.ttf"}),
    ("Hind Siliguri", {"Regular": "HindSiliguri-Regular.ttf", "Bold": "HindSiliguri-SemiBold.ttf"}),
    ("Amiri", {"Regular": "Amiri-Regular.ttf"}),
]

def obfuscate(data, guid):
    key = bytes.fromhex(guid.replace("-", ""))[::-1]
    b = bytearray(data)
    for i in range(32): b[i] ^= key[i % 16]
    return bytes(b)

src, dst = sys.argv[1], sys.argv[2]
zin = zipfile.ZipFile(src)
files = {n: zin.read(n) for n in zin.namelist()}
fonts_xml, rels = [], []
n = 0
for name, kinds in FONTS:
    emb = []
    for kind, fn in kinds.items():
        n += 1
        guid = str(uuid.uuid4()).upper()
        files[f"word/fonts/font{n}.odttf"] = obfuscate(open(os.path.join(FD, fn), "rb").read(), guid)
        rels.append(f'<Relationship Id="rIdF{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/font" Target="fonts/font{n}.odttf"/>')
        emb.append(f'<w:embed{kind} r:id="rIdF{n}" w:fontKey="{{{guid}}}"/>')
    fonts_xml.append(f'<w:font w:name="{name}"><w:charset w:val="00"/><w:family w:val="auto"/><w:pitch w:val="variable"/>{"".join(emb)}</w:font>')

ft = files["word/fontTable.xml"].decode()
assert ft.endswith("/>"), "unexpected fontTable"
ft = ft[:-2] + ">" + "".join(fonts_xml) + "</w:fonts>"
files["word/fontTable.xml"] = ft.encode()
files["word/_rels/fontTable.xml.rels"] = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(rels) + "</Relationships>").encode()
import re
ORDER = ["top", "left", "bottom", "right", "between", "bar"]
def fix_bdr(m):
    kids = re.findall(r"<w:(\w+) [^>]*/>", m.group(1))
    els = re.findall(r"(<w:(\w+) [^>]*/>)", m.group(1))
    els.sort(key=lambda e: ORDER.index(e[1]))
    return "<w:pBdr>" + "".join(e[0] for e in els) + "</w:pBdr>"
for part in ("word/document.xml", "word/styles.xml"):
    files[part] = re.sub(r"<w:pBdr>(.*?)</w:pBdr>", fix_bdr, files[part].decode()).encode()
# docx-js সব বুকমার্কে একই id দেয়; ক্রমিকভাবে নতুন id
doc = files["word/document.xml"].decode()
cnt = iter(range(1, 10000)); cur = {}
def bm(m):
    if m.group(1) == "Start":
        cur["id"] = next(cnt)
        return m.group(0).replace(f'w:id="{m.group(2)}"', f'w:id="{cur["id"]}"')
    return m.group(0).replace(f'w:id="{m.group(2)}"', f'w:id="{cur["id"]}"')
doc = re.sub(r'<w:bookmark(Start|End)[^>]*w:id="(\d+)"[^>]*/>', bm, doc)
files["word/document.xml"] = doc.encode()
st = files["word/settings.xml"].decode()
st = st.replace("<w:displayBackgroundShape/>", "<w:displayBackgroundShape/><w:embedTrueTypeFonts/>", 1)
assert "embedTrueTypeFonts" in st
files["word/settings.xml"] = st.encode()
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    order = ["[Content_Types].xml"] + [k for k in files if k != "[Content_Types].xml"]
    for k in order: z.writestr(k, files[k])
print("embedded", n, "font files ->", dst)
