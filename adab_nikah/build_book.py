#!/usr/bin/env python3
"""Build an A5 Bengali book (PDF + DOCX with real footnotes) from simple markup.

Usage: build_book.py OUT_BASENAME file1.txt [file2.txt ...]

Markup:
  %title_ar: / %title: / %subtitle: / %author: / %extra: / %source: /
  %translator: / %publisher:          (title page, front file only)
  # Chapter heading                   (new page)
  ## Section heading
  @sub: run-in sub-heading
  @ar: Arabic line (RTL, Amiri)
  @center: centred line
  | verse line
  text[^key]   + a line "[^key]: footnote text" anywhere in the file
  blank line = paragraph break
"""
import os, re, subprocess, sys
from xml.sax.saxutils import escape

BN = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')


def bn(n):
    return str(n).translate(BN)


def parse(files):
    meta, blocks = {}, []
    for f in files:
        lines = open(f, encoding='utf-8').read().split('\n')
        notes = {}
        body = []
        for l in lines:
            m = re.match(r'^\s*\[\^([^\]]+)\]:\s*(.*)$', l)
            if m:
                notes[m.group(1)] = m.group(2).strip()
            else:
                body.append(l)
        para = []

        def flush():
            if para:
                blocks.append(('p', ' '.join(s.strip() for s in para), notes))
                para.clear()
        for l in body:
            s = l.rstrip()
            if s.startswith('%'):
                k, _, v = s[1:].partition(':')
                meta.setdefault(k.strip(), []).append(v.strip())
                continue
            if not s.strip():
                flush(); continue
            for pre, kind in (('## ', 'h2'), ('# ', 'h1'), ('@sub:', 'sub'),
                              ('@ar:', 'ar'), ('@center:', 'center'), ('| ', 'verse')):
                if s.startswith(pre):
                    flush()
                    blocks.append((kind, s[len(pre):].strip(), notes))
                    break
            else:
                para.append(s)
        flush()
    return meta, blocks


class Builder:
    def __init__(self):
        self.fn = 0
        self.used = set()

    def inline(self, text, notes):
        out, pos = [], 0
        for m in re.finditer(r'\[\^([^\]]+)\]', text):
            out.append(escape(text[pos:m.start()]))
            key = m.group(1)
            if key not in notes:
                sys.exit('missing footnote: ' + key)
            self.fn += 1
            lab = bn(self.fn)
            out.append('<text:note text:id="ftn%d" text:note-class="footnote">'
                       '<text:note-citation text:label="%s">%s</text:note-citation>'
                       '<text:note-body><text:p text:style-name="Footnote">%s</text:p>'
                       '</text:note-body></text:note>' % (len(self.used) + 1, lab, lab,
                                                          escape(notes[key])))
            self.used.add((id(notes), key))
            pos = m.end()
        out.append(escape(text[pos:]))
        s = ''.join(out)
        s = re.sub(r'\*\*(.+?)\*\*', r'<text:span text:style-name="B">\1</text:span>', s)
        return s

    def body(self, meta, blocks):
        P = []
        def p(style, txt):
            P.append('<text:p text:style-name="%s">%s</text:p>' % (style, txt))
        g = lambda k: meta.get(k, [''])[0]
        if 'title' in meta:
            p('TitleP', escape(g('title_ar')))
            p('Title', escape(g('title')))
            for s in meta.get('subtitle', []):
                p('Subtitle', escape(s))
            p('Gap', '')
            p('Author', escape(g('author')))
            for s in meta.get('extra', []):
                p('Extra', escape(s))
            for s in meta.get('source', []):
                p('Extra', escape(s))
            p('Gap', '')
            p('Label', 'অনুবাদ')
            p('Translator', escape(g('translator')))
            p('Gap', '')
            p('Publisher', escape(g('publisher')))
        first = 'title' not in meta
        for kind, txt, notes in blocks:
            if kind == 'h1':
                self.fn = 0
                p('ChapterFirst' if first else 'Chapter', self.inline(txt, notes))
                first = False
            elif kind == 'h2':
                p('Section', self.inline(txt, notes))
            elif kind == 'sub':
                p('SubHead', self.inline(txt, notes))
            elif kind == 'ar':
                p('Arabic', escape(txt))
            elif kind == 'center':
                p('Center', self.inline(txt, notes))
            elif kind == 'verse':
                p('Verse', self.inline(txt, notes))
            else:
                p('Text', self.inline(txt, notes))
        return '\n'.join(P)


