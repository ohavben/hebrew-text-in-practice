#!/usr/bin/env python3
"""Whole-corpus measurements on the Westminster Leningrad Codex (openscriptures/morphhb).

    git clone https://github.com/openscriptures/morphhb
    python3 corpus_checks.py morphhb/wlc

Prints counts the resource quotes. Each figure is computed here, from the XML; the known answers at the top
(Gen 1:1 = 7 words and 28 letters) check the parser before any other number is used.
"""
import os, sys, unicodedata
from collections import Counter
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'))
from build_data import build, NS, book_file  # noqa: E402

TORAH = ['Gen', 'Exod', 'Lev', 'Num', 'Deut']
BIBLE = TORAH + ['Josh', 'Judg', '1Sam', '2Sam', '1Kgs', '2Kgs', 'Isa', 'Jer', 'Ezek', 'Hos', 'Joel', 'Amos', 'Obad',
                 'Jonah', 'Mic', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal', 'Ps', 'Prov', 'Job', 'Song', 'Ruth', 'Lam',
                 'Eccl', 'Esth', 'Dan', 'Ezra', 'Neh', '1Chr', '2Chr']
LETTER = lambda c: 0x5D0 <= ord(c) <= 0x5EA
MUNACH, STROKE, UPPER_DOT, CGJ = chr(0x5A3), chr(0x5C0), chr(0x5C4), chr(0x34F)
FINALS = 'ךםןףץ'
SEP = chr(0x5BE)

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

def verses(wlc, books):
    for b in books:
        root = ET.parse(book_file(wlc, b)).getroot()
        for v in root.iter(NS + 'verse'):
            raw, qere, segs = build(v)
            yield b, v.get('osisID'), raw, raw.replace('/', ''), qere, segs

def words(text):
    return [w for w in text.replace(SEP, ' ').split() if any(LETTER(c) for c in w)]

def main(wlc):
    root = ET.parse(book_file(wlc, 'Gen')).getroot()
    rev = [r for r in root.iter(NS + 'revisionDesc')][:1]
    if rev:
        print('morphhb header, latest revision:', ' '.join(''.join(rev[0].itertext()).split())[:120])
    # known answer first
    g11 = next(t for b, o, r, t, q, s in verses(wlc, ['Gen']) if o == 'Gen.1.1')
    print('Gen 1:1 words', len(words(g11)), '· letters', sum(map(LETTER, g11)), '(known answer: 7 and 28)')
    assert (len(words(g11)), sum(map(LETTER, g11))) == (7, 28)

    T = Counter()
    strokes = Counter()
    for b, osis, raw, text, qere, segs in verses(wlc, TORAH):
        T['verses'] += 1
        T['letters'] += sum(map(LETTER, text))
        ws = words(text)
        T['words'] += len(ws)
        T['words_with_slash'] += sum('/' in w for w in words(raw))
        T['nfc_changed'] += sum(unicodedata.normalize('NFC', w) != w for w in ws)
        T['qere'] += len(qere)
        T['pe'] += segs.count('x-pe'); T['samekh'] += segs.count('x-samekh')
        toks = text.split()
        for k, tok in enumerate(toks):
            if tok == STROKE:
                strokes['total'] += 1
                strokes['after a munach word' if MUNACH in toks[k - 1] else 'after another accent'] += 1
                strokes['legarmeh by the rule (munach before, next disjunctive revia)'] += MUNACH in toks[k - 1] and next_disjunctive(toks, k) == chr(0x597)
                strokes['part of shalshelet (after a shalshelet word)'] += chr(0x593) in toks[k - 1]
    print('\nTORAH (Gen-Deut, written text, notes removed):')
    for k in ('verses', 'words', 'letters', 'words_with_slash', 'nfc_changed', 'qere', 'pe', 'samekh'):
        print(f'  {k:18s} {T[k]:>8,}')
    print(f'  share of words changed by NFC: {T["nfc_changed"] / T["words"]:.1%} · words carrying a morphhb slash: {T["words_with_slash"] / T["words"]:.1%}')
    print('  the stroke U+05C0 as a separate token:', dict(strokes))

    B = Counter(); dotted = Counter(); final_points = {f: Counter() for f in FINALS}; two_vowels = Counter()
    for b, osis, raw, text, qere, segs in verses(wlc, BIBLE):
        B['verses'] += 1
        B['qere'] += len(qere)
        B['cgj'] += text.count(CGJ)
        n = text.count(UPPER_DOT)
        if n:
            dotted[osis] = n
        for w in words(text):
            for i, ch in enumerate(w):
                if ch in FINALS:
                    j = i + 1
                    while j < len(w) and unicodedata.category(w[j]) == 'Mn':
                        if 0x5B0 <= ord(w[j]) <= 0x5BC:
                            final_points[ch][unicodedata.name(w[j]).replace('HEBREW POINT ', '')] += 1
                        j += 1
                if LETTER(ch):
                    marks = []
                    j = i + 1
                    while j < len(w) and unicodedata.category(w[j]) == 'Mn':
                        marks.append(w[j]); j += 1
                    vowels = [m for m in marks if 0x5B0 <= ord(m) <= 0x5BB]
                    if len(vowels) >= 2:
                        two_vowels[''.join(vowels) == unicodedata.normalize('NFC', ''.join(vowels))] += 1
    print('\nWHOLE BIBLE (39 books):')
    print(f'  verses {B["verses"]:,} · ketiv/qere places {B["qere"]:,} · combining grapheme joiners (U+034F) {B["cgj"]}')
    print(f'  verses with the upper dot U+05C4: {len(dotted)} · dotted letters: {sum(dotted.values())}')
    print('   ', ' '.join(f'{k}:{v}' for k, v in sorted(dotted.items())))
    print(f'  letters carrying two vowel points: {sum(two_vowels.values())} (stored order already NFC order: {two_vowels[True]}, reordered by NFC: {two_vowels[False]})')
    print('  points on the final letters:')
    for f in FINALS:
        print(f'    {unicodedata.name(f):24s}', dict(final_points[f].most_common()))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
