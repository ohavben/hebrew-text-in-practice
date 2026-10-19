#!/usr/bin/env python3
"""Build the browser test pages and (if chromium is installed) screenshot them.

  python3 make_pages.py            -> bidi.html, fonts.html, blocks.html (+ .png screenshots with chromium)

The pages are the second method for the bidi claims of 06_bidi.py (a browser's implementation of the same
algorithm) and the first for the rendering claims: per-block direction, isolates, and fonts for te'amim.
Every control character is written as an HTML entity (&#x2067;), never as a raw character.
"""
import html, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), 'data', 'verses.json')
V = {v['ref']: v for v in json.load(open(DATA, encoding='utf-8'))['verses']}

HEAD = '''<!doctype html><html{lang}><head><meta charset="utf-8"><title>{title}</title><style>
 body {{ font: 20px/1.6 "Noto Sans Hebrew", sans-serif; margin: 16px; background: #fff; color: #111; }}
 .row {{ display: grid; grid-template-columns: 340px 1fr; gap: 12px; border-bottom: 1px solid #ccc; padding: 6px 0; }}
 .label {{ font: 14px/1.4 "DejaVu Sans", sans-serif; color: #444; direction: ltr; text-align: left; }}
 .box {{ border: 1px dashed #999; padding: 2px 8px; }}
</style></head><body>
'''

def row(label, content, d=None):
    attr = f' dir="{d}"' if d else ''
    return f'<div class="row"><div class="label">{html.escape(label)}</div><div class="box"{attr}>{content}</div></div>\n'

def bidi_page():
    rows = [
        ('B1 rtl: שלום world!', 'שלום world!', 'rtl'),
        ('B1 rtl: … world! + &lrm;', 'שלום world!&lrm;', 'rtl'),
        ('B1 rtl: אני כותב C++', 'אני כותב C++', 'rtl'),
        ('B1 rtl: … <bdi>C++</bdi>', 'אני כותב <bdi>C++</bdi>', 'rtl'),
        ('B1 rtl: חום -5 מעלות', 'חום -5 מעלות', 'rtl'),
        ('B1 rtl: … <bdi dir=ltr>-5</bdi>', 'חום <bdi dir="ltr">-5</bdi> מעלות', 'rtl'),
        ('B2 ltr: /data/תיקיה/מסמכים/a.txt', '/data/תיקיה/מסמכים/a.txt', 'ltr'),
        ('ISO ltr: see RLE…PDF, 5', 'see &#x202B;שלום&#x202C;, 5', 'ltr'),
        ('ISO ltr: see <bdi>…</bdi>, 5', 'see <bdi>שלום</bdi>, 5', 'ltr'),
        ('B6 rtl: (שלום) [עולם]', '(שלום) [עולם]', 'rtl'),
    ]
    return HEAD.format(title='bidi', lang=' lang="he"') + ''.join(row(a, b, d) for a, b, d in rows) + '</body></html>\n'

def blocks_page():
    he = 'זה משפט בעברית.'
    en = 'This is an English sentence.'
    rows = [
        ('B4 one element, no dir (inherits ltr)', f'{he} {en}', None),
        ('B4 one element, dir=rtl', f'{he} {en}', 'rtl'),
        ('B4 one element, dir=auto (first strong = English)', f'{en} {he}', 'auto'),
        ('B4 two blocks, dir=auto each', f'<div dir="auto">{he}</div><div dir="auto">{en}</div>', None),
        ('B4 one element, unicode-bidi: plaintext, two lines', f'<div style="unicode-bidi: plaintext; white-space: pre-line">{he}\n{en}</div>', None),
        ('B5 raw Markdown in rtl: **שָׁלוֹם** עוֹלָם', '**שָׁלוֹם** עוֹלָם', 'rtl'),
        ('B5 raw Markdown in rtl: עוֹלָם **שָׁלוֹם**', 'עוֹלָם **שָׁלוֹם**', 'rtl'),
    ]
    return HEAD.format(title='blocks', lang=' lang="he"') + ''.join(row(a, b, d) for a, b, d in rows) + '</body></html>\n'

def fonts_page(lang):
    verse = V['Gen 2:25']['text']                     # nikud + te'amim + meteg; no Name
    fams = ['Arial', 'DejaVu Sans', 'Times New Roman', 'Noto Sans Hebrew', 'Noto Serif Hebrew', 'Ezra SIL',
            'Keter YG', 'Liberation Mono', 'monospace']
    out = HEAD.format(title='fonts', lang=lang)
    for f in fams:
        out += row(f'font-family: {f}', f'<span style="font-family: {f}; font-size: 28px">{html.escape(verse)}</span>', 'rtl')
    return out + '</body></html>\n'

def screenshot(name, height):
    exe = shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')
    if not exe:
        print('no chromium: open the .html files in a browser instead'); return
    src, png = os.path.join(HERE, name + '.html'), os.path.join(HERE, name + '.png')
    cmd = [exe, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size=1100,{height}',
           f'--screenshot={png}', 'file://' + src]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print(name, '->', png if os.path.exists(png) else 'NO SCREENSHOT', '(exit', r.returncode, ')')

for name, build, h in (('bidi', bidi_page, 620), ('blocks', blocks_page, 520),
                       ('fonts_lang_he', lambda: fonts_page(' lang="he"'), 820), ('fonts_no_lang', lambda: fonts_page(''), 820)):
    open(os.path.join(HERE, name + '.html'), 'w', encoding='utf-8').write(build())
    screenshot(name, h)
