#!/usr/bin/env python3
"""Whole-corpus measurements on the Westminster Leningrad Codex (openscriptures/morphhb).

    git clone https://github.com/openscriptures/morphhb
    python3 corpus_checks.py morphhb/wlc

Counts the numbers the resource quotes, each computed here from the XML, and checks every one of them against the
page: one line per check, ok or XX, and a count at the end; the exit status is 0 only when every check passed
(another morphhb revision may count differently). The known answer at the top (Gen 1:1 = 7 words and 28 letters)
checks the parser before any other number is used. No verse text is printed, only counts and references.

Claims tested (the tags are those of the ten-verse scripts that test the same claims):
  U2  1.2  The stroke U+05C0 in the Torah: how many, how many follow the rule for legarmeh (a munach before the
           stroke, a revia as the next disjunctive accent), how many belong to shalshelet; and what a first,
           wrong rule found (a revia on the very next word).
  U3  1.3  The dots over letters (U+05C4) and the dots below them (U+05C5).
  F4  2.4  The final letters carry almost no points, except kaf.
  N1  3.1  NFC changes almost half the words of the Torah; the WLC writes a dagesh before its vowel.
      3.2  Letters with two vowels, and where they are: NFC reverses the two on every one. The WLC has no CGJ.
  S13 4.6  In the hitpa'el (and the Aramaic t-stems), the tav written after a tsadi is a tet.
  T1  5.1  The morpheme slash; the morph attribute is divided in step with the word, the lemma attribute is not.
  T6  5.2  Ketiv/qere places.
  T7  5.2, 5.6  Verses, words and letters.
  T5  5.3  The section markers pe and samekh.
  C1  12   The bytes of pointed and bare text.
"""
import os, sys, unicodedata
from collections import Counter
import xml.etree.ElementTree as ET
EXAMPLES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(EXAMPLES, 'data'))
sys.path.insert(0, EXAMPLES)
from build_data import build, NS, book_file  # noqa: E402
from _common import check, done  # noqa: E402

TORAH = ['Gen', 'Exod', 'Lev', 'Num', 'Deut']
BIBLE = TORAH + ['Josh', 'Judg', '1Sam', '2Sam', '1Kgs', '2Kgs', 'Isa', 'Jer', 'Ezek', 'Hos', 'Joel', 'Amos', 'Obad',
                 'Jonah', 'Mic', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal', 'Ps', 'Prov', 'Job', 'Song', 'Ruth', 'Lam',
                 'Eccl', 'Esth', 'Dan', 'Ezra', 'Neh', '1Chr', '2Chr']
LETTER = lambda c: 0x5D0 <= ord(c) <= 0x5EA
H = lambda *cps: ''.join(chr(c) for c in cps)
MUNACH, REVIA, SHALSHELET = chr(0x5A3), chr(0x597), chr(0x593)
STROKE, UPPER_DOT, LOWER_DOT, CGJ = chr(0x5C0), chr(0x5C4), chr(0x5C5), chr(0x34F)
DAGESH, LAMED, TSADI, TET, TAV = chr(0x5BC), chr(0x5DC), chr(0x5E6), chr(0x5D8), chr(0x5EA)
KAF, MEM, NUN, PE, TSADI_F = FINALS = H(0x5DA, 0x5DD, 0x5DF, 0x5E3, 0x5E5)   # the five final forms
SEP = chr(0x5BE)
CITY = H(0x5D9, 0x5E8, 0x5D5, 0x5E9, 0x5DC, 0x5DD)        # Jerusalem as the WLC writes it, consonants only
CITY_TO = H(0x5D9, 0x5E8, 0x5D5, 0x5E9, 0x5DC, 0x5DE, 0x5D4)   # the same with the directional ending: "to Jerusalem"

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
            yield b, v, raw, raw.replace('/', ''), qere, segs

def words(text):
    return [w for w in text.replace(SEP, ' ').split() if any(LETTER(c) for c in w)]

def bare(text):                     # every combining mark removed
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

def no_teamim(text):                # the te'amim (U+0591..U+05AF) removed, the points kept
    return ''.join(c for c in text if not 0x591 <= ord(c) <= 0x5AF)

def stem(morph):
    """'H' or 'A' (Hebrew or Aramaic) and the stem letter of the verb in a morphhb morph code, or None."""
    verb = [p for p in morph[1:].split('/') if p.startswith('V')]
    return (morph[:1], verb[0][1]) if verb else None

