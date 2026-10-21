#!/usr/bin/env python3
"""The layers of a pointed Hebrew string, and the one-range trap.

Claims tested (section 1 of the resource):
  U1  The block U+0591..U+05C7 is not "all the marks": four of its code points are punctuation that separates
      words (maqaf, paseq, sof pasuq, nun hafukha). One regex range over the block deletes them, and the words a
      maqaf joins fuse into one.
  U3  The extraordinary dots (U+05C4) are combining marks inside the same range: a mark strip removes them too.
  U6  One code point, U+05BC, is dagesh, mappiq and shuruk: its function depends on the letter it sits on.
  U2  U+05C0 is one code point for two signs: the paseq, and the stroke of the accent legarmeh.
  U4  Some layers have no Unicode at all: no character name mentions the tagin, the crowns of a Torah scroll.
Run: python3 01_layers.py
"""
import os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import verses, check, cp, show, done

V = verses()
LO, HI = 0x0591, 0x05C7
block = [chr(c) for c in range(LO, HI + 1)]

# --- the general categories inside the block --------------------------------------------------------------
cats = {}
for ch in block:
    cats.setdefault(unicodedata.category(ch), []).append(ch)
print('categories in U+0591..U+05C7:', {k: len(v) for k, v in sorted(cats.items())})
not_marks = [ch for ch in block if not unicodedata.category(ch).startswith('M')]
for ch in not_marks:
    print('   not a mark:', cp(ch), '-', unicodedata.category(ch))
check('U1', 'code points in the block · of them combining marks (category Mn)', (len(block), len(cats.get('Mn', []))), (55, 51))
check('U1', 'code points in the block that are NOT combining marks', [f'{ord(c):04X}' for c in not_marks],
      ['05BE', '05C0', '05C3', '05C6'])

# --- the one-range strip, and the right strip ----------------------------------------------------------------
one_range = re.compile('[' + chr(LO) + '-' + chr(HI) + ']')          # what is often written to "strip the points"
def strip_marks(s):                                                   # remove combining marks only (category M*)
    return ''.join(ch for ch in s if not unicodedata.category(ch).startswith('M'))
def words(s):                                                         # words: split on spaces AND on the maqaf
    return [w for w in re.split('[ ' + chr(0x5BE) + ']+', s) if w]

g26 = V['Gen 2:6']['text']
print('\nGen 2:6, as stored:      ', show(g26))
print('one-range strip:         ', one_range.sub('', g26))
print('mark strip (category M): ', strip_marks(g26))
check('U1', 'Gen 2:6 words before stripping', len(words(g26)), 9)
check('U1', 'Gen 2:6 words after the one-range strip (maqaf deleted, words fused)', len(words(one_range.sub('', g26))), 5)
check('U1', 'Gen 2:6 words after the mark strip', len(words(strip_marks(g26))), 9)
check('U1', 'the sof pasuq survives the mark strip', strip_marks(g26).endswith(chr(0x5C3)), True)
check('U1', 'the sof pasuq survives the one-range strip', one_range.sub('', g26).endswith(chr(0x5C3)), False)

g1815 = V['Gen 18:15']['text']
check('U1', 'Gen 18:15: strokes U+05C0 kept by the mark strip', strip_marks(g1815).count(chr(0x5C0)), 3)
check('U1', 'Gen 18:15: strokes U+05C0 kept by the one-range strip', one_range.sub('', g1815).count(chr(0x5C0)), 0)

# --- U3: the extraordinary dots are marks ----------------------------------------------------------------------
g189 = V['Gen 18:9']['text']
dotted = [w for w in g189.split() if chr(0x5C4) in w][0]
print('\nGen 18:9, the dotted word:', show(dotted))
check('U3', 'U+05C4 is a combining mark', unicodedata.category(chr(0x5C4)), 'Mn')
check('U3', 'dots in Gen 18:9 before / after the mark strip', (g189.count(chr(0x5C4)), strip_marks(g189).count(chr(0x5C4))), (4, 0))

