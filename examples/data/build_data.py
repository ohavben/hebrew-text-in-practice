#!/usr/bin/env python3
"""Build data/verses.json — the Bible verses the examples use — from the Open Scriptures Hebrew Bible (morphhb).

    git clone https://github.com/openscriptures/morphhb      # the Westminster Leningrad Codex as OSIS XML
    python3 build_data.py morphhb/wlc > verses.json

The WLC text is in the public domain; the morphhb markup is CC BY 4.0 (Open Scriptures Hebrew Bible).
Every verse below was chosen because it shows one feature AND contains no Divine Name: the resource avoids
spelling out the Name in its own examples (see the display-policy section). The builder refuses a verse whose
consonants contain one of the Name stems — a conservative test that also catches some ordinary words.

Fields per verse:
  ref       "Gen 2:6"
  text      the written text as one string: words separated by spaces, the maqaf and the sof pasuq attached
            as in print, editorial notes dropped, the morphhb morpheme slash removed. At a ketiv/qere place the
            WRITTEN (ketiv, unpointed) word stands in the text.
  raw       the same, but keeping morphhb's "/" between the morphemes of a word
  qere      [[ketiv, qere], ...] where the verse has a ketiv/qere
  segs      the <seg> types in the verse (x-maqqef, x-paseq, x-sof-pasuq, x-pe, x-samekh)
  shows     what the verse is used to show
"""
import json, os, re, sys
import xml.etree.ElementTree as ET

NS = '{http://www.bibletechnologies.net/2003/OSIS/namespace}'

SPECIMENS = [
    ('Gen.2.6',   'maqaf: four words joined to the next by U+05BE'),
    ('Gen.2.10',  'maqaf, final letters'),
    ('Gen.2.25',  'meteg (U+05BD) and silluq, final letters, no maqaf'),
    ('Gen.18.9',  'the extraordinary dots (U+05C4) over a word'),
    ('Gen.18.15', 'the stroke U+05C0 as a true paseq'),
    ('Exod.2.11', 'the stroke U+05C0 as part of the accent legarmeh (munach + stroke)'),
    ('Exod.1.7',  'a verse that ends an open section (pe)'),
    ('Exod.1.22', 'a verse that ends a closed section (samekh)'),
    ('Lev.9.22',  'a ketiv/qere: written without the yod, read with it'),
    ('Ps.107.23', 'an inverted nun (U+05C6) before the verse'),
]

def H(*cps):
    return ''.join(chr(c) for c in cps)

# Name stems on the consonants (points removed, final forms folded). Conservative on purpose.
NAME_STEMS = [H(0x5D9, 0x5D4, 0x5D5, 0x5D4), H(0x5D0, 0x5DC, 0x5D4), H(0x5D0, 0x5D3, 0x5E0, 0x5D9)]
FOLD = {chr(0x5DA): chr(0x5DB), chr(0x5DD): chr(0x5DE), chr(0x5DF): chr(0x5E0), chr(0x5E3): chr(0x5E4), chr(0x5E5): chr(0x5E6)}

SEPARATORS = {chr(0x5BE), chr(0x5C0), chr(0x5C3), ' '}    # maqaf, paseq, sof pasuq: punctuation, NOT marks

def consonants(s):
    # Keep letters; turn the separators into spaces. Dropping the maqaf instead would fuse the two words it
    # joins -- and that fusion made this very filter refuse Lev 9:22: the preposition and the noun after it,
    # glued, spell a Name stem.
    return ''.join(' ' if ch in SEPARATORS else FOLD.get(ch, ch) for ch in s if 0x5D0 <= ord(ch) <= 0x5EA or ch in SEPARATORS)

def book_file(wlc_dir, book):
    for name in (f'{book}.xml', f'wlc_{book}.xml'):
        p = os.path.join(wlc_dir, name)
        if os.path.exists(p):
            return p
    sys.exit(f'no XML for {book} in {wlc_dir}')

def verse_element(wlc_dir, osis):
    book = osis.split('.')[0]
    root = ET.parse(book_file(wlc_dir, book)).getroot()
    for v in root.iter(NS + 'verse'):
        if v.get('osisID') == osis:
            return v
    sys.exit(f'no verse {osis}')

def build(v):
    parts, qere, segs = [], [], []
    for el in v:
        tag = el.tag[len(NS):] if el.tag.startswith(NS) else el.tag
        tail_space = bool(el.tail and el.tail.strip() == '' and el.tail != '')
        if tag == 'w':
            parts.append(''.join(el.itertext()) + (' ' if tail_space else ''))
        elif tag == 'seg':
            segs.append(el.get('type'))
            if el.get('type') in ('x-pe', 'x-samekh'):
                continue                         # section marks: reported in segs, not printed in the text
            parts.append((el.text or '') + (' ' if tail_space else ''))
        elif tag == 'note':
            if el.get('type') == 'variant':      # <catchWord>ketiv</catchWord><rdg type="x-qere"><w>qere</w></rdg>
                cw = el.find(NS + 'catchWord')
                rdg = el.find(NS + 'rdg')
                if cw is not None and rdg is not None:
                    qere.append([''.join(cw.itertext()).replace('/', ''), ''.join(rdg.itertext()).replace('/', '').strip()])
            if tail_space and parts and not parts[-1].endswith(' '):
                parts[-1] += ' '
    raw = re.sub(r'\s+', ' ', ''.join(parts)).strip()
    return raw, qere, segs

def main(wlc_dir):
    out = []
    for osis, shows in SPECIMENS:
        raw, qere, segs = build(verse_element(wlc_dir, osis))
        text = raw.replace('/', '')
        cons = consonants(text + ' ' + ' '.join(q for _, q in qere))
        if any(st in cons for st in NAME_STEMS):
            sys.exit(f'refused: {osis} contains a Divine-Name stem')
        book, c, vv = osis.split('.')
        out.append({'ref': f'{book} {c}:{vv}', 'osis': osis, 'text': text, 'raw': raw,
                    'qere': qere, 'segs': segs, 'shows': shows})
    json.dump({'source': 'Westminster Leningrad Codex (public domain); adapted from the Open Scriptures Hebrew Bible, https://github.com/openscriptures/morphhb, CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)',
               'verses': out}, sys.stdout, ensure_ascii=False, indent=1)
    sys.stdout.write('\n')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
