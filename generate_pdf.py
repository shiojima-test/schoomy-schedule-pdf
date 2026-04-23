#!/usr/bin/env python3
"""Generate SchooMy Festa annual schedule PDF (A4 landscape)."""
import argparse
import csv
import io
import os
import re
import sys
from datetime import datetime
from html import escape as h_escape

import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

CSV_URL = (
    'https://docs.google.com/spreadsheets/d/e/'
    '2PACX-1vRooWpJWGHr60e039XzbxEbeZ7p6zEL-wuP-xrq4jv1TnZXHSOWjtT8FvScuKsQn05aZx8PfIW14d83'
    '/pub?output=csv'
)
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
FONT_REGULAR = 'JP'
FONT_BOLD = 'JP-Bold'

COLOR_FESTA = colors.HexColor('#E88A0A')
COLOR_SESSION = colors.HexColor('#3AABA8')
COLOR_HEADER = colors.HexColor('#333333')
COLOR_STRIPE = colors.HexColor('#F5F5F5')
COLOR_WHITE = colors.white
COLOR_TEXT = colors.HexColor('#1a1a22')
COLOR_GRAY_SMALL = '#999999'
COLOR_SUB = colors.HexColor('#666666')
COLOR_GRID = colors.HexColor('#CCCCCC')

HEADERS_HTML = ['種別', '開催日<br/>（大会当日）', 'イベント名', '開催地', '主催', 'エントリー開始', '予選通過者発表']
COL_WIDTHS_MM = [19, 28, 100, 22, 37, 36, 40]


def parse_date(s):
    s = (s or '').strip()
    if not s:
        return None
    try:
        return datetime.strptime(s.replace('-', '/'), '%Y/%m/%d')
    except ValueError:
        return None


def sort_key(row):
    d = parse_date(row.get('date_start'))
    if d:
        return d
    try:
        y = int(row.get('year') or 9999)
        m = int(row.get('month') or 1)
        return datetime(y, m, 1)
    except (ValueError, TypeError):
        return datetime(9999, 1, 1)


def fmt_date_cell(row):
    dt = (row.get('date_text') or '').strip()
    if dt:
        return dt
    ds = parse_date(row.get('date_start'))
    de = parse_date(row.get('date_end'))
    if ds and de:
        if ds.year == de.year and ds.month == de.month:
            return f'{ds.year}/{ds.month:02d}/{ds.day:02d}〜{de.day:02d}'
        return f'{ds.year}/{ds.month:02d}/{ds.day:02d}〜{de.year}/{de.month:02d}/{de.day:02d}'
    if ds:
        return f'{ds.year}/{ds.month:02d}/{ds.day:02d}'
    return ''


def normalize_dates_inline(s):
    return re.sub(r'(\d{4})-(\d{2})-(\d{2})', r'\1/\2/\3', s)


def fmt_entry_start(row):
    v = (row.get('entry_start') or '').strip()
    return normalize_dates_inline(v) if v else ''


def fmt_entry_result(row):
    lines = []
    for k in ('entry_result_1', 'entry_result_2'):
        v = (row.get(k) or '').strip()
        if v:
            lines.append(normalize_dates_inline(v))
    return '\n'.join(lines)