# --- U6: one point, three functions ---------------------------------------------------------------------------
DOT = chr(0x5BC)
roles = {}
for v in V.values():
    for w in v['text'].replace(chr(0x5BE), ' ').split():
        for i, ch in enumerate(w):
            if ch != DOT:
                continue
            j = i - 1
            while j >= 0 and not (0x5D0 <= ord(w[j]) <= 0x5EA):
                j -= 1
            base = w[j] if j >= 0 else '?'
            has_vowel = any(0x5B0 <= ord(c) <= 0x5BB for c in w[j + 1:i] + w[i + 1:i + 3])
            last_letter = all(not (0x5D0 <= ord(c) <= 0x5EA) for c in w[i + 1:])
            if base == chr(0x5D5) and not has_vowel:
                role = 'shuruk (on vav, no other vowel)'
            elif base == chr(0x5D4) and last_letter:
                role = 'mappiq (on a final he)'
            else:
                role = 'dagesh'
            roles[role] = roles.get(role, 0) + 1
print('\nU+05BC in the ten verses, by the letter it sits on:', roles)
print('   its one name:', cp(DOT))
check('U6', 'one code point, several roles: in these verses, all of them · by role (no mappiq here)',
      (sum(roles.values()), roles), (71, {'dagesh': 61, 'shuruk (on vav, no other vowel)': 10}))

# --- U2: the stroke, two signs -------------------------------------------------------------------------------
# The prose (21-book) disjunctive accents; every other accent in U+0591..U+05AF is a conjunctive (or a mark).
DISJUNCTIVE = {chr(c) for c in (0x591, 0x592, 0x593, 0x594, 0x595, 0x596, 0x597, 0x598, 0x599, 0x59A, 0x59B, 0x59C,
                                0x59D, 0x59E, 0x59F, 0x5A0, 0x5A1, 0x5AE)}
def next_disjunctive(tokens, k):
    """The first disjunctive accent on a word after position k (conjunctive-only words are passed over)."""
    for tok in tokens[k + 1:]:
        d = [c for c in tok if c in DISJUNCTIVE]
        if d:
            return d[0]
    return None
MUNACH, REVIA = chr(0x5A3), chr(0x597)
kinds = {}
for ref in ('Gen 18:15', 'Exod 2:11'):
    t = V[ref]['text']
    tokens = t.split()
    for k, tok in enumerate(tokens):
        if tok == chr(0x5C0):
            prev = tokens[k - 1]
            acc = [unicodedata.name(c).replace('HEBREW ACCENT ', '') for c in prev if 0x591 <= ord(c) <= 0x5AF]
            nd = next_disjunctive(tokens, k)
            # the Masoretic rule: munach + stroke whose next disjunctive is revia is the accent legarmeh
            kind = 'legarmeh' if MUNACH in prev and nd == REVIA else 'paseq'
            kinds.setdefault(ref, []).append(kind)
            print(f'{ref}: stroke after {acc}, next disjunctive {unicodedata.name(nd).replace("HEBREW ACCENT ", "") if nd else None} -> {kind}')
check('U2', 'one code point, read by the accents around it', kinds, {'Gen 18:15': ['paseq'] * 3, 'Exod 2:11': ['legarmeh']})

# --- U4: no character for the tagin ---------------------------------------------------------------------------
names = [unicodedata.name(chr(c), '') for c in range(0x110000)]
print(f'\nUnicode {unicodedata.unidata_version}: {sum(map(bool, names))} named code points')
check('U4', 'names that mention TAGIN · Hebrew names that mention a CROWN · the control name HEBREW MARK UPPER DOT',
      (sum('TAGIN' in n for n in names), sum('HEBREW' in n and 'CROWN' in n for n in names), names.count('HEBREW MARK UPPER DOT')),
      (0, 0, 1))
done()
