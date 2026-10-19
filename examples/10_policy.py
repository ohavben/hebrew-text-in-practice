#!/usr/bin/env python3
"""Masking a word inside pointed text (the technique behind a display policy such as aliasing the Divine Name).

The examples mask an ordinary word, "ארץ" (land), so that this file never spells out a Name; the technique is
the same. Claims tested (section 11 of the resource):
  D2a A pattern that allows combining marks between the letters finds the word in pointed text; stored text
      stays byte-exact, and the mask is applied at display time.
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
# combining marks only: the block's code points of category Mn (NOT the maqaf, paseq, sof pasuq, nun hafukha)
MARKS = '[' + ''.join(chr(c) for c in range(0x591, 0x5C8) if unicodedata.category(chr(c)) == 'Mn') + ']*'
def word_re(letters):
    """A pattern for a word written with any points and te'amim between (and after) its letters.
    Each slot may hold either form of a letter that has a final form."""
    alt = {'כ': '[כך]', 'מ': '[מם]', 'נ': '[נן]', 'פ': '[פף]', 'צ': '[צץ]', 'ך': '[כך]', 'ם': '[מם]', 'ן': '[נן]', 'ף': '[פף]', 'ץ': '[צץ]'}
    return re.compile(''.join(alt.get(ch, re.escape(ch)) + MARKS for ch in letters))

MASK = '⟨…⟩'
target = word_re('ארץ')
stored = [V['Gen 2:6']['text'], V['Exod 1:7']['text']]
shown = [target.sub(MASK, s) for s in stored]
check('D2a', 'occurrences found in the pointed verses', sum(len(target.findall(s)) for s in stored), 2)
check('D2a', 'none left after masking', sum(len(target.findall(s)) for s in shown), 0)
check('D2a', 'the stored text is untouched', stored[0] == V['Gen 2:6']['text'], True)

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
