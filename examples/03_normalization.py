#!/usr/bin/env python3
"""Normalization: mark order, presentation forms, and marks from other scripts.

Claims tested (section 3 of the resource):
  N1  Unicode normalization puts Hebrew points into canonical-combining-class order (vowels before dagesh, the
      shin dot after the vowel), so pointed text from one source rarely equals the same text from another byte
      for byte. Compare normalized forms; store and hash the bytes as written. Two vowels on one letter are
      swapped by NFC unless a COMBINING GRAPHEME JOINER (U+034F) stands between them.
  N2  Presentation forms (U+FB1D..U+FB4F) look like pointed letters but are other code points; NFC decomposes
      most of them, NFKC is needed for the rest.
  N3  A combining mark from another script on a Hebrew letter survives a Hebrew-only strip.
Run: python3 03_normalization.py
"""
import hashlib, os, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import verses, check, show, done

V = verses()
NFC = lambda s: unicodedata.normalize('NFC', s)
NFD = lambda s: unicodedata.normalize('NFD', s)

# --- N1: the classes ---------------------------------------------------------------------------------------
for c in (0x5B0, 0x5B4, 0x5B7, 0x5B8, 0x5BC, 0x5BD, 0x5C1, 0x5C2, 0x591, 0x5A3):
    ch = chr(c)
    print(f'  U+{c:04X} {unicodedata.name(ch):34s} combining class {unicodedata.combining(ch)}')

words = [w for v in V.values() for w in v['text'].replace(chr(0x5BE), ' ').split()]
changed = [w for w in words if NFC(w) != w]
print(f'\nwords in the ten verses: {len(words)}; changed by NFC: {len(changed)}; changed by NFD: {sum(NFD(w) != w for w in words)}')
w = next(w for w in changed if chr(0x5BC) in w)
print('  stored:', show(w))
print('  NFC:   ', show(NFC(w)))
check('N1', 'NFC changes some WLC words', len(changed) > 0, True)
check('N1', 'NFC and NFD agree here (no Hebrew precomposed letters in the stored text)', all(NFC(w) == NFD(w) for w in words), True)

# two spellings of one pointed syllable: dagesh then qamats, and qamats then dagesh
a = 'כ' + chr(0x5BC) + chr(0x5B8)
b = 'כ' + chr(0x5B8) + chr(0x5BC)
check('N1', 'the two orders are different strings', a == b, False)
check('N1', 'and the same string after NFC', NFC(a) == NFC(b), True)
s = V['Gen 2:25']['text']
h1, h2 = hashlib.sha256(s.encode()).hexdigest()[:12], hashlib.sha256(NFC(s).encode()).hexdigest()[:12]
print(f'\nGen 2:25 sha256 as written {h1} · after NFC {h2}')
check('N1', 'normalizing before hashing changes the hash (store and hash the bytes as written)', h1 == h2, False)

# two vowels on one letter (Jerusalem's lamed carries patah + hiriq): NFC swaps them; a CGJ between them stops it
CGJ = chr(0x34F)
lamed = 'ל' + chr(0x5B7) + chr(0x5B4)                       # lamed + patah + hiriq, in the Masoretic order
check('N1', 'NFC puts the hiriq before the patah', NFC(lamed), 'ל' + chr(0x5B4) + chr(0x5B7))
check('N1', 'with a COMBINING GRAPHEME JOINER between them, NFC keeps the order', NFC('ל' + chr(0x5B7) + CGJ + chr(0x5B4)), 'ל' + chr(0x5B7) + CGJ + chr(0x5B4))

# --- N2: presentation forms ---------------------------------------------------------------------------------
for c in (0xFB2A, 0xFB35, 0xFB4B, 0xFB21, 0xFB4F):
    ch = chr(c)
    print(f'  U+{c:04X} {unicodedata.name(ch):40s} NFC -> {show(NFC(ch)):14s} NFKC -> {show(unicodedata.normalize("NFKC", ch))}')
check('N2', 'U+FB2A (shin with shin dot) is not the letter shin', chr(0xFB2A) == 'ש' + chr(0x5C1), False)
check('N2', 'NFC decomposes U+FB2A to shin + shin dot', NFC(chr(0xFB2A)), 'ש' + chr(0x5C1))
check('N2', 'NFC leaves the wide alef U+FB21 alone; NFKC maps it to alef', (NFC(chr(0xFB21)), unicodedata.normalize('NFKC', chr(0xFB21))), (chr(0xFB21), 'א'))
check('N2', 'the alef-lamed ligature U+FB4F needs NFKC', (NFC(chr(0xFB4F)) == chr(0xFB4F), unicodedata.normalize('NFKC', chr(0xFB4F))), (True, 'אל'))

# --- N3: a mark from another script ---------------------------------------------------------------------
odd = 'ש' + chr(0x307) + 'לום'            # a COMBINING DOT ABOVE (Latin/Greek) on a Hebrew letter
hebrew_strip = ''.join(ch for ch in odd if not 0x591 <= ord(ch) <= 0x5C7)
print('\nwith a foreign mark:', show(odd), '-> Hebrew-range strip ->', show(hebrew_strip))
check('N3', 'a Hebrew-range strip leaves U+0307 in place', chr(0x307) in hebrew_strip, True)
check('N3', 'so the word does not equal its plain spelling', hebrew_strip == 'שלום', False)
check('N3', 'a category strip (all marks) removes it', ''.join(ch for ch in odd if not unicodedata.category(ch).startswith('M')), 'שלום')
done()