def ps(name, parent='Standard', para='', text=''):
    return ('<style:style style:name="%s" style:family="paragraph" style:parent-style-name="%s">'
            '<style:paragraph-properties %s/><style:text-properties %s/></style:style>'
            % (name, parent, para, text))


def font(face, size, weight='normal', style='normal'):
    return ('style:font-name="{f}" fo:font-size="{s}pt" fo:font-weight="{w}" fo:font-style="{st}" '
            'style:font-name-complex="{f}" style:font-size-complex="{s}pt" '
            'style:font-weight-complex="{w}" style:font-style-complex="{st}" '
            'style:font-name-asian="{f}" style:font-size-asian="{s}pt"').format(f=face, s=size, w=weight, st=style)


def doc(body):
    BNL = 'fo:language="bn" fo:country="BD" style:language-complex="bn" style:country-complex="BD"'
    TB, HS, AM = 'Tiro Bangla', 'Hind Siliguri', 'Amiri'
    styles = [
        '<style:default-style style:family="paragraph"><style:paragraph-properties fo:hyphenation-ladder-count="no-limit" style:writing-mode="lr-tb"/>'
        '<style:text-properties %s %s/></style:default-style>' % (font(TB, 11), BNL),
        ps('Standard', 'Standard', '', font(TB, 11)).replace(' style:parent-style-name="Standard"', ''),
        ps('Text', 'Standard', 'fo:text-align="justify" fo:line-height="160%" fo:margin-top="0cm" fo:margin-bottom="0.18cm" fo:text-indent="0.6cm"', font(TB, 11)),
        ps('Chapter', 'Standard', 'fo:text-align="center" fo:break-before="page" fo:margin-top="0.6cm" fo:margin-bottom="0.6cm" fo:line-height="140%" fo:keep-with-next="always"', font(HS, 17, 'bold')),
        ps('Section', 'Standard', 'fo:text-align="center" fo:margin-top="0.45cm" fo:margin-bottom="0.3cm" fo:line-height="140%" fo:keep-with-next="always"', font(HS, 13.5, 'bold')),
        ps('SubHead', 'Standard', 'fo:text-align="start" fo:margin-top="0.3cm" fo:margin-bottom="0.12cm" fo:line-height="140%" fo:keep-with-next="always"', font(HS, 11.5, 'bold')),
        ps('Arabic', 'Standard', 'fo:text-align="center" style:writing-mode="rl-tb" fo:line-height="190%" fo:margin-top="0.15cm" fo:margin-bottom="0.05cm" fo:keep-with-next="always"',
           font(AM, 14.5) + ' style:language-complex="ar" style:country-complex="SA"'),
        ps('Center', 'Standard', 'fo:text-align="center" fo:line-height="155%" fo:margin-bottom="0.2cm"', font(TB, 11)),
        ps('Verse', 'Standard', 'fo:text-align="start" fo:margin-left="1.1cm" fo:line-height="150%" fo:margin-bottom="0.05cm"', font(TB, 11, style='italic')),
        ps('Footnote', 'Standard', 'fo:text-align="justify" fo:margin-left="0.45cm" fo:text-indent="-0.45cm" fo:line-height="125%" fo:margin-bottom="0.05cm"', font(TB, 8.5)),
        ps('Footer', 'Standard', 'fo:text-align="center"', font(TB, 9)),
        ps('TitleArabic', 'Standard', 'fo:text-align="center" style:writing-mode="rl-tb" fo:margin-top="1.2cm" fo:margin-bottom="0.5cm"', font(AM, 22, 'bold') + ' style:language-complex="ar"'),
        ps('TitleFirst', 'Standard', 'fo:margin-top="2cm"', font(TB, 11)),
        ps('Title', 'Standard', 'fo:text-align="center" fo:margin-bottom="0.3cm" fo:line-height="130%"', font(HS, 26, 'bold')),
        ps('Subtitle', 'Standard', 'fo:text-align="center" fo:margin-bottom="0.15cm" fo:line-height="140%"', font(HS, 13)),
        ps('Gap', 'Standard', 'fo:margin-top="0.9cm"', font(TB, 11)),
        ps('Author', 'Standard', 'fo:text-align="center" fo:line-height="140%"', font(HS, 15, 'bold')),
        ps('Extra', 'Standard', 'fo:text-align="center" fo:line-height="140%" fo:margin-top="0.1cm"', font(TB, 11)),
        ps('Label', 'Standard', 'fo:text-align="center"', font(TB, 11)),
        ps('Translator', 'Standard', 'fo:text-align="center" fo:line-height="140%"', font(HS, 14, 'bold')),
        ps('Publisher', 'Standard', 'fo:text-align="center"', font(HS, 13, 'bold')),
        '<text:notes-configuration text:note-class="footnote" style:num-format="1" text:start-value="0" text:footnotes-position="page" text:start-numbering-at="document"/>',
    ]
    auto = [
        '<style:style style:name="B" style:family="text"><style:text-properties fo:font-weight="bold" style:font-weight-complex="bold"/></style:style>',
        '<style:page-layout style:name="pm1"><style:page-layout-properties fo:page-width="14.8cm" fo:page-height="21cm" '
        'fo:margin-top="1.7cm" fo:margin-bottom="1.5cm" fo:margin-left="1.8cm" fo:margin-right="1.8cm" style:footnote-max-height="7cm">'
        '<style:footnote-sep style:width="0.02cm" style:distance-before-sep="0.1cm" style:distance-after-sep="0.1cm" style:adjustment="left" style:rel-width="30%" style:color="#000000"/>'
        '</style:page-layout-properties><style:footer-style><style:header-footer-properties fo:min-height="0.6cm" fo:margin-top="0.3cm"/></style:footer-style></style:page-layout>',
        '<style:page-layout style:name="pm2"><style:page-layout-properties fo:page-width="14.8cm" fo:page-height="21cm" '
        'fo:margin-top="1.2cm" fo:margin-bottom="1.2cm" fo:margin-left="1.8cm" fo:margin-right="1.8cm"/></style:page-layout>',
    ]
    auto.append('<style:style style:name="ChapterFirst" style:family="paragraph" style:parent-style-name="Chapter" style:master-page-name="Standard"/>')
    auto.append('<style:style style:name="TitleP" style:family="paragraph" style:parent-style-name="TitleArabic" style:master-page-name="First"/>')
    styles = [x.replace('<style:style style:name="Chapter" style:family="paragraph"',
                        '<style:style style:name="Chapter" style:family="paragraph" style:master-page-name="Standard"') for x in styles]
    masters = ('<style:master-page style:name="Standard" style:page-layout-name="pm1"><style:footer>'
               '<text:p text:style-name="Footer"><text:page-number text:select-page="current"/></text:p></style:footer></style:master-page>'
               '<style:master-page style:name="First" style:page-layout-name="pm2"/>')
    fonts = ''.join('<style:font-face style:name="%s" svg:font-family="\'%s\'"/>' % (f, f) for f in (TB, HS, AM))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
            'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
            'office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">'
            '<office:font-face-decls>%s</office:font-face-decls>'
            '<office:styles>%s</office:styles><office:automatic-styles>%s</office:automatic-styles>'
            '<office:master-styles>%s</office:master-styles>'
            '<office:body><office:text>%s</office:text></office:body></office:document>'
            % (fonts, ''.join(styles), ''.join(auto), masters, body))


def main():
    out, files = sys.argv[1], sys.argv[2:]
    meta, blocks = parse(files)
    xml = doc(Builder().body(meta, blocks))
    fodt = out + '.fodt'
    open(fodt, 'w', encoding='utf-8').write(xml)
    d = os.path.dirname(os.path.abspath(out))
    for fmt in ('pdf', 'docx:MS Word 2007 XML'):
        subprocess.run(['soffice', '--headless', '--convert-to', fmt, '--outdir', d, fodt],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('built', out + '.pdf', out + '.docx')


if __name__ == '__main__':
    main()
