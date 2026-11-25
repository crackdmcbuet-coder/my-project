#!/usr/bin/env python3
"""Build an A5 book (FODT -> PDF + DOCX) from the simple markup used for the
Bengali translations.

usage: build_book.py OUT_BASENAME quran.json file1.txt [file2.txt ...]

Markup
  %key: value          title-page fields (title_ar, title, subtitle, author,
                       extra, takhrij, translator, publisher)
  # Chapter            ## Section        @sub: run-in sub-heading
  @ar: Arabic line     @center: centred line        | verse line
  text[^label]  +  a line "[^label]: footnote text"
"""
import json
import re
import subprocess
import sys
from difflib import SequenceMatcher
from xml.sax.saxutils import escape

BN = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')
EN = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')

# ---------------------------------------------------------------- Qur'an
DIAC = re.compile('[ؐ-ًؚ-ٰٟۖ-ۭ࣓-ࣿـ‏‎]')


def skel(w):
    w = DIAC.sub('', w)
    w = re.sub('[اٱأإآء]', '', w)
    return w.replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي')


class Quran:
    def __init__(self, path):
        data = json.load(open(path, encoding='utf-8'))['quran']
        self.suras = {}
        for v in data:
            words = v['text'].replace('‏', '').split()
            st = self.suras.setdefault(v['chapter'], [])
            for w in words:
                s = skel(w)
                if s:
                    st.append((s, w, v['verse']))
                elif st:  # stand-alone waqf mark: glue to the previous word
                    st[-1] = (st[-1][0], st[-1][1] + ' ' + w, st[-1][2])

    def find(self, frag, ayah_hint=None):
        fw = [skel(w) for w in frag.split()]
        fw = [w for w in fw if w]
        n = len(fw)
        if not n:
            return None
        target = ' '.join(fw)
        best = None
        for su, st in self.suras.items():
            for i in range(len(st) - n + 1):
                win = st[i:i + n]
                same = sum(1 for a, b in zip(fw, win) if a == b[0])
                if same < max(1, int(n * 0.55)):
                    continue
                r = SequenceMatcher(None, target, ' '.join(x[0] for x in win)).ratio()
                if r < 0.86:
                    continue
                ayat = {x[2] for x in win}
                bonus = 0.05 if ayah_hint and ayah_hint & ayat else 0
                if best is None or r + bonus > best[0]:
                    txt = ' '.join(x[1] for x in win)
                    txt = re.sub('[\u06d6-\u06dc\u06de\u06e9 ]+$', '', txt)
                    best = (r + bonus, su, sorted(ayat), txt)
        return best


def fix_quran(lines, quran, log):
    """Replace undiacritised ayah text in @ar lines by the Uthmani text."""
    out = list(lines)
    for i, ln in enumerate(lines):
        if not ln.startswith('@ar:') or '﴿' not in ln:
            continue
        hint = set()
        for j in range(i + 1, min(i + 4, len(lines))):
            m = re.search(r'\[[^\]]*?:\s*([০-৯0-9]+)(?:\s*[-–—]\s*([০-৯0-9]+))?\]', lines[j])
            if m:
                a = int(m.group(1).translate(EN))
                b = int(m.group(2).translate(EN)) if m.group(2) else a
                hint = set(range(a, b + 1))
                break

        def rep(m):
            frag = m.group(1).strip()
            hit = quran.find(frag, hint)
            if not hit:
                log.append('QURAN no match: ' + frag)
                return m.group(0)
            if hint and not (hint & set(hit[2])):
                log.append('QURAN ref mismatch: %s -> found %d:%s, cited %s' % (frag, hit[1], hit[2], sorted(hint)))
            return '﴿' + hit[3] + '﴾'

        out[i] = re.sub('﴿([^﴾]*)﴾', rep, ln)
    return out


