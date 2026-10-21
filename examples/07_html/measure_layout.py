#!/usr/bin/env python3
"""Two implementations of the bidi algorithm, compared on the same strings: GNU FriBidi and a browser (Chromium).

For each case the page lays the string out in a block with the given dir; a script asks the browser where each
character was drawn (Range.getBoundingClientRect) and writes the order of their x positions into the page; the
page is read back with chromium --dump-dom. FriBidi's side is the same string's stored characters in the order of
fribidi --vtol, its visual-to-logical map (positions are of the STORED characters, so mirroring is part of neither
side; --nomirror would do the same, but the fribidi command ignores it before version 1.0.17). The two visual
orders must agree. Letters are printed as ASCII capitals (as in 06_bidi.py) so that no viewer reorders the result
again.
  ISO  <bdi> and elements with a dir attribute are isolates in the browser's style sheet; a plain span is not.
  X    the browser and FriBidi put the characters of each test line in the same visual order.
Run: python3 measure_layout.py      (needs chromium and fribidi)
"""
import html, json, os, re, shutil, subprocess, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from _common import check, done

LRM = chr(0x200E)
LRI, RLI, FSI, PDI, RLE, PDF = chr(0x2066), chr(0x2067), chr(0x2068), chr(0x2069), chr(0x202B), chr(0x202C)
TRANSLIT = dict(zip('אבגדהוזחטיכךלמםנןסעפףצץקרשת', 'ABGDHVZXTYKKLMMNNSOPPCCQRWJ'))
CASES = [
    ('rtl', 'שלום world!'), ('rtl', 'שלום world!' + LRM), ('rtl', 'אני כותב C++'),
    ('rtl', 'אני כותב ' + FSI + 'C++' + PDI), ('rtl', 'חום -5 מעלות'), ('rtl', 'חום ' + LRI + '-5' + PDI + ' מעלות'),
    ('ltr', '/data/תיקיה/מסמכים/a.txt'), ('ltr', 'see ' + RLE + 'שלום' + PDF + ', 5'),
    ('ltr', 'see ' + RLI + 'שלום' + PDI + ', 5'), ('rtl', '(שלום) [עולם]'),
    # raw Markdown emphasis in a left-to-right editor line, unpointed and pointed (does the pointing change it?)
    ('ltr', '**שלום** עולם'), ('ltr', '**שָׁלוֹם** עוֹלָם'), ('ltr', 'עולם **שלום**'), ('ltr', 'עוֹלָם **שָׁלוֹם**'),
    ('ltr', 'see **שלום** here'), ('ltr', 'see **שָׁלוֹם** here'),
]

def entity(s):          # every non-ASCII character as an entity: the file holds no raw control character
    return ''.join(c if ord(c) < 128 else f'&#x{ord(c):X};' for c in html.escape(s, quote=False))

def visible(c):
    return unicodedata.category(c) not in ('Cf', 'Mn') and c != ' '

def page():
    rows = ''.join(f'<div class="t" dir="{d}">{entity(s)}</div>\n' for d, s in CASES)
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
 body {{ font: 24px "Noto Sans Hebrew", sans-serif; }} .t {{ width: 700px; white-space: pre; margin: 8px; }}</style></head>
<body>{rows}<p><bdi id="cb">x</bdi> <span id="cl" dir="ltr">y</span> <span id="ca" dir="auto">z</span> <span id="cn">w</span></p>
<pre id="out"></pre><pre id="css"></pre><script>
document.getElementById('css').textContent = 'CSS' + JSON.stringify(['cb', 'cl', 'ca', 'cn'].map(i => getComputedStyle(document.getElementById(i)).unicodeBidi)) + 'END';
const res = [];
for (const div of document.querySelectorAll('.t')) {{
  const node = div.firstChild, s = node.data, pos = [];
  for (let i = 0; i < s.length; i++) {{
    const r = document.createRange(); r.setStart(node, i); r.setEnd(node, i + 1);
    const b = r.getBoundingClientRect();
    pos.push([i, b.width > 0 ? b.left : null]);
  }}
  res.push(pos);
}}
document.getElementById('out').textContent = 'RESULT' + JSON.stringify(res) + 'END';
</script></body></html>'''

exe = shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')
if not exe or not shutil.which('fribidi'):
    sys.exit('needs chromium and fribidi')
src = os.path.join(HERE, 'measure.html')
with open(src, 'w', encoding='utf-8') as f:
    f.write(page())
run = subprocess.run([exe, '--headless=new', '--disable-gpu', '--dump-dom', 'file://' + src],
                     capture_output=True, text=True, timeout=120)
dom = run.stdout
found = re.search(r'RESULT(.*?)END', dom, re.S)
if not found:           # the browser did not run the page: say so, with what it said, instead of a traceback
    said = run.stderr.strip().splitlines()[-3:]
    if any('sandbox' in line for line in said):
        why = "its sandbox could not start (as root, or in a container); Chromium starts there only with --no-sandbox"
    elif any('Socket path too long' in line for line in said):
        why = 'the path of its socket was too long; set TMPDIR to a short directory'
    else:
        why = 'its last lines are below'
    sys.exit(f'{exe} did not lay out the page (exit status {run.returncode}): {why}\n' + '\n'.join('    ' + l for l in said))
data = json.loads(found.group(1))
print(subprocess.run([exe, '--version'], capture_output=True, text=True).stdout.strip(), '·',
      subprocess.run(['fribidi', '--version'], capture_output=True, text=True).stdout.splitlines()[0])

css = json.loads(re.search(r'CSS(.*?)END', dom, re.S).group(1))
print('  computed unicode-bidi: <bdi> %s · <span dir=ltr> %s · <span dir=auto> %s · <span> %s' % tuple(css))
check('ISO', '<bdi> and elements with a dir attribute are isolates; a plain span is not', css, ['isolate', 'isolate', 'isolate', 'normal'])
for (d, s), pos in zip(CASES, data):
    shown = [(x, i) for i, x in pos if x is not None and visible(s[i])]
    browser = ''.join(TRANSLIT.get(s[i], s[i]) for x, i in sorted(shown))
    vtol = subprocess.run(['fribidi', '--nopad', '--nobreak', '--novisual', '--vtol', f'--{d}'],
                          input=s, capture_output=True, text=True, check=True).stdout.split()
    fribidi = ''.join(TRANSLIT.get(s[int(i)], s[int(i)]) for i in vtol if visible(s[int(i)]))
    label = ''.join(f'<{unicodedata.name(c).split()[-1]}>' if unicodedata.category(c) == 'Cf' else TRANSLIT.get(c, c) for c in s)
    print(f'  {d}  {label}\n       browser: {browser}\n       fribidi: {fribidi}')
    check('X', f'browser and FriBidi agree on {label}', browser, fribidi)
done()
