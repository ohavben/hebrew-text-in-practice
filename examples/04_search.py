#!/usr/bin/env python3
"""Searching Hebrew: word characters, homographs, proclitics, both sides, positive controls, and full-text indexes.

Claims tested (section 4 of the resource):
  S1  In Python, \\w matches Hebrew letters but not the points, so \\w+ cuts a pointed word into pieces.
      (JavaScript: see 04_search.mjs.)
  S2  Stripped of its points, one consonant string is several words: list the matched tokens before counting.
  S5  Proclitics are written inside the word: an exact-word search misses them, a prefix pattern buys them back
      and brings in words that only look prefixed.
  S6  A bare query never meets pointed text until the text is stripped too.
  S7  A zero means nothing until the same search finds something you know is there.
  S9  SQLite FTS5's default tokenizer (unicode61) cuts pointed Hebrew at every point.
  S10 Geresh and gershayim are separators to it, and an ASCII double quote in an acronym is FTS5 query syntax.
  S11 The trigram tokenizer cannot find a term shorter than three characters.
  S12 A Hebrew proclitic glued to a Latin word becomes one token.
Run: python3 04_search.py
"""
import os, re, sqlite3, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import verses, check, show, done

V = verses()
FOLD = str.maketrans('ךםןףץ', 'כמנפצ')
def strip(s):
    s = ''.join(ch for ch in s if not unicodedata.category(ch).startswith('M'))
    return re.sub('[' + chr(0x5BE) + chr(0x5C0) + chr(0x5C3) + ']', ' ', s)

# --- S1: \w and the points -----------------------------------------------------------------------------------
w = V['Gen 2:25']['text'].split()[0]                         # the verse's first word, pointed
pieces = re.findall(r'\w+', w)
print('pointed word:', show(w), '\n  re.findall(r"\\w+") ->', [show(p) for p in pieces])
check('S1', r'\w+ returns the pointed word in pieces', len(pieces) > 1, True)
check('S1', r'\w+ on the stripped word returns it whole', re.findall(r'\w+', strip(w)), [strip(w)])

# --- S2: homographs after stripping --------------------------------------------------------------------------
pointed = ['דָּבָר', 'דֶּבֶר', 'דִּבֵּר', 'דְּבַר']               # word · plague · he spoke · word of (construct)
inventory = {}
for p in pointed:
    inventory.setdefault(strip(p), []).append(p)
print('\nfour pointed words ->', {k: len(v) for k, v in inventory.items()}, 'consonant string(s)')
check('S2', 'four different words, one stripped string', len(inventory), 1)

# --- S5: proclitics -------------------------------------------------------------------------------------------
text = ' '.join(strip(v['text']) for v in V.values()).translate(FOLD)
tokens = text.split()
exact = sum(t == 'ארצ' for t in tokens)
prefixed = [t for t in tokens if re.fullmatch('[והבכלמש]{0,3}ארצ', t)]
print(f'\n"ארץ" in the ten verses: exact {exact}; with up to three proclitics {len(prefixed)} {sorted(set(prefixed))}')
check('S5', 'the exact-word search misses the prefixed forms', exact < len(prefixed), True)
cands = ['כל', 'הכל', 'בכל', 'לכל', 'מכל', 'שכל']        # SYNTHETIC: the last is the noun "intellect", not ש + כל
hits = [t for t in cands if re.fullmatch('[והבכלמש]{0,3}כל', t)]
check('S5', 'the prefix pattern also takes in a word that only looks prefixed', 'שכל' in hits, True)

# --- S6: strip both sides --------------------------------------------------------------------------------------
raw = ' '.join(v['text'] for v in V.values())
check('S6', 'a bare query against the pointed text', raw.count('הארץ'), 0)
check('S6', 'the same query after stripping the text', strip(raw).count('הארץ'), 2)

# --- S7: a positive control ------------------------------------------------------------------------------------
control = 'מן'                                             # visibly present in Gen 2:6 ("from the land")
check('S7', 'the control phrase, searched the same broken way, also returns zero', raw.count(control), 0)
check('S7', 'and after stripping, the control is found', strip(raw).split().count(control) >= 1, True)

# --- S9..S12: SQLite FTS5 -------------------------------------------------------------------------------------
db = sqlite3.connect(':memory:')
print('\nSQLite', sqlite3.sqlite_version)
db.execute("CREATE VIRTUAL TABLE t USING fts5(x)")                               # default: unicode61
db.execute("CREATE VIRTUAL TABLE v USING fts5vocab(t, 'instance')")
g26 = V['Gen 2:6']['text']
db.execute('INSERT INTO t VALUES (?)', (g26,))
toks = [r[0] for r in db.execute('SELECT term FROM v ORDER BY doc, col, offset')]
one_letter = sum(len(x) == 1 for x in toks)
print(f'unicode61 tokens of pointed Gen 2:6: {len(toks)} (the verse has 9 words); one-letter tokens: {one_letter}')
print('  first ten:', toks[:10])
check('S9', 'unicode61 makes more tokens than the verse has words', len(toks) > 9, True)
check('S9', 'a bare word does not find the pointed verse', db.execute("SELECT count(*) FROM t WHERE t MATCH ?", ('הארץ',)).fetchone()[0], 0)

db.execute('DELETE FROM t')
db.execute('INSERT INTO t VALUES (?)', ('אמר ר׳ יוחנן',))                       # "Rabbi Yohanan said", with a geresh
toks = [r[0] for r in db.execute('SELECT term FROM v ORDER BY doc, col, offset')]
check('S10', 'the geresh is a separator: the abbreviation shrinks to its letter', toks, ['אמר', 'ר', 'יוחנן'])
try:
    db.execute("SELECT count(*) FROM t WHERE t MATCH ?", ('רש"י',)).fetchone()
    err = None
except sqlite3.OperationalError as e:
    err = str(e)
print('  MATCH \'רש"י\' ->', err)
check('S10', 'an acronym typed with an ASCII double quote is a query syntax error', err is not None, True)

db.execute('DELETE FROM t')
db.execute('INSERT INTO t VALUES (?)', ('ראיתי הcommit של אתמול',))           # "I saw the-commit of yesterday"
toks = [r[0] for r in db.execute('SELECT term FROM v ORDER BY doc, col, offset')]
check('S12', 'the article glued to a Latin word is one token', 'הcommit' in toks, True)

db.execute("CREATE VIRTUAL TABLE g USING fts5(x, tokenize='trigram')")
db.execute('INSERT INTO g VALUES (?)', ('האש והמים',))                           # "the fire and the water"
n2 = db.execute("SELECT count(*) FROM g WHERE g MATCH ?", ('אש',)).fetchone()[0]
n3 = db.execute("SELECT count(*) FROM g WHERE g MATCH ?", ('האש',)).fetchone()[0]
check('S11', 'trigram: a two-letter word is not found, a three-letter one is', (n2, n3), (0, 1))
done()
