#!/usr/bin/env python3
"""Text sources: what the files actually contain.

Claims tested (section 5 of the resource):
  T1  The WLC XML (openscriptures/morphhb) writes "/" between the morphemes of a word, so a search over the raw
      text finds no word that carries a prefix or a suffix until the slash is removed.
  T3  Older Hebrew web pages are windows-1255: a UTF-8 search over the bytes finds nothing; and "mojibake" on
      screen can be good UTF-8 read through cp1255 — inspect the bytes before repairing anything.
  T5  Editions put the section markers (pe / samekh) into the text stream as tokens; a character-class cleaner
      that removes those letters destroys words, a whole-token filter does not.
  T6  At a ketiv/qere place the written and the read word differ; a single text field keeps one of them.
Run: python3 05_sources.py
"""
import os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import verses, check, show, done

V = verses()
def strip(s):
    s = ''.join(ch for ch in s if not unicodedata.category(ch).startswith('M'))
    return re.sub('[' + chr(0x5BE) + chr(0x5C0) + chr(0x5C3) + ']', ' ', s)

# --- T1: the morpheme slash --------------------------------------------------------------------------------
v = V['Gen 2:6']
print('Gen 2:6 raw (stripped):', strip(v['raw']))
print('Gen 2:6 text (stripped):', strip(v['text']))
check('T1', 'slashes inside the words of raw Gen 2:6', v['raw'].count('/'), 4)
check('T1', '"הארץ" (the land) in the raw text', strip(v['raw']).split().count('הארץ'), 0)
check('T1', '"הארץ" once the slash is removed', strip(v['text']).split().count('הארץ'), 1)

# --- T3: windows-1255 ---------------------------------------------------------------------------------------
page = 'בְּרֵאשִׁית'                                     # a pointed word, as a legacy page would store it
legacy = page.encode('cp1255')                          # windows-1255 has the points (not the te'amim)
print('\ncp1255 bytes:', legacy.hex(' '), '| UTF-8 bytes:', page.encode('utf-8').hex(' '))
check('T3', 'a UTF-8 needle in the cp1255 bytes', page.encode('utf-8') in legacy, False)
check('T3', 'the same bytes decoded as cp1255', legacy.decode('cp1255'), page)
try:
    legacy.decode('utf-8'); err = None
except UnicodeDecodeError as e:
    err = e.reason
print('  decoding the cp1255 bytes as UTF-8 fails with:', err)
check('T3', 'decoding them as UTF-8 fails', err is not None, True)
dash = '—'.encode('utf-8')                              # an em dash, correctly written as UTF-8
seen = dash.decode('cp1255', errors='replace')
print('an em dash, UTF-8 bytes', dash.hex(' '), 'read as cp1255 ->', seen, [f'U+{ord(c):04X}' for c in seen])
check('T3', 'good UTF-8 read through cp1255 shows gimel + euro sign + a quote mark', [f'{ord(c):04X}' for c in seen], ['05D2', '20AC', '201D'])
try:
    '֑'.encode('cp1255'); teamim = True
except UnicodeEncodeError:
    teamim = False
check('T3', "windows-1255 can carry the te'amim (U+0591 etnahta)", teamim, False)

# --- T5: section markers in the text stream --------------------------------------------------------------------
edition = strip(V['Exod 1:7']['text']).strip() + ' פ'      # how printed editions show "an open section ends here"
check('T5', 'Exod 1:7 ends a section in the WLC markup (seg x-pe)', 'x-pe' in V['Exod 1:7']['segs'], True)
by_class = re.sub('[פס]', '', edition)                     # the "clean the markers" mistake
by_token = ' '.join(t for t in edition.split() if t not in ('פ', 'ס'))
print('\nwith the marker:  ', edition)
print('class [פס] removed:', by_class)
print('token filter:      ', by_token)
check('T5', 'the class cleaner also deletes letters inside words', by_class.replace(' ', '') != by_token.replace(' ', ''), True)
check('T5', 'the token filter removes only the marker', len(by_token.split()), len(edition.split()) - 1)

# --- T6: ketiv and qere ------------------------------------------------------------------------------------------
k, q = V['Lev 9:22']['qere'][0]
print('\nLev 9:22 ketiv (written):', show(k), '| qere (read):', show(q))
check('T6', 'the written word is unpointed', any(unicodedata.category(c).startswith('M') for c in k), False)
check('T6', 'and its letters differ from the read word', strip(k).strip() == strip(q).strip(), False)
check('T6', 'the text field holds the written form only', (k in V['Lev 9:22']['text'], q in V['Lev 9:22']['text']), (True, False))
done()
