#!/usr/bin/env python3
"""Invisible characters and escapes.

Claims tested (section 9 of the resource):
  E2  An invisible format character inside a Hebrew word (RLM, LRM, ZWJ, ZWNJ, soft hyphen, word joiner, BOM)
      leaves the word looking whole and makes it unmatchable as typed. Only a scan by category shows them.
  E3  U+2028 and U+2029 are valid inside JSON strings, and JSON.stringify leaves them raw — but Node's readline
      ends a line at them, so a JSON-lines stream is cut in the middle of a record (see 08_invisible.mjs).
  E4  Hebrew stored as backslash-u escape TEXT (Python's json.dumps default) contains no Hebrew letter at all:
      every Hebrew search over the file finds nothing.
  E5  One NUL byte makes grep treat a text file as binary (see 09_shell.sh).
  E1  An AI agent's tool parameters can decode a typed backslash-u escape before the tool runs: the claim is
      about the agent's harness, so it is recorded from our measurements, not reproduced here (see the text).
Run: python3 08_invisible.py
"""
import json, os, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check, cp, done

INVISIBLE = [0x200F, 0x200E, 0x200D, 0x200C, 0x00AD, 0x2060, 0xFEFF, 0x2067, 0x2069]
word = 'שלום'
for c in INVISIBLE:
    w = word[:2] + chr(c) + word[2:]
    found = word in w
    print(f'  "{word}" with {cp(chr(c)):42s} inside: category {unicodedata.category(chr(c))}, the plain word found in it: {found}')
check('E2', 'none of the nine variants contains the plain word', any(word in (word[:2] + chr(c) + word[2:]) for c in INVISIBLE), False)
check('E2', 'all nine are category Cf (format), except none', sorted({unicodedata.category(chr(c)) for c in INVISIBLE}), ['Cf'])

def scan(text):
    """Report every format character (category Cf) and every control character except tab and newline."""
    out = []
    for i, ch in enumerate(text):
        cat = unicodedata.category(ch)
        if cat == 'Cf' or (cat == 'Cc' and ch not in '\t\n'):
            out.append((i, f'U+{ord(ch):04X}'))
    return out
sample = 'שלום' + chr(0x200F) + ' עולם' + chr(0xFEFF) + '\n'
check('E2', 'a category scan finds both hidden characters', scan(sample), [(4, 'U+200F'), (10, 'U+FEFF')])
check('E2', 'removing category Cf restores the plain words', ''.join(c for c in sample if unicodedata.category(c) != 'Cf'), 'שלום עולם\n')

# E4 — Hebrew as escape text
rec = {'text': 'שלום עולם'}
default = json.dumps(rec)
readable = json.dumps(rec, ensure_ascii=False)
print('\n  json.dumps default:            ', default)
print('  json.dumps(ensure_ascii=False):', readable)
check('E4', 'the default output holds no Hebrew letter', any(0x5D0 <= ord(c) <= 0x5EA for c in default), False)
check('E4', 'a search for the word in the default output', 'שלום' in default, False)
check('E4', 'both decode to the same record', json.loads(default) == json.loads(readable), True)

# E3 — the line separators, from the JSON side (the readline side is in 08_invisible.mjs)
ls = {'text': 'a' + chr(0x2028) + 'b'}
check('E3', 'Python json.dumps escapes U+2028 by default (ensure_ascii)', chr(0x2028) in json.dumps(ls), False)
check('E3', 'with ensure_ascii=False it is written raw', chr(0x2028) in json.dumps(ls, ensure_ascii=False), True)
check('E3', 'str.splitlines() splits at U+2028 too', len(('x' + chr(0x2028) + 'y').splitlines()), 2)
done()
