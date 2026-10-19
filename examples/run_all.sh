#!/usr/bin/env bash
# Run every example and keep its output in outputs/<name>.txt. Exit status: 0 only if every example passed.
#   bash run_all.sh                 the examples (need python3; node, fribidi and chromium for some)
#   bash run_all.sh <morphhb/wlc>   also the whole-corpus checks
set -u
export PYTHONDONTWRITEBYTECODE=1     # no __pycache__ beside the examples
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$here/outputs"
status=0
run() {  # run NAME COMMAND...
  local name=$1; shift
  if "$@" > "$here/outputs/$name.txt" 2>&1; then echo "pass  $name"; else echo "FAIL  $name   (outputs/$name.txt)"; status=1; fi
}
run 01_layers        python3 "$here/01_layers.py"
run 02_finals        python3 "$here/02_finals.py"
run 03_normalization python3 "$here/03_normalization.py"
run 04_search_py     python3 "$here/04_search.py"
command -v node >/dev/null && run 04_search_mjs node "$here/04_search.mjs"
run 05_sources       python3 "$here/05_sources.py"
command -v fribidi >/dev/null && run 06_bidi python3 "$here/06_bidi.py"
if command -v chromium >/dev/null || command -v chromium-browser >/dev/null || command -v google-chrome >/dev/null; then
  command -v fribidi >/dev/null && run 07_measure_layout python3 "$here/07_html/measure_layout.py"
  command -v node >/dev/null && run 07_fonts_used node "$here/07_html/fonts_used.mjs"
  command -v node >/dev/null && run 07_fonts_used_no_lang node "$here/07_html/fonts_used.mjs" --no-lang
fi
run 08_invisible_py  python3 "$here/08_invisible.py"
command -v node >/dev/null && run 08_invisible_mjs node "$here/08_invisible.mjs"
run 09_shell         bash "$here/09_shell.sh"
run 10_policy        python3 "$here/10_policy.py"
[ $# -ge 1 ] && run corpus_checks python3 "$here/corpus/corpus_checks.py" "$1"
{ echo "python: $(python3 --version 2>&1)"; command -v node >/dev/null && echo "node: $(node --version)";
  command -v fribidi >/dev/null && echo "fribidi: $(fribidi --version | head -1)";
  for c in chromium chromium-browser google-chrome; do command -v $c >/dev/null && echo "browser: $($c --version)" && break; done
  echo "sqlite: $(python3 -c 'import sqlite3; print(sqlite3.sqlite_version)')"; echo "unicodedata: $(python3 -c 'import unicodedata; print(unicodedata.unidata_version)')";
  echo "os: $(uname -sr)"; } > "$here/outputs/ENVIRONMENT.txt"
exit $status