# ---------------------------------------------------------------- parse
def parse(files, quran, log):
    meta, blocks, notes = {}, [], {}
    for path in files:
        lines = open(path, encoding='utf-8').read().split('\n')
        lines = fix_quran(lines, quran, log) if quran else lines
        para = []

        def flush():
            if para:
                blocks.append(('p', ' '.join(para)))
                para.clear()

        for ln in lines:
            s = ln.strip()
            m = re.match(r'^\[\^([^\]]+)\]:\s*(.*)$', s)
            if m:
                flush()
                notes[m.group(1)] = m.group(2)
            elif not s:
                flush()
            elif s.startswith('%'):
                flush()
                k, _, v = s[1:].partition(':')
                meta[k.strip()] = v.strip()
            elif s.startswith('## '):
                flush(); blocks.append(('h2', s[3:].strip()))
            elif s.startswith('# '):
                flush(); blocks.append(('h1', s[2:].strip()))
            elif s.startswith('@sub:'):
                flush(); blocks.append(('sub', s[5:].strip()))
            elif s.startswith('@ar:'):
                flush(); blocks.append(('ar', s[4:].strip()))
            elif s.startswith('@center:'):
                flush(); blocks.append(('center', s[8:].strip()))
            elif s.startswith('|'):
                flush(); blocks.append(('verse', s[1:].strip()))
            else:
                para.append(s)
        flush()
    return meta, blocks, notes


# ---------------------------------------------------------------- FODT
def tp(western, complex_=None, size=None, bold=False, italic=False, extra=''):
    complex_ = complex_ or western
    a = ('style:font-name="%s" style:font-name-asian="%s" style:font-name-complex="%s"'
         % (western, western, complex_))
    if size:
        a += ' fo:font-size="%spt" style:font-size-asian="%spt" style:font-size-complex="%spt"' % (size, size, size)
    if bold:
        a += ' fo:font-weight="bold" style:font-weight-asian="bold" style:font-weight-complex="bold"'
    if italic:
        a += ' fo:font-style="italic" style:font-style-asian="italic" style:font-style-complex="italic"'
    return '<style:text-properties %s %s/>' % (a, extra)


def pstyle(name, pp, t, parent='Standard', family='paragraph', extra=''):
    return ('<style:style style:name="%s" style:family="%s" style:parent-style-name="%s" %s>'
            '<style:paragraph-properties %s/>%s</style:style>' % (name, family, parent, extra, pp, t))


BODY, HEAD, ARAB = 'Tiro Bangla', 'Hind Siliguri', 'Amiri'
LANG = 'fo:language="bn" fo:country="BD" style:language-complex="bn" style:country-complex="BD"'
ARLANG = 'fo:language="ar" fo:country="SA" style:language-complex="ar" style:country-complex="SA"'

