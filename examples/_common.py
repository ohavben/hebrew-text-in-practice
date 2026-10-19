"""Shared helpers for the examples: load the verses, print a check, and count the results."""
import json, os, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
_results = []

def verses():
    with open(os.path.join(HERE, 'data', 'verses.json'), encoding='utf-8') as f:
        return {v['ref']: v for v in json.load(f)['verses']}

def cp(ch):
    """A character as U+XXXX NAME — the only safe way to print an invisible or combining character."""
    return f'U+{ord(ch):04X} {unicodedata.name(ch, "<unnamed>")}'

def show(s):
    """A string with every non-letter Hebrew character spelled out, so marks and controls are visible."""
    out = []
    for ch in s:
        o = ord(ch)
        if 0x5D0 <= o <= 0x5EA or ch == ' ' or (0x20 < o < 0x7F):
            out.append(ch)
        else:
            out.append('{' + f'{o:04X}' + '}')
    return ''.join(out)

def check(tag, label, observed, expected):
    ok = observed == expected
    _results.append(ok)
    mark = 'ok ' if ok else 'XX '
    print(f'{mark}[{tag}] {label}: observed {observed!r}' + ('' if ok else f'  (expected {expected!r})'))
    return ok

def done():
    n, bad = len(_results), _results.count(False)
    print(f'--- {n - bad} of {n} checks as expected' + ('' if not bad else f'; {bad} NOT'))
    sys.exit(1 if bad else 0)
