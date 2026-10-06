"""Render this report's Markdown to a reading PDF with ReportLab (optional).

This deliberately small renderer supports the manuscript's headings, paragraphs,
table, numeric references and two displayed equations. It is not a TeX compiler
or a general Markdown converter. The editable paper.tex remains a separate source.
"""

import html
import os
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]


def inline(value):
    value = value.replace('\u2014', ' -- ').replace('\u2013', '-').replace('\u2011', '-')
    value = html.escape(value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)
    value = re.sub(r'`([^`]+)`', r'<font name="Courier" size="9">\1</font>', value)
    value = re.sub(r'\$([^$]+)\$', lambda m: '<i>' + re.sub(r'_([a-z])', r'<sub>\1</sub>', m[1]) + '</i>', value)
    value = re.sub(r'https://[^\s<]+', lambda m: '<link href="' + m[0] + '" color="#205870">' + m[0] + '</link>', value)
    return value


def render():
    font_candidates = [Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/timesi.ttf',
                       Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf'),
                       Path('/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf')]
    equation_font = next((p for p in font_candidates if p.is_file()), None)
    if equation_font is None:
        raise RuntimeError('The reading PDF needs an embeddable serif font with Greek glyphs; configure font_candidates for this platform.')
    pdfmetrics.registerFont(TTFont('EquationSymbols', str(equation_font)))
    text = (ROOT / 'research/paper.md').read_text(encoding='utf-8')
    metadata, body = text.split('---', 2)[1:]
    title = re.search(r'^title: "(.*)"$', metadata, re.M)[1]
    author = re.search(r'^author: "(.*)"$', metadata, re.M)[1]
    date = re.search(r'^date: "(.*)"$', metadata, re.M)[1]
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('PaperTitle', fontName='Times-Bold', fontSize=21, leading=25, alignment=TA_CENTER, spaceAfter=13))
    styles.add(ParagraphStyle('AuthorLine', fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_CENTER, spaceAfter=17))
    styles.add(ParagraphStyle('Body', fontName='Times-Roman', fontSize=10.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=8))
    styles.add(ParagraphStyle('Section', fontName='Times-Bold', fontSize=13, leading=16, spaceBefore=13, spaceAfter=7, keepWithNext=True))
    styles.add(ParagraphStyle('Subsection', fontName='Times-Bold', fontSize=11, leading=14, spaceBefore=9, spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle('Reference', fontName='Times-Roman', fontSize=9, leading=10.5, spaceAfter=3))
    styles.add(ParagraphStyle('Equation', fontName='Times-Italic', fontSize=12, leading=22, alignment=TA_CENTER, spaceAfter=7))
    styles.add(ParagraphStyle('Cell', fontName='Times-Roman', fontSize=9.5, leading=12))
    story = [Paragraph(inline(title), styles['PaperTitle']), Paragraph(inline(author + '<SEP>' + date).replace('&lt;SEP&gt;', '<br/>'), styles['AuthorLine'])]
    references = False
    lines = body.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('## '):
            heading = line[3:]
            references = heading == 'References'
            story.append(Paragraph(inline(heading), styles['Section']))
        elif line.startswith('### '):
            story.append(Paragraph(inline(line[4:]), styles['Subsection']))
        elif line.startswith('$$'):
            if 'L_{t+1}' in line:
                equation = 'L<sub>t+1</sub> = A(L<sub>t</sub>, C<sub>t</sub>, E).'
            elif '\\max_L' in line:
                equation = 'max<sub>L</sub> Q(L; E, D) - <font name="EquationSymbols">λ</font> C(L; E, D) - <font name="EquationSymbols">μ</font> K(L),'
            else:
                raise ValueError('Unrecognized equation; extend and visually verify the renderer')
            story.append(Paragraph(equation, styles['Equation']))
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', x) for x in cells):
                    rows.append([Paragraph(inline(x), styles['Cell']) for x in cells])
                i += 1
            table = Table(rows, colWidths=[139, 207, 105], repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E9F0F1')),
                                       ('LINEBELOW', (0,0), (-1,0), .6, colors.HexColor('#536D78')),
                                       ('LINEBELOW', (0,-1), (-1,-1), .4, colors.grey),
                                       ('VALIGN', (0,0), (-1,-1), 'TOP'),
                                       ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7)]))
            story.extend([table, Spacer(1,10)])
            continue
        else:
            paragraph = [line]
            while not references and i+1 < len(lines) and lines[i+1].strip() and not lines[i+1].startswith(('#', '|', '$$')):
                i += 1
                paragraph.append(lines[i].strip())
            story.append(Paragraph(inline(' '.join(paragraph)), styles['Reference' if references else 'Body']))
        i += 1

    def page_frame(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#53616A'))
        if doc.page > 1:
            canvas.drawString(72, A4[1]-40, 'Skill Loom | Systems technical report | v0.1')
        canvas.drawString(72, 35, '6 October 2026 | Not peer reviewed')
        canvas.drawRightString(A4[0]-72, 35, str(doc.page))
        canvas.restoreState()

    output = ROOT / 'research/paper.pdf'
    document = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=72, rightMargin=72,
                                 topMargin=61, bottomMargin=56, title=title, author=author)
    document.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    print(output)


if __name__ == '__main__':
    render()