def build_document(args, rows):
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, os.path.join(FONT_DIR, 'NotoSansJP-Regular.ttf')))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, os.path.join(FONT_DIR, 'NotoSansJP-Bold.ttf')))
    pdfmetrics.registerFontFamily(FONT_REGULAR, normal=FONT_REGULAR, bold=FONT_BOLD,
                                  italic=FONT_REGULAR, boldItalic=FONT_BOLD)

    st_title = ParagraphStyle('title', fontName=FONT_BOLD, fontSize=16, leading=20,
                              textColor=COLOR_TEXT)
    st_subtitle = ParagraphStyle('sub', fontName=FONT_REGULAR, fontSize=9, leading=12,
                                 textColor=COLOR_SUB)
    st_legend = ParagraphStyle('leg', fontName=FONT_REGULAR, fontSize=9, leading=11,
                               textColor=COLOR_TEXT)
    st_legend_badge = ParagraphStyle('leg_badge', fontName=FONT_BOLD, fontSize=9, leading=11,
                                     textColor=colors.white, alignment=1)
    st_cell = ParagraphStyle('cell', fontName=FONT_REGULAR, fontSize=9, leading=11.5,
                             textColor=COLOR_TEXT, wordWrap='CJK')
    st_type = ParagraphStyle('type', fontName=FONT_BOLD, fontSize=9, leading=11,
                             textColor=colors.white, alignment=1)
    st_header = ParagraphStyle('hdr', fontName=FONT_BOLD, fontSize=9, leading=11,
                               textColor=colors.white, alignment=1)
    st_footer = ParagraphStyle('ft', fontName=FONT_REGULAR, fontSize=8, leading=10,
                               textColor=COLOR_SUB)

    doc = SimpleDocTemplate(
        args.output, pagesize=landscape(A4),
        leftMargin=5*mm, rightMargin=5*mm, topMargin=5*mm, bottomMargin=5*mm,
        title='スクーミーフェスタ年間スケジュール 2026年度',
    )

    story = []
    story.append(Paragraph('スクーミーフェスタ年間スケジュール 2026年度', st_title))
    story.append(Spacer(1, 1*mm))
    y, m, d = args.update_date.split('-')
    story.append(Paragraph(
        f'v{args.version} / {y}年{int(m)}月{int(d)}日 更新 / 株式会社スクーミー',
        st_subtitle
    ))
    story.append(Spacer(1, 3*mm))

    legend_data = [[
        Paragraph('フェスタ', st_legend_badge),
        Paragraph('全国大会・競技大会', st_legend),
        Paragraph('説明会', st_legend_badge),
        Paragraph('大会に向けた説明会・交流会', st_legend),
    ]]
    legend = Table(legend_data, colWidths=[22*mm, 60*mm, 22*mm, 60*mm])
    legend.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), COLOR_FESTA),
        ('BACKGROUND', (2, 0), (2, 0), COLOR_SESSION),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(legend)
    story.append(Spacer(1, 3*mm))

    def build_type_cell(t):
        label = 'フェスタ' if t == 'festa' else '説明会'
        return Paragraph(label, st_type)

    def build_date_cell(row):
        dv = fmt_date_cell(row)
        time_v = (row.get('time') or '').strip()
        parts = []
        if dv:
            parts.append(h_escape(dv, quote=False))
        if time_v:
            parts.append(f'<font size="7" color="{COLOR_GRAY_SMALL}">{h_escape(time_v, quote=False)}</font>')
        return Paragraph('<br/>'.join(parts) if parts else '—', st_cell)

    def build_event_cell(row):
        title_html = h_escape(row.get('title', '') or '', quote=False)
        if (row.get('type') or '').strip() == 'session':
            target = (row.get('target') or '').strip()
            if target:
                lines = [l.strip() for l in target.split('\n') if l.strip()]
                processed = []
                for ln in lines:
                    if not ln.endswith('について'):
                        ln = ln + 'について'
                    processed.append(h_escape(ln, quote=False))
                target_html = '<br/>'.join(processed)
                html_ = f'{title_html}<br/><font size="6.5" color="{COLOR_GRAY_SMALL}">{target_html}</font>'
            else:
                html_ = title_html
        else:
            html_ = title_html
        return Paragraph(html_ or '—', st_cell)

    def build_simple_cell(text):
        text = (text or '').strip()
        return Paragraph(h_escape(text, quote=False) if text else '—', st_cell)

    def build_multiline_cell(text):
        if not text:
            return Paragraph('—', st_cell)
        parts = [h_escape(l, quote=False) for l in text.split('\n')]
        return Paragraph('<br/>'.join(parts), st_cell)

    header_row = [Paragraph(h, st_header) for h in HEADERS_HTML]
    table_data = [header_row]

    for row in rows:
        t = (row.get('type') or '').strip()
        table_data.append([
            build_type_cell(t),
            build_date_cell(row),
            build_event_cell(row),
            build_simple_cell(row.get('location')),
            build_simple_cell(row.get('host')),
            build_simple_cell(fmt_entry_start(row)),
            build_multiline_cell(fmt_entry_result(row)),
        ])

    tbl = Table(table_data, colWidths=[w*mm for w in COL_WIDTHS_MM], repeatRows=1)

    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
        ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.3, COLOR_GRID),
    ]
    for i, row in enumerate(rows, start=1):
        t = (row.get('type') or '').strip()
        style_cmds.append(('BACKGROUND', (0, i), (0, i),
                           COLOR_FESTA if t == 'festa' else COLOR_SESSION))
        stripe = COLOR_STRIPE if (i % 2 == 1) else COLOR_WHITE
        style_cmds.append(('BACKGROUND', (1, i), (-1, i), stripe))

    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        '※日付・会場等は変更になる場合があります。最新情報は '
        '<a href="https://fox.schoomy.com/" color="#2E8EC4">https://fox.schoomy.com/</a> '
        'をご確認ください。',
        st_footer
    ))

    doc.build(story)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--version', type=int, required=True)
    p.add_argument('--update-date', required=True, help='YYYY-MM-DD')
    p.add_argument('--output', required=True)
    args = p.parse_args()

    r = requests.get(CSV_URL, timeout=30)
    r.raise_for_status()
    text = r.content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))
    rows = [row for row in reader]

    rows = [
        row for row in rows
        if (row.get('is_published') or '').strip().upper() == 'TRUE'
        and (row.get('type') or '').strip() in ('festa', 'session')
    ]
    rows.sort(key=sort_key)

    if not rows:
        print('ERROR: no rows to render', file=sys.stderr)
        sys.exit(1)

    build_document(args, rows)
    print(f'Generated: {args.output} ({len(rows)} rows)')


if __name__ == '__main__':
    main()