def main(wlc):
    root = ET.parse(book_file(wlc, 'Gen')).getroot()
    rev = [r for r in root.iter(NS + 'revisionDesc')][:1]
    if rev:
        print('morphhb header, latest revision:', ' '.join(''.join(rev[0].itertext()).split())[:120])
    # known answer first
    g11 = next(t for b, v, r, t, q, s in verses(wlc, ['Gen']) if v.get('osisID') == 'Gen.1.1')
    print('Gen 1:1 words', len(words(g11)), '· letters', sum(map(LETTER, g11)), '(known answer: 7 and 28)')
    assert (len(words(g11)), sum(map(LETTER, g11))) == (7, 28)

    T = Counter(); by_book = {b: Counter() for b in TORAH}
    strokes = Counter()
    for b, v, raw, text, qere, segs in verses(wlc, TORAH):
        T['verses'] += 1; by_book[b]['verses'] += 1
        n = sum(map(LETTER, text)); T['letters'] += n; by_book[b]['letters'] += n
        ws = words(text)
        T['words'] += len(ws)
        T['words_with_slash'] += sum('/' in w for w in words(raw))
        T['nfc_changed'] += sum(unicodedata.normalize('NFC', w) != w for w in ws)
        T['qere'] += len(qere)
        for kind in ('x-pe', 'x-samekh'):
            T[kind[2:]] += segs.count(kind); by_book[b][kind[2:]] += segs.count(kind)
        T['bytes'] += len(text.encode()); T['bytes_points'] += len(no_teamim(text).encode())
        T['bytes_bare'] += len(bare(text).encode())
        for w in v.findall(NS + 'w'):                       # the written words; a read word sits inside a <note>
            slashes = ''.join(w.itertext()).count('/')
            T['w'] += 1
            T['morph_in_step'] += (w.get('morph') or '').count('/') == slashes
            T['lemma_in_step'] += (w.get('lemma') or '').count('/') == slashes
        toks = text.split()                                 # a maqaf pair is one token: it carries one accent
        for k, tok in enumerate(toks):
            if tok == STROKE:
                strokes['total'] += 1
                strokes['after a munach'] += MUNACH in toks[k - 1]
                strokes['legarmeh by the rule'] += MUNACH in toks[k - 1] and next_disjunctive(toks, k) == REVIA
                strokes['after a shalshelet word'] += SHALSHELET in toks[k - 1]
                strokes['first rule: revia on the next token'] += MUNACH in toks[k - 1] and REVIA in ''.join(toks[k + 1:k + 2])
        strokes['U+05C0 anywhere in the text'] += text.count(STROKE)
    print('\nTORAH (Gen-Deut, written text, notes removed):')
    for k in ('verses', 'words', 'letters', 'words_with_slash', 'nfc_changed', 'qere', 'pe', 'samekh'):
        print(f'  {k:18s} {T[k]:>8,}')
    print('  by book:', ' · '.join(f'{b} {by_book[b]["verses"]:,} verses, {by_book[b]["letters"]:,} letters, '
                                    f'pe {by_book[b]["pe"]}, samekh {by_book[b]["samekh"]}' for b in TORAH))
    print('  304,850 letters is the count of this text, the WLC\'s written words with the notes removed. The figure'
          '\n  usually quoted for the Torah, 304,805, counts the letters of a different text (editions differ, section 5.9).')
    print(f'  share of words changed by NFC: {T["nfc_changed"] / T["words"]:.1%} · words carrying a morphhb slash: {T["words_with_slash"] / T["words"]:.1%}')
    print(f'  written words (<w>) {T["w"]:,}: the morph attribute has as many slashes as the word in {T["morph_in_step"]:,},'
          f' the lemma attribute in {T["lemma_in_step"]:,}')
    print('  the stroke U+05C0:', dict(strokes))
    print(f'  bytes in UTF-8, verse by verse: with points and te\'amim {T["bytes"]:,} · points only {T["bytes_points"]:,}'
          f' · bare {T["bytes_bare"]:,}')

    B = Counter(); dotted = Counter(); below = Counter(); final_points = {f: Counter() for f in FINALS}
    two_vowels = Counter(); jerusalem = Counter(); elsewhere = []; dagesh_order = Counter()
    tsadi_tet = []; tav_by_tsadi = []; pointed_pe = []
    for b, v, raw, text, qere, segs in verses(wlc, BIBLE):
        osis = v.get('osisID')
        B['verses'] += 1
        B['qere'] += len(qere)
        B['cgj'] += text.count(CGJ)
        if text.count(UPPER_DOT):
            dotted[osis] = text.count(UPPER_DOT)
        if text.count(LOWER_DOT):
            below[osis] = text.count(LOWER_DOT)
        for w in v.findall(NS + 'w'):                       # verbs: a tsadi with a tet or a tav beside it
            cons = ''.join(c for c in ''.join(w.itertext()) if LETTER(c))
            st = stem(w.get('morph') or '')
            lemma = ''.join(c for c in (w.get('lemma') or '').split('/')[-1] if c.isdigit())
            if TSADI + TET in cons:
                tsadi_tet.append((osis, ''.join(st or ''), lemma))
            if st == ('H', 't') and (TSADI + TAV in cons or TAV + TSADI in cons):
                tav_by_tsadi.append((osis, lemma))
        for w in words(text):
            cons = ''.join(c for c in w if LETTER(c))
            nth = -1                                         # the position of the current letter among the letters
            for i, ch in enumerate(w):
                if not LETTER(ch):
                    continue
                nth += 1
                marks = []
                j = i + 1
                while j < len(w) and unicodedata.category(w[j]) == 'Mn':
                    marks.append(w[j]); j += 1
                if ch in FINALS:                            # one count per LETTER: the points it carries, together
                    pts = sorted(unicodedata.name(m).replace('HEBREW POINT ', '') for m in marks if 0x5B0 <= ord(m) <= 0x5BD)
                    final_points[ch]['+'.join(pts) or 'none'] += 1
                    if ch == PE and pts:
                        pointed_pe.append(osis)
                vowels = [m for m in marks if 0x5B0 <= ord(m) <= 0x5BB]
                if DAGESH in marks and vowels:
                    dagesh_order['dagesh first' if marks.index(DAGESH) < marks.index(vowels[0]) else 'vowel first'] += 1
                if len(vowels) >= 2:
                    two_vowels['letters'] += 1
                    two_vowels['reordered by NFC'] += ''.join(vowels) != unicodedata.normalize('NFC', ''.join(vowels))
                    pair = ' + '.join(unicodedata.name(m).replace('HEBREW POINT ', '') for m in vowels)
                    if ch == LAMED and cons.endswith(CITY) and nth == len(cons) - 2:
                        jerusalem[pair] += 1
                        jerusalem['with a prefix' if len(cons) > len(CITY) else 'without a prefix'] += 1
                    elif ch == LAMED and cons.endswith(CITY_TO) and nth == len(cons) - 3:
                        jerusalem['to Jerusalem: ' + pair] += 1
                    else:
                        elsewhere.append((osis, pair))
    print('\nWHOLE BIBLE (39 books):')
    print(f'  verses {B["verses"]:,} · ketiv/qere places {B["qere"]:,} · combining grapheme joiners (U+034F) {B["cgj"]}')
    print(f'  verses with the upper dot U+05C4: {len(dotted)} · dotted letters: {sum(dotted.values())}')
    print('   ', ' '.join(f'{k}:{v}' for k, v in sorted(dotted.items())))
    print(f'  verses with the lower dot U+05C5: {len(below)} · letters: {sum(below.values())} ·', ' '.join(f'{k}:{v}' for k, v in sorted(below.items())))
    print(f'  letters with a dagesh and a vowel: {dict(dagesh_order)}')
    print(f'  letters carrying two vowel points: {two_vowels["letters"]} (reordered by NFC: {two_vowels["reordered by NFC"]})')
    print('    the lamed of Jerusalem:', dict(jerusalem))
    print('    elsewhere:', elsewhere)
    print('  final letters, by the points each one carries:')
    for f in FINALS:
        print(f'    {unicodedata.name(f):24s}', dict(final_points[f].most_common()))
    print("  words with a tsadi followed by a tet (reference, language and verb stem, lemma):", tsadi_tet)
    print("  hitpa'el words (morph stem t) with a tav beside a tsadi (reference, lemma):", tav_by_tsadi)

    print('\nTHE NUMBERS ON THE PAGE:')
    with_point = lambda f, p: sum(n for combo, n in final_points[f].items() if p in combo.split('+'))
    pointed = lambda f: sum(n for combo, n in final_points[f].items() if combo != 'none')
    letters = lambda f: sum(final_points[f].values())
    check('U2', 'Torah: strokes U+05C0 · each a token of its own · after a munach · legarmeh by the rule · after a '
          'shalshelet word · the rest', (strokes['U+05C0 anywhere in the text'], strokes['total'], strokes['after a munach'],
          strokes['legarmeh by the rule'], strokes['after a shalshelet word'],
          strokes['total'] - strokes['legarmeh by the rule'] - strokes['after a shalshelet word']), (378, 378, 315, 280, 4, 94))
    check('U2', 'Torah: the first rule (a munach before the stroke, a revia on the next token; a maqaf pair is one token)',
          strokes['first rule: revia on the next token'], 29)
    check('U3', 'Bible: letters with the upper dot U+05C4 · verses · in Gen 18:9', (sum(dotted.values()), len(dotted), dotted['Gen.18.9']), (53, 15, 4))
    check('U3', 'Bible: letters with the lower dot U+05C5 · the verses', (sum(below.values()), sorted(below)), (3, ['Ps.27.13']))
    check('F4', 'final kaf: letters · with a vowel · with a sheva · with a qamats · with both · with a dagesh · a dagesh '
          'without a vowel · with a meteg', (letters(KAF), letters(KAF) - final_points[KAF]['none'], with_point(KAF, 'SHEVA'),
          with_point(KAF, 'QAMATS'), sum(n for c, n in final_points[KAF].items() if 'SHEVA' in c and 'QAMATS' in c),
          with_point(KAF, 'DAGESH OR MAPIQ'), final_points[KAF]['DAGESH OR MAPIQ'], with_point(KAF, 'METEG')),
          (14002, 13921, 7405, 6516, 0, 126, 0, 15))
    check('F4', 'pointed letters: final nun · final pe · final mem · final tsadi; of all of them',
          (pointed(NUN), pointed(PE), pointed(MEM), pointed(TSADI_F), sum(letters(f) for f in (NUN, PE, MEM, TSADI_F))),
          (40, 1, 0, 0, 62374))
    check('F4', 'the points they carry: final nun · final pe, and where that pe is', ([c for c in final_points[NUN] if c != 'none'],
          [c for c in final_points[PE] if c != 'none'], pointed_pe), (['QAMATS'], ['DAGESH OR MAPIQ+SHEVA'], ['Prov.30.6']))
    check('N1', 'Torah: words NFC changes · of all words · share', (T['nfc_changed'], T['words'], f'{T["nfc_changed"] / T["words"]:.1%}'),
          (37528, 79982, '46.9%'))
    check('N1', 'Bible: letters with a dagesh and a vowel, the dagesh written first · the vowel first',
          (dagesh_order['dagesh first'], dagesh_order['vowel first']), (121949, 0))
    check('N1', 'Bible: letters with two vowels · reordered by NFC · combining grapheme joiners',
          (two_vowels['letters'], two_vowels['reordered by NFC'], B['cgj']), (641, 641, 0))
    city = jerusalem['PATAH + HIRIQ'] + jerusalem['QAMATS + HIRIQ']
    to_city = jerusalem['to Jerusalem: PATAH + SHEVA'] + jerusalem['to Jerusalem: QAMATS + SHEVA']
    check('N1', 'of them the lamed of Jerusalem: in the name (patah + hiriq, qamats + hiriq; without, with a prefix) · '
          'in "to Jerusalem" (patah + sheva, qamats + sheva) · elsewhere',
          ((city, jerusalem['PATAH + HIRIQ'], jerusalem['QAMATS + HIRIQ'], jerusalem['without a prefix'], jerusalem['with a prefix']),
           (to_city, jerusalem['to Jerusalem: PATAH + SHEVA'], jerusalem['to Jerusalem: QAMATS + SHEVA']), len(elsewhere)),
          ((633, 348, 285, 345, 288), (4, 3, 1), 4))
    check('S13', 'words with a tsadi followed by a tet: all are verbs in a t-stem, with tsadi as the first root letter',
          tsadi_tet, [('Gen.44.16', 'Ht', '6663'), ('Josh.9.4', 'Ht', '6737'), ('Josh.9.12', 'Ht', '6679'),
                      ('Dan.4.12', 'AM', '6647'), ('Dan.4.20', 'AM', '6647'), ('Dan.4.30', 'AM', '6647'), ('Dan.5.21', 'AM', '6647')])
    check('S13', "hitpa'el words with a tav beside a tsadi: none has tsadi as its first root letter (lemmas 3320, 7364, 553)",
          tav_by_tsadi, [('Exod.2.4', '3320'), ('Job.9.30', '7364'), ('Ruth.1.18', '553')])
    check('T1', 'Torah: words carrying a morphhb slash · share', (T['words_with_slash'], f'{T["words_with_slash"] / T["words"]:.1%}'), (39585, '49.5%'))
    check('T1', 'Torah: written words · the morph attribute divided like the word · the lemma attribute',
          (T['w'], T['morph_in_step'], T['lemma_in_step']), (79982, 79982, 67263))
    check('T6', 'ketiv/qere places: Torah · Bible', (T['qere'], B['qere']), (67, 1251))
    check('T7', 'Torah: verses · words · letters; Bible: verses', (T['verses'], T['words'], T['letters'], B['verses']), (5853, 79982, 304850, 23213))
    check('T5', 'Torah: section markers pe · samekh', (T['pe'], T['samekh']), (293, 394))
    check('C1', 'Torah: UTF-8 bytes with points and te\'amim, and with points only, to the bytes of the bare text',
          (f'{T["bytes"] / T["bytes_bare"]:.2f}', f'{T["bytes_points"] / T["bytes_bare"]:.2f}'), ('1.94', '1.76'))
    done()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
