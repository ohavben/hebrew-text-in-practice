#!/usr/bin/env bash
# Run every example except 07_html/make_pages.py (which rewrites the committed pages and screenshots: run it by hand)
# and write its output to outputs/<name>.txt, over the published copy: in a git clone, `git diff outputs/` then
# shows what came out differently here, and `git checkout outputs/` restores it. An example whose tool is missing is
# skipped with a "skip" line, and its published output stays in place. Each line ends with the example's own count
# of checks; the last line adds them up. Exit status: 0 only if every example that ran passed.
#   bash run_all.sh                 the examples (need python3; node, fribidi and chromium for some)
#   bash run_all.sh <morphhb/wlc>   also the whole-corpus checks
set -u
export PYTHONDONTWRITEBYTECODE=1     # no __pycache__ beside the examples
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$here/outputs"
has() { command -v "$1" >/dev/null; }
has python3 || { echo "the examples need python3"; exit 2; }
browser=; for c in chromium chromium-browser google-chrome; do has $c && { browser=$c; break; }; done
status=0; ran=0; skipped=0; good=0; total=0
run() {  # run NAME COMMAND...
  local name=$1 result count; shift
  if "$@" > "$here/outputs/$name.txt" 2>&1; then result=pass; else result=FAIL; status=1; fi
  ran=$((ran+1))
  count=$(command grep -E '^--- [0-9]+ of [0-9]+ checks' "$here/outputs/$name.txt" | tail -1)
  if [[ $count =~ ^---\ ([0-9]+)\ of\ ([0-9]+) ]]; then good=$((good+BASH_REMATCH[1])); total=$((total+BASH_REMATCH[2])); fi
  printf '%-5s %-34s %s\n' "$result" "$name" "${count:-(no count line: see outputs/$name.txt)}"
}
skip() {  # skip NAME REASON
  skipped=$((skipped+1))
  printf 'skip  %-34s (%s; outputs/%s.txt is still the published one)\n' "$1" "$2" "$1"
}
run 01_layers        python3 "$here/01_layers.py"
run 02_finals        python3 "$here/02_finals.py"
run 03_normalization python3 "$here/03_normalization.py"
run 04_search_py     python3 "$here/04_search.py"
if has node; then run 04_search_mjs node "$here/04_search.mjs"; else skip 04_search_mjs "needs node"; fi
run 05_sources       python3 "$here/05_sources.py"
if has fribidi; then run 06_bidi python3 "$here/06_bidi.py"; else skip 06_bidi "needs fribidi"; fi
if [ -n "$browser" ] && has fribidi; then run 07_measure_layout python3 "$here/07_html/measure_layout.py"
else skip 07_measure_layout "needs chromium and fribidi"; fi
for option in "" --no-lang --no-user-fontconfig; do     # 07_fonts_used, 07_fonts_used_no_lang, ..._no_user_fontconfig
  name=07_fonts_used${option:+_${option#--}}; name=${name//-/_}
  if [ -n "$browser" ] && has node; then run "$name" node "$here/07_html/fonts_used.mjs" ${option:+"$option"}
  else skip "$name" "needs chromium and node"; fi
done
run 08_invisible_py  python3 "$here/08_invisible.py"
if has node; then run 08_invisible_mjs node "$here/08_invisible.mjs"; else skip 08_invisible_mjs "needs node"; fi
run 09_shell         bash "$here/09_shell.sh"
run 10_policy        python3 "$here/10_policy.py"
if [ $# -ge 1 ]; then run corpus_checks python3 "$here/corpus/corpus_checks.py" "$1"
else skip corpus_checks "give the path of a morphhb wlc folder"; fi
echo "--- $good of $total checks as expected, in $ran examples$( [ $skipped -gt 0 ] && echo "; $skipped skipped")"
locale_listed() { locale -a 2>/dev/null | command grep -qixE "$1" && echo listed || echo 'not listed'; }
{ echo "python: $(python3 --version 2>&1)"; has node && echo "node: $(node --version)";
  has fribidi && echo "fribidi: $(fribidi --version | head -1)";
  [ -n "$browser" ] && echo "browser: $($browser --version)";
  echo "sqlite: $(python3 -c 'import sqlite3; print(sqlite3.sqlite_version)')"; echo "unicodedata: $(python3 -c 'import unicodedata; print(unicodedata.unidata_version)')";
  echo "grep: $(command grep --version | head -1)"; echo "coreutils: $(cut --version 2>&1 | head -1)";
  has col && echo "col: $(col --version 2>&1 | head -1)"; has rg && echo "ripgrep: $(rg --version | head -1)";
  echo "locale: charmap $(locale charmap 2>/dev/null) · C.UTF-8 $(locale_listed 'c\.utf-?8') · en_US.UTF-8 $(locale_listed 'en_US\.utf-?8') (locale -a)";
  has fc-list && echo "fontconfig: $(fc-list --version 2>&1 | head -1) · sans-serif for lang=he: $(fc-match -f '%{family}' 'sans-serif:lang=he' 2>/dev/null)";
  f=$(cd "${XDG_CONFIG_HOME:-$HOME/.config}/fontconfig" 2>/dev/null && ls -d fonts.conf conf.d/* 2>/dev/null | paste -sd' ' -)
  echo "user fontconfig files: ${f:-none}";
  echo "os: $(uname -sr)"; } > "$here/outputs/ENVIRONMENT.txt"
exit $status
