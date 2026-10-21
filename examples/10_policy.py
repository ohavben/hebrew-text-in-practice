#!/usr/bin/env python3
"""Masking a word inside pointed text (the technique behind a display policy such as aliasing the Divine Name).

The examples mask an ordinary word, "ארץ" (land), so that this file never spells out a Name; the technique is
the same. Claims tested (section 11 of the resource):
  D2a A pattern that allows combining marks between the letters finds the word in pointed text; stored text
      stays byte-exact, and the mask is applied at display time. The pattern must allow ANY combining mark (from
      any block, not only the Hebrew points) and any format character (category Cf): a pattern that allows only
      the Hebrew points fails open, and one joiner or soft hyphen inside the word leaves it on screen.
  D2b Mask first, then truncate: cutting a snippet first can split the word, the pattern no longer matches,
      and the first letters leak.
  D2c One replacement pass is not always idempotent: the replacement and its neighbours can form the pattern
      again. Repeat until nothing changes, or choose a replacement that cannot recreate it.
  D2d A mask keyed to one spelling misses the other (plene / defective); allow the optional vowel letter.
Run: python3 10_policy.py
"""
import os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import verses, check, done

V = verses()
# Between the letters: any combining mark (category M, from any block) and any format character (category Cf).
# NOT the maqaf, paseq, sof pasuq or nun hafukha: those are punctuation, and a word does not run across them.
CATEGORY = lambda c: unicodedata.category(chr(c))
MARKS = '[' + ''.join(chr(c) for c in range(0x110000) if CATEGORY(c)[0] == 'M' or CATEGORY(c) == 'Cf') + ']*'
# The narrower class, for comparison: the Hebrew points and te'amim only (the block's code points of category Mn).
HEBREW_POINTS = '[' + ''.join(chr(c) for c in range(0x591, 0x5C8) if CATEGORY(c) == 'Mn') + ']*'
def word_re(letters, marks=MARKS):
    """A pattern for a word written with any marks (and invisible format characters) between and after its letters.
    Each slot may hold either form of a letter that has a final form."""
    alt = {'כ': '[כך]', 'מ': '[מם]', 'נ': '[נן]', 'פ': '[פף]', 'צ': '[צץ]', 'ך': '[כך]', 'ם': '[מם]', 'ן': '[נן]', 'ף': '[פף]', 'ץ': '[צץ]'}
    return re.compile(''.join(alt.get(ch, re.escape(ch)) + marks for ch in letters))

MASK = '⟨…⟩'
target = word_re('ארץ')
stored = [V['Gen 2:6']['text'], V['Exod 1:7']['text']]
shown = [target.sub(MASK, s) for s in stored]
check('D2a', 'occurrences found in the pointed verses', sum(len(target.findall(s)) for s in stored), 2)
check('D2a', 'none left after masking', sum(len(target.findall(s)) for s in shown), 0)
check('D2a', 'the stored text is untouched', stored[0] == V['Gen 2:6']['text'], True)

# D2a — one hidden character inside the word: ZERO WIDTH JOINER, SOFT HYPHEN, RIGHT-TO-LEFT MARK (category Cf,
# section 9.1), COMBINING GRAPHEME JOINER (section 3.2) and COMBINING DOT ABOVE (section 3.5), each placed after
# every character of the word but its last: 5 characters x 5 places = 25 variants of Gen 2:6
HIDDEN = [0x200D, 0x00AD, 0x200F, 0x034F, 0x0307]
s = V['Gen 2:6']['text']
m = target.search(s)
variants = [s[:i] + chr(c) + s[i:] for c in HIDDEN for i in range(m.start() + 1, m.end())]
narrow = word_re('ארץ', HEBREW_POINTS)
letters = lambda t: ''.join(ch for ch in t if not (CATEGORY(ord(ch))[0] == 'M' or CATEGORY(ord(ch)) == 'Cf'))
shows = lambda pattern, t: 'ארץ' in letters(pattern.sub(MASK, t))          # the word's letters still on screen
print(f'  {len(variants)} variants with a hidden character inside the word')
check('D2a', 'a pattern that allows only the Hebrew points: variants masked · variants where the word still shows',
      (sum(len(narrow.findall(t)) for t in variants), sum(shows(narrow, t) for t in variants)), (0, 25))
check('D2a', 'the pattern that allows any mark and any format character: masked · still shows',
      (sum(len(target.findall(t)) for t in variants), sum(shows(target, t) for t in variants)), (25, 0))

# D2b — truncate a snippet in the middle of the word, then mask: the pattern misses the half word
s = V['Exod 1:7']['text']
m = target.search(s)
cut = m.start() + (m.end() - m.start()) // 2                  # a snippet that ends inside the word
leak = target.sub(MASK, s[:cut])
safe = target.sub(MASK, s)[:cut]
print('  truncate then mask, the last characters:', ' '.join(f'{ord(c):04X}' for c in leak[-4:]))
check('D2b', 'truncate-then-mask leaves letters of the word on screen', 'א' in leak[m.start() - 2:], True)
check('D2b', 'mask-then-truncate does not', 'ארץ'[0] in safe[m.start():], False)

# D2c — a single pass can recreate the pattern
pat = re.compile('אבב')
text = 'אבבבב'                                                   # SYNTHETIC letters
once = pat.sub('א', text)
check('D2c', 'after one pass the pattern is still there', bool(pat.search(once)), True)
fixed = text
while pat.search(fixed):
    fixed = pat.sub('א', fixed)
check('D2c', 'repeating until nothing changes removes it', bool(pat.search(fixed)), False)

# D2d — plene and defective spellings
defective, plene = 'כהן', 'כוהן'                              # "priest": the same word, with and without vav
narrow = word_re(defective)
wide = re.compile('כ' + MARKS + '(?:ו' + MARKS + ')?' + 'ה' + MARKS + '[נן]' + MARKS)
check('D2d', 'a mask keyed to the defective spelling misses the plene one', bool(narrow.fullmatch(plene)), False)
check('D2d', 'an optional vav catches both', (bool(wide.fullmatch(defective)), bool(wide.fullmatch(plene))), (True, True))
done()
