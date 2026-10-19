# The examples

Each script measures the claims of one section of the [main page](../README.md) and prints one line per check:
`ok` when the observation is what the page says, `XX` when it is not, and a count at the end. The exit status is 0
only when every check passed.

| script | section | needs |
|---|---|---|
| [`01_layers.py`](01_layers.py) | 1 · the layers of a string, the one-range trap, U+05C0, U+05C4, U+05BC | Python 3 |
| [`02_finals.py`](02_finals.py) | 2 · final forms | Python 3 |
| [`03_normalization.py`](03_normalization.py) | 3 · NFC and the points, CGJ, presentation forms, foreign marks | Python 3 |
| [`04_search.py`](04_search.py) | 4 · `\w`, homographs, prefixes, positive controls, SQLite FTS5 | Python 3 (with SQLite FTS5) |
| [`04_search.mjs`](04_search.mjs) | 4.1 · `\b` and `\w` in JavaScript | Node.js |
| [`05_sources.py`](05_sources.py) | 5 · the WLC slash, section markers, windows-1255, ketiv/qere | Python 3 |
| [`06_bidi.py`](06_bidi.py) | 6 · the bidi algorithm, measured with GNU FriBidi | Python 3, `fribidi` |
| [`07_html/measure_layout.py`](07_html/measure_layout.py) | 6 · the same lines laid out by Chromium, compared with FriBidi | Python 3, `fribidi`, Chromium |
| [`07_html/make_pages.py`](07_html/make_pages.py) | 7, 8 · test pages and screenshots | Python 3, Chromium |
| [`07_html/fonts_used.mjs`](07_html/fonts_used.mjs) | 8.2 · which fonts Chromium used (`--no-lang` for the other half) | Node.js 22+, Chromium |
| [`08_invisible.py`](08_invisible.py) | 9 · invisible characters, Hebrew as escape text | Python 3 |
| [`08_invisible.mjs`](08_invisible.mjs) | 9.3 · U+2028 in JSON lines | Node.js |
| [`09_shell.sh`](09_shell.sh) | 9.5, 10 · NUL bytes, `col`, `grep` ranges, `wc`, `cut` | bash, GNU grep, util-linux, coreutils |
| [`10_policy.py`](10_policy.py) | 11.2 · masking a word in pointed text | Python 3 |
| [`corpus/corpus_checks.py`](corpus/corpus_checks.py) | 1, 2, 3, 5 · whole-Bible counts | Python 3 and a [morphhb](https://github.com/openscriptures/morphhb) checkout |

`bash run_all.sh` runs them all and writes each output to [`outputs/`](outputs/); add the path of a morphhb `wlc`
folder to include the whole-corpus counts. [`outputs/ENVIRONMENT.txt`](outputs/ENVIRONMENT.txt) records the
versions the published outputs came from. Results on other systems (other fonts, other browsers, other versions of
grep or SQLite) may differ; that is the point of keeping the scripts.

The verses are in [`data/verses.json`](data/verses.json), built by [`data/build_data.py`](data/build_data.py) from
the Westminster Leningrad Codex as published by the Open Scriptures Hebrew Bible (text in the public domain, markup
CC BY 4.0). Every verse there contains no Divine Name.

No script writes a control character or an invisible character into a file as a raw character: every such character
is built at run time from its code point, and printed as `U+XXXX`. Visual-order lines are printed in ASCII, with
Hebrew letters as capitals, so that no terminal or viewer can reorder them a second time.