STYLES = '\n'.join([
    '<style:default-style style:family="paragraph">'
    '<style:paragraph-properties fo:hyphenation-ladder-count="no-limit" style:writing-mode="lr-tb"/>'
    + tp(BODY, size=11, extra=LANG) + '</style:default-style>',
    '<style:style style:name="Standard" style:family="paragraph">'
    '<style:paragraph-properties fo:text-align="justify" fo:line-height="160%" fo:margin-top="0cm" '
    'fo:margin-bottom="0.22cm" fo:orphans="2" fo:widows="2"/>' + tp(BODY, size=11) + '</style:style>',
    pstyle('Chapter', 'fo:text-align="center" fo:line-height="140%" fo:margin-top="1.2cm" fo:margin-bottom="0.8cm" '
           'fo:break-before="page" fo:keep-with-next="always"', tp(HEAD, size=17, bold=True),
           extra='style:default-outline-level="1"'),
    pstyle('Section', 'fo:text-align="center" fo:line-height="140%" fo:margin-top="0.55cm" fo:margin-bottom="0.3cm" '
           'fo:keep-with-next="always"', tp(HEAD, size=13.5, bold=True), extra='style:default-outline-level="2"'),
    pstyle('SubHead', 'fo:text-align="start" fo:line-height="140%" fo:margin-top="0.35cm" fo:margin-bottom="0.15cm" '
           'fo:keep-with-next="always"', tp(HEAD, size=11.5, bold=True)),
    pstyle('Arabic', 'fo:text-align="center" fo:line-height="190%" fo:margin-top="0.1cm" fo:margin-bottom="0.05cm" '
           'style:writing-mode="rl-tb" fo:keep-with-next="always"', tp(ARAB, size=14.5, extra=ARLANG)),
    pstyle('Centered', 'fo:text-align="center" fo:margin-bottom="0.25cm" fo:margin-left="0.6cm" fo:margin-right="0.6cm"',
           tp(BODY, size=11)),
    pstyle('Verse', 'fo:text-align="start" fo:margin-left="1.1cm" fo:margin-bottom="0.04cm" fo:line-height="150%"',
           tp(BODY, size=11, italic=True)),
    pstyle('VerseEnd', 'fo:text-align="start" fo:margin-left="1.1cm" fo:margin-bottom="0.25cm" fo:line-height="150%"',
           tp(BODY, size=11, italic=True)),
    pstyle('Footnote', 'fo:text-align="justify" fo:line-height="135%" fo:margin-left="0.45cm" fo:text-indent="-0.45cm" '
           'fo:margin-bottom="0.04cm"', tp(BODY, size=8.5)),
    pstyle('Footer', 'fo:text-align="center"', tp(HEAD, size=9)),
    pstyle('TitleArabic', 'fo:text-align="center" fo:margin-top="0.6cm" fo:margin-bottom="0.2cm" style:writing-mode="rl-tb" '
           'fo:line-height="170%"', tp(ARAB, size=22, bold=True, extra=ARLANG)),
    pstyle('Title', 'fo:text-align="center" fo:margin-top="0.4cm" fo:margin-bottom="0.2cm" fo:line-height="130%"',
           tp(HEAD, size=26, bold=True)),
    pstyle('Subtitle', 'fo:text-align="center" fo:margin-bottom="0.7cm" fo:line-height="140%"', tp(HEAD, size=13)),
    pstyle('Author', 'fo:text-align="center" fo:margin-top="0.6cm" fo:margin-bottom="0.05cm" fo:line-height="140%"',
           tp(HEAD, size=15, bold=True)),
    pstyle('TitleSmall', 'fo:text-align="center" fo:margin-bottom="0.1cm" fo:line-height="140%"', tp(HEAD, size=11)),
    pstyle('TitleLabel', 'fo:text-align="center" fo:margin-top="0.8cm" fo:margin-bottom="0.05cm" fo:line-height="140%"',
           tp(HEAD, size=11)),
    pstyle('Translator', 'fo:text-align="center" fo:margin-bottom="0.1cm" fo:line-height="140%"',
           tp(HEAD, size=14, bold=True)),
    pstyle('Publisher', 'fo:text-align="center" fo:margin-top="1.1cm" fo:line-height="140%"', tp(HEAD, size=13, bold=True)),
    '<style:style style:name="FnAnchor" style:family="text"><style:text-properties style:text-position="super 62%"/></style:style>',
    '<text:notes-configuration text:note-class="footnote" style:num-format="1" text:start-numbering-at="document" '
    'text:footnotes-position="page" text:citation-style-name="FnAnchor" text:citation-body-style-name="FnAnchor" '
    'text:default-style-name="Footnote"/>',
])

PAGE = ('fo:page-width="14.8cm" fo:page-height="21cm" fo:margin-top="1.7cm" fo:margin-bottom="1.5cm" '
        'fo:margin-left="1.8cm" fo:margin-right="1.8cm" style:writing-mode="lr-tb" style:footnote-max-height="7cm"')
SEP = ('<style:footnote-sep style:width="0.018cm" style:distance-before-sep="0.25cm" style:distance-after-sep="0.15cm" '
       'style:line-style="solid" style:adjustment="left" style:rel-width="30%" style:color="#000000"/>')

