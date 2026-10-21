# The examples

Each script measures the claims of one or more sections of the [main page](../README.md) and prints one line per
check: `ok` when the observation is what the page says, `XX` when it is not, and a count at the end. The exit status
is 0 only when every check passed. A check that cannot run on your system (a tool, a locale or a font is missing)
prints a line that begins with `--` and says why, and is not counted. One script has no checks:
[`07_html/make_pages.py`](07_html/make_pages.py) builds the test pages and their screenshots, to be looked at.

| script | section | needs |
|---|---|---|
| [`01_layers.py`](01_layers.py) | 1 · the layers of a string, the one-range trap, U+05C0, U+05C4, U+05BC, the tagin | Python 3 |
| [`02_finals.py`](02_finals.py) | 2 · final forms, the word-end boundary | Python 3 |
| [`03_normalization.py`](03_normalization.py) | 3 · NFC and the points, combining classes, CGJ, presentation forms, foreign marks | Python 3 |
| [`04_search.py`](04_search.py) | 4 · `\w`, homographs, prefixes, positive controls, SQLite FTS5 | Python 3 (with SQLite FTS5) |
| [`04_search.mjs`](04_search.mjs) | 2.2, 4.1 · `\b`, `\w` and the word-end boundary in JavaScript | Node.js |
| [`05_sources.py`](05_sources.py) | 5 · the WLC slash, section markers, windows-1255, ketiv/qere | Python 3 |
| [`06_bidi.py`](06_bidi.py) | 6 · the bidi algorithm, measured with GNU FriBidi | Python 3, `fribidi` |
| [`07_html/measure_layout.py`](07_html/measure_layout.py) | 6 · the same lines laid out by Chromium, compared with FriBidi | Python 3, `fribidi`, Chromium |
| [`07_html/make_pages.py`](07_html/make_pages.py) | 6.5, 7, 8 · test pages and screenshots; no checks, and not run by `run_all.sh` | Python 3, Chromium |
| [`07_html/fonts_used.mjs`](07_html/fonts_used.mjs) | 8.2 · which fonts Chromium used (`--no-lang` for the other half; `--no-user-fontconfig` leaves out the user's own fontconfig rules) | Node.js 22 or later, Chromium; fontconfig's `fc-list` for the checks |
| [`08_invisible.py`](08_invisible.py) | 9 · invisible characters, Hebrew as escape text | Python 3 |
| [`08_invisible.mjs`](08_invisible.mjs) | 9.3 · U+2028 and U+2029 in JSON lines | Node.js |
| [`09_shell.sh`](09_shell.sh) | 9.5, 10 · NUL bytes, `col`, `grep` ranges, `wc`, `cut`, bytes per character; 8.1 · which fonts have the te'amim, by `fc-list` (reported, not checked) | bash, GNU grep, GNU coreutils, `col` (in util-linux; in the `bsdextrautils` package on Debian and Ubuntu), the `C.UTF-8` and `en_US.UTF-8` locales; ripgrep and fontconfig optional |
| [`10_policy.py`](10_policy.py) | 11.2 · masking a word in pointed text | Python 3 |
| [`corpus/corpus_checks.py`](corpus/corpus_checks.py) | 1–5, 12 · whole-Bible counts | Python 3 and a [morphhb](https://github.com/openscriptures/morphhb) checkout |

Three results depend on the version of a tool, and the checks that measure them say which version ran and what that
version is expected to do:

- Node.js's `readline` ends a line at U+2028 and U+2029 from Node.js 24 on; Node.js 23 and earlier return the record
  whole (measured with Node.js 20, 22, 23, 24.0 and 26).
- GNU `cut -c` counts characters in a UTF-8 locale from coreutils 9.11 on; up to 9.10, `-c` is the same as `-b`.
  Fedora's and RHEL's builds of older versions count characters too (measured with 9.1 and 9.10 on Debian, 9.10 on
  Fedora, 8.32 on Rocky Linux, 9.11 on Alpine, and 9.12 in the published run).
- The `fribidi` command ignores `--nomirror` and `--reordernsm` before FriBidi 1.0.17: it always mirrors and always
  moves each mark after its letter, so the order without rule L3 cannot be shown with it (measured with 1.0.8,
  1.0.16 and 1.0.17). Every other check of `06_bidi.py` and `measure_layout.py` passed with all three.

`bash run_all.sh` runs every script except `07_html/make_pages.py` (it rewrites the committed pages and screenshots:
run it by hand) and writes each output to [`outputs/`](outputs/), over the published one: in a git clone,
`git diff outputs/` shows what came out differently on your system, and `git checkout outputs/` restores ours. Each
line ends with the script's own count of checks, and the last line adds them up. A script whose tool is missing is
skipped with a `skip` line, and its published output stays in place. Add the path of a morphhb `wlc` folder to
include the whole-corpus counts. [`outputs/ENVIRONMENT.txt`](outputs/ENVIRONMENT.txt) records the versions the
outputs came from: as published, those of our system (our own fontconfig rules included); after a run, yours.
Results on other systems (other fonts, other browsers, other versions of grep or SQLite) may differ; that is the
point of keeping the scripts. In a Docker container, Chromium started only with `--no-sandbox` (as root and as an
ordinary user); on Debian, add it with
`echo 'export CHROMIUM_FLAGS="$CHROMIUM_FLAGS --no-sandbox"' > /etc/chromium.d/no-sandbox`.

Each check line carries a tag, such as `[SH2]`. The tags are listed, each with the claim it tests, at the top of the
script that prints them; they are numbered across the whole page, so a script shows only the ones it measures, and
some numbers are not used.

| tags | section of the main page | scripts |
|---|---|---|
| U1–U4, U6 | 1 · the layers of a string | `01_layers.py`; U2 and U3 also `corpus_checks.py` |
| F1–F4 | 2 · final forms | `02_finals.py`; F2 also `04_search.mjs`, F4 `corpus_checks.py` |
| N1–N3 | 3 · normalization and byte identity | `03_normalization.py`; N1 also `corpus_checks.py` |
| S1–S13 | 4 · searching Hebrew | `04_search.py`, `04_search.mjs` (S1); S13 `corpus_checks.py` |
| T1–T7 | 5 · text sources | `05_sources.py`; T1, T5, T6 and T7 also `corpus_checks.py` |
| B0–B6, NSM, ISO, X | 6 · direction | `06_bidi.py`; ISO and X `measure_layout.py` |
| FO1 | 8.2 · fonts | `fonts_used.mjs` |
| E2–E5 | 9 · invisible characters and escapes | `08_invisible.py`, `08_invisible.mjs` (E3), `09_shell.sh` (E5) |
| SH1–SH5 | 10 · command-line tools | `09_shell.sh` |
| D2a–D2d | 11.2 · masking a word | `10_policy.py` |
| C1 | 12 · costs: bytes | `corpus_checks.py` |

The verses are in [`data/verses.json`](data/verses.json), built by [`data/build_data.py`](data/build_data.py) from
the Westminster Leningrad Codex as published by the Open Scriptures Hebrew Bible (text in the public domain, markup
CC BY 4.0). Every verse there contains no Divine Name.

No script writes a control character or an invisible character into a file as a raw character: every such character
is built at run time from its code point, and printed as `U+XXXX`. Visual-order lines are printed in ASCII, with
Hebrew letters as capitals, so that no terminal or viewer can reorder them a second time.

The source code in this directory (the `.py`, `.mjs` and `.sh` files) is licensed under the MIT License
([`LICENSE`](LICENSE)); everything else here is covered by the page's CC BY 4.0, and the verses keep their sources'
terms (above).
