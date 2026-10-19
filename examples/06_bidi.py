#!/usr/bin/env python3
"""The bidi algorithm in practice, measured with GNU FriBidi (the Unicode Bidirectional Algorithm, UAX #9).

A visual-order string cannot be shown honestly in a viewer that runs the bidi algorithm itself (it would be
reordered a second time). So every VISUAL line below is printed in ASCII: Hebrew letters as capitals
(see TRANSLIT), combining marks as `, and the line reads left to right exactly as the screen would show it.

Claims tested (section 6 of the resource):
  B0  The paragraph direction comes from the first strong character, unless it is set.
  B1  A neutral at the edge of a Latin run inside a right-to-left paragraph lands on the far side: "world!"
      shows as "!world" and "C++" as "++C"; a left-to-right mark (LRM) after the run, or an isolate, fixes it.
  B1  A number with a minus sign inside right-to-left text shows the sign on the other side ("5-");
      an LRI ... PDI isolate keeps "-5".
  B2  Two Hebrew segments of a left-to-right path form one right-to-left run, so they show in swapped order.
  B6  Brackets are mirrored: inside a right-to-left run the stored "(" is drawn as ")".
  NSM In visual order a combining mark comes BEFORE its letter unless the renderer reorders it (rule L3);
      a program that writes visual-order text without L3 hands its marks to the wrong letters.
  ISO An embedding (LRE/RLE ... PDF) lets the following neutrals and numbers join the embedded run; an
      isolate (LRI/RLI/FSI ... PDI) keeps them in the outer text.
Run: python3 06_bidi.py      (needs the fribidi command: GNU FriBidi)
"""
import os, shutil, subprocess, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check, done

if not shutil.which('fribidi'):
    sys.exit('this example needs GNU FriBidi (the fribidi command)')

LRM, RLM = chr(0x200E), chr(0x200F)
LRI, RLI, FSI, PDI = chr(0x2066), chr(0x2067), chr(0x2068), chr(0x2069)
LRE, PDF = chr(0x202A), chr(0x202C)
TRANSLIT = dict(zip('אבגדהוזחטיכךלמםנןסעפףצץקרשת', 'ABGDHVZXTYKKLMMNNSOPPCCQRWJ'))

def visual(s, base=None, extra=()):
    args = ['fribidi', '--nopad', '--nobreak', '--clean'] + ([f'--{base}'] if base else []) + list(extra)
    out = subprocess.run(args, input=s, capture_output=True, text=True, check=True).stdout
    return out.rstrip('\n')

def basedir(s):
    out = subprocess.run(['fribidi', '--basedir', '--novisual'], input=s, capture_output=True, text=True, check=True).stdout
    return out.split()[-1]

def ascii_line(s):
    return ''.join(TRANSLIT.get(ch, '`' if unicodedata.category(ch) == 'Mn' else ch) for ch in s)

def show(label, logical, base=None, extra=()):
    v = visual(logical, base, extra)
    printable = ''.join(f'<{unicodedata.name(c).split()[-1]}>' if unicodedata.category(c) == 'Cf' else c for c in logical)
    print(f'  {label}\n     logical: {ascii_line(printable)}\n     visual:  {ascii_line(v)}')
    return ascii_line(v)

print(subprocess.run(['fribidi', '--version'], capture_output=True, text=True).stdout.splitlines()[0])

# B0 — the paragraph direction
check('B0', 'a line that starts with Hebrew', basedir('שלום world'), 'R')
check('B0', 'a line that starts with Latin', basedir('note: שלום'), 'L')
check('B0', 'a line that starts with a digit, then Hebrew (a digit is weak)', basedir('3 ספרים'), 'R')

# B1 — neutrals at the edge of a Latin run
v = show('"world!" at the end of an RTL line', 'שלום world!', 'rtl')
check('B1', 'the "!" shows at the far left, before "world"', v.startswith('!world'), True)
v = show('the same with an LRM after the "!"', 'שלום world!' + LRM, 'rtl')
check('B1', 'with an LRM the "!" stays after "world"', v.startswith('world!'), True)
v = show('"C++" at the end of an RTL line', 'אני כותב C++', 'rtl')
check('B1', '"C++" shows as "++C"', v.startswith('++C'), True)
v = show('"C++" in an FSI ... PDI isolate', 'אני כותב ' + FSI + 'C++' + PDI, 'rtl')
check('B1', 'isolated, it shows as "C++"', v.startswith('C++'), True)

# B1 — a negative number
v = show('a negative number in RTL text', 'חום -5 מעלות', 'rtl')
check('B1', 'the minus sign shows on the right of the 5', '5-' in v, True)
v = show('the number in an LRI ... PDI isolate', 'חום ' + LRI + '-5' + PDI + ' מעלות', 'rtl')
check('B1', 'isolated, it shows as "-5"', '-5' in v, True)

# B2 — a path with two Hebrew segments
v = show('an LTR path with two Hebrew folders', '/data/תיקיה/מסמכים/a.txt', 'ltr')
first, second = ascii_line('תיקיה'), ascii_line('מסמכים')
check('B2', 'the second folder shows before the first', v.find(second[::-1]) < v.find(first[::-1]), True)

# B6 — mirrored brackets
mirrored = visual('(שלום)', 'rtl')
plain = visual('(שלום)', 'rtl', ['--nomirror'])
print(f'  "(שלום)" in RTL: with mirroring {ascii_line(mirrored)} · without {ascii_line(plain)}')
check('B6', 'with mirroring the visual line starts with "(" (the stored ")" drawn mirrored)', ascii_line(mirrored), '(MVLW)')
check('B6', 'without mirroring the stored characters would face the wrong way', ascii_line(plain), ')MVLW(')

# NSM — marks in visual order
w = 'שָׁלוֹם'
no_l3 = visual(w, 'rtl')
l3 = visual(w, 'rtl', ['--reordernsm'])
HOLAM, VAV = chr(0x5B9), chr(0x5D5)
check('NSM', 'without L3 the holam stands BEFORE its vav (a left-to-right viewer puts it on the letter before)', no_l3.index(HOLAM) < no_l3.index(VAV), True)
print('  visual, no L3:  ', ' '.join(f'{ord(c):04X}' for c in no_l3))
print('  visual, with L3:', ' '.join(f'{ord(c):04X}' for c in l3))
check('NSM', 'with L3 the holam follows its vav', l3.index(HOLAM) > l3.index(VAV), True)
check('NSM', 'the two orders differ', no_l3 == l3, False)

# Embedding vs isolate: a Hebrew name inside an English line, followed by ", 5"
RLE = chr(0x202B)
emb = show('RLE ... PDF around a Hebrew word in an LTR line', 'see ' + RLE + 'שלום' + PDF + ', 5', 'ltr')
iso = show('RLI ... PDI around the same word', 'see ' + RLI + 'שלום' + PDI + ', 5', 'ltr')
check('ISO', 'the embedding pulls ", 5" into the Hebrew run', emb, 'see 5 ,MVLW')
check('ISO', 'the isolate keeps it outside', iso, 'see MVLW, 5')
done()
