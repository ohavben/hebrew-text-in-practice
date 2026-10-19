#!/usr/bin/env python3
"""Final forms: five letters, two code points each.

Claims tested (section 2 of the resource):
  F1  A needle written with a medial letter never matches the final form, and vice versa; folding only one side
      of the comparison returns a silent zero. Fold the text AND the needle.
  F2  Folding erases the word end a final letter marks: the folded needle also matches inside longer words.
      Restore it with a boundary when the needle ended in a final.
  F3  A medial letter can end a token legitimately (numerals, abbreviations), so "medial at the end = typo" is
      not a rule.
Run: python3 02_finals.py
"""
import os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import verses, check, done

FINAL_TO_MEDIAL = {'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ'}
for f, m in FINAL_TO_MEDIAL.items():
    print(f'{unicodedata.name(f):32s} U+{ord(f):04X}   {unicodedata.name(m):26s} U+{ord(m):04X}')

def strip(s):          # combining marks out; maqaf and sof pasuq become spaces (see 01_layers.py)
    s = ''.join(ch for ch in s if not unicodedata.category(ch).startswith('M'))
    return re.sub('[' + chr(0x5BE) + chr(0x5C0) + chr(0x5C3) + ']', ' ', s)

def fold(s):
    return ''.join(FINAL_TO_MEDIAL.get(ch, ch) for ch in s)

text = ' '.join(strip(v['text']) for v in verses().values())    # the ten verses, consonants only

# F1 — a needle typed with the medial form (as a stem or a prefix query would be)
needle = 'הארצ'                                  # "the land", typed as a stem would be: with a medial tsadi
final = 'הארץ'                                   # the same word, typed with the final tsadi
check('F1', 'query typed with the medial form, text not folded', text.count(needle), 0)
check('F1', 'query typed with the final form, text not folded (works only if you typed the right form)', text.count(final), 2)
check('F1', 'query folded, text NOT folded (one side only)', text.count(fold(final)), 0)
check('F1', 'text folded, query typed with the final form (the other side only)', fold(text).count(final), 0)
either_form = len(re.findall('האר[צץ]', text))      # an independent count: a class that accepts both forms
print(f'\n"{needle}" written either way, counted by the class [צץ]: {either_form}')
check('F1', 'both sides folded = the count by the both-forms class', fold(text).count(fold(needle)), either_form)
check('F1', 'and that count is not zero', either_form > 0, True)

# F2 — the folded needle forgets where the word ended
needle = 'מן'                                     # "from": the final nun says "the word ends here"
phrase = 'מן המנחה ומן הענן'                      # SYNTHETIC: "from the offering and from the cloud"
anywhere = fold(phrase).count(fold(needle))
at_end = len(re.findall(fold(needle) + r'(?!\S)', fold(phrase)))
inside = [w for w in fold(phrase).split() if fold(needle) in w and not w.endswith(fold(needle))]
print(f'\n"{needle}" in the synthetic phrase "{phrase}": folded, anywhere {anywhere}; folded, at a word end {at_end}')
print('   folded matches inside longer words:', inside)
check('F2', 'the folded needle also matches inside a longer word', inside, ['המנחה'])
check('F2', 'a word-end boundary after the folded needle removes exactly those', at_end, anywhere - len(inside))

# F3 — medial letters that end a token on purpose
tokens = ['תש״פ', 'כ׳', 'פ׳', 'יד:כ']                # a year (5780), the numeral 20, an abbreviation, chapter:verse
naive = [t for t in tokens if t and t[-1] in FINAL_TO_MEDIAL.values()]
print('\ntokens that end in a medial letter, all correct as written:', tokens)
check('F3', 'a "medial at the end" rule flags correct tokens', len(naive), 2)
done()