HEADER = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">
<office:meta><dc:title>%(title)s</dc:title></office:meta>
<office:font-face-decls>
<style:font-face style:name="Tiro Bangla" svg:font-family="'Tiro Bangla'"/>
<style:font-face style:name="Hind Siliguri" svg:font-family="'Hind Siliguri'"/>
<style:font-face style:name="Amiri" svg:font-family="Amiri"/>
</office:font-face-decls>
<office:styles>
%(styles)s
</office:styles>
<office:automatic-styles>
<style:page-layout style:name="pm0"><style:page-layout-properties %(page)s/></style:page-layout>
<style:page-layout style:name="pm1"><style:page-layout-properties %(page)s style:num-format="১, ২, ৩, ...">%(sep)s</style:page-layout-properties>
<style:footer-style><style:header-footer-properties fo:min-height="0.7cm" fo:margin-top="0.25cm"/></style:footer-style></style:page-layout>
<style:style style:name="TitleFirst" style:family="paragraph" style:parent-style-name="%(first)s" style:master-page-name="First"/>
<style:style style:name="BodyFirst" style:family="paragraph" style:parent-style-name="Chapter" style:master-page-name="Standard"><style:paragraph-properties style:page-number="1"/></style:style>
</office:automatic-styles>
<office:master-styles>
<style:master-page style:name="Standard" style:page-layout-name="pm1"><style:footer><text:p text:style-name="Footer"><text:page-number text:select-page="current" style:num-format="১, ২, ৩, ..."/></text:p></style:footer></style:master-page>
<style:master-page style:name="First" style:page-layout-name="pm0" style:next-style-name="Standard"/>
</office:master-styles>
<office:body><office:text>
'''


def smart(t):
    """Straight quotes -> typographic quotes (Bengali text only)."""
    t = re.sub(r'(^|[\s(\[—–\u2018])"', '\\1\u201c', t)
    t = t.replace('"', '\u201d')
    t = re.sub(r"(^|[\s(\[—–\u201c])'", '\\1\u2018', t)
    return t.replace("'", '\u2019')


def inline(text, notes, counter, log):
    """Escape text and turn [^label] into real footnotes."""
    text = smart(text)
    out, pos = [], 0
    for m in re.finditer(r'\[\^([^\]]+)\]', text):
        out.append(escape(text[pos:m.start()]))
        pos = m.end()
        lab = m.group(1)
        if lab not in notes:
            log.append('FOOTNOTE missing definition: ' + lab)
            continue
        notes[lab + '\0used'] = True
        counter[0] += 1
        num = str(counter[0]).translate(BN)
        out.append('<text:note text:note-class="footnote"><text:note-citation text:label="%s">%s</text:note-citation>'
                   '<text:note-body><text:p text:style-name="Footnote">%s</text:p></text:note-body></text:note>'
                   % (num, num, escape(smart(notes[lab]))))
    out.append(escape(text[pos:]))
    return ''.join(out)


def build(meta, blocks, notes, log):
    body = []
    title_fields = [('title_ar', 'TitleArabic'), ('title', 'Title'), ('subtitle', 'Subtitle'), ('author', 'Author'),
                    ('extra', 'TitleSmall'), ('takhrij', 'TitleSmall'), ('_label', 'TitleLabel'),
                    ('translator', 'Translator'), ('publisher', 'Publisher')]
    first = True
    first_style = 'TitleArabic'
    for key, st in title_fields:
        val = 'অনুবাদ' if key == '_label' and meta.get('translator') else meta.get(key)
        if not val:
            continue
        if first:
            first_style = st
        body.append('<text:p text:style-name="%s">%s</text:p>' % ('TitleFirst' if first else st, escape(val)))
        first = False
    counter = [0]
    first_ch = True
    n = len(blocks)
    for i, (kind, text) in enumerate(blocks):
        if kind == 'h1':
            counter[0] = 0
            st = 'BodyFirst' if first_ch else 'Chapter'
            first_ch = False
            body.append('<text:h text:style-name="%s" text:outline-level="1">%s</text:h>' % (st, inline(text, notes, counter, log)))
        elif kind == 'h2':
            body.append('<text:h text:style-name="Section" text:outline-level="2">%s</text:h>' % inline(text, notes, counter, log))
        elif kind == 'verse':
            last = i + 1 >= n or blocks[i + 1][0] != 'verse'
            body.append('<text:p text:style-name="%s">%s</text:p>' % ('VerseEnd' if last else 'Verse', inline(text, notes, counter, log)))
        else:
            st = {'p': 'Standard', 'sub': 'SubHead', 'ar': 'Arabic', 'center': 'Centered'}[kind]
            body.append('<text:p text:style-name="%s">%s</text:p>' % (st, inline(text, notes, counter, log)))
    for k in notes:
        if not k.endswith('\0used') and (k + '\0used') not in notes:
            log.append('FOOTNOTE never referenced: ' + k)
    head = HEADER % dict(title=escape(meta.get('title', '')), styles=STYLES, page=PAGE, sep=SEP, first=first_style)
    return head + '\n'.join(body) + '\n</office:text></office:body></office:document>\n'


def main():
    out, qpath, files = sys.argv[1], sys.argv[2], sys.argv[3:]
    log = []
    quran = Quran(qpath) if qpath != '-' else None
    meta, blocks, notes = parse(files, quran, log)
    fodt = out + '.fodt'
    open(fodt, 'w', encoding='utf-8').write(build(meta, blocks, notes, log))
    outdir = fodt.rsplit('/', 1)[0] if '/' in fodt else '.'
    for fmt in ('pdf', 'docx'):
        subprocess.run(['soffice', '--headless', '--convert-to', fmt, '--outdir', outdir, fodt],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('blocks', len(blocks), 'footnotes', sum(1 for k in notes if not k.endswith('\0used')))
    for l in log:
        print('WARN', l)


if __name__ == '__main__':
    main()
