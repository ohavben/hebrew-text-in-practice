#!/usr/bin/env bash
# Command-line tools and Hebrew (section 10 of the resource).
#   SH1  col -b (used by man-page pipelines) deletes Hebrew combining marks.
#   SH2  A GNU grep bracket range of Hebrew letters follows the locale: refused in C.utf8, letters in
#        en_US.utf8, raw bytes in POSIX (where it also matches a French line).
#   E5   One NUL byte makes grep treat a text file as binary; ripgrep reports it too.
#   SH4  wc -c counts bytes, wc -m characters (in a UTF-8 locale); every Hebrew letter and point is 2 bytes.
#   SH5  GNU cut -c follows the locale: characters in a UTF-8 locale (coreutils 9.12), bytes in C.
# Run: bash 09_shell.sh          (GNU grep, util-linux col, GNU coreutils; ripgrep optional)
set -u
GREP="command grep"     # the real GNU grep, not a shell function or alias of the same name
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
pass=0; fail=0
check() {  # check TAG LABEL OBSERVED EXPECTED
  if [ "$3" = "$4" ]; then pass=$((pass+1)); echo "ok  [$1] $2: observed '$3'"
  else fail=$((fail+1)); echo "XX  [$1] $2: observed '$3' (expected '$4')"; fi
}
hex() { od -An -tx1 | tr -s ' \n' ' ' | sed 's/^ //; s/ $//'; }

word='שָׁלוֹם'          # shalom, with qamats, shin dot and holam: 4 letters + 3 points
plain='שלום'

# SH1 — col -b
out=$(printf '%s\n' "$word" | col -b)
check SH1 "col -b on a pointed word returns the bare letters" "$out" "$plain"

# SH2 — bracket ranges by locale: a range of Hebrew letters (alef..tav) against a Hebrew line and a French one
printf '%s\n' "$plain" 'café' > "$work/h.txt"
for loc in C.utf8 en_US.utf8 POSIX; do
  n=$(LC_ALL=$loc $GREP -E '[א-ת]' "$work/h.txt" 2>&1 | tr '\n' '|')
  echo "    LC_ALL=$loc  grep -E '[alef-tav]' -> $n"
  eval "r_${loc//./_}=\"\$n\""
done
check SH2 "C.utf8: the range is refused" "$r_C_utf8" "grep: Invalid collation character|"
check SH2 "en_US.utf8: only the Hebrew line" "$r_en_US_utf8" "$plain|"
check SH2 "POSIX: the range is bytes, and the French line matches too" "$r_POSIX" "$plain|café|"

# E5 — a NUL byte
printf '%s\000%s\n' "$plain" 'עולם' > "$work/nul.txt"
g=$($GREP 'עולם' "$work/nul.txt" 2>&1)
check E5 "GNU grep on a file with one NUL" "$g" "grep: $work/nul.txt: binary file matches"
ga=$($GREP -a -c 'עולם' "$work/nul.txt")
check E5 "grep -a reads it as text" "$ga" "1"
if command -v rg >/dev/null; then
  r=$(rg 'עולם' "$work/nul.txt" 2>&1)
  echo "    ripgrep: $r"
  check E5 "ripgrep names the NUL" "$(case "$r" in *binary*) echo binary;; *) echo text;; esac)" "binary"
fi

# SH4 — bytes and characters
check SH4 "wc -c of the pointed word (bytes)" "$(printf '%s' "$word" | wc -c)" "14"
check SH4 "wc -m in a UTF-8 locale (characters)" "$(printf '%s' "$word" | LC_ALL=C.utf8 wc -m)" "7"
check SH4 "wc -m in the C locale (bytes again)" "$(printf '%s' "$word" | LC_ALL=C wc -m)" "14"

# SH5 — cut -c, by locale
cu=$(printf '%s\n' "$plain" | LC_ALL=C.utf8 cut -c1 | hex)
cc=$(printf '%s\n' "$plain" | LC_ALL=C cut -c1 | hex)
echo "    cut -c1 of '$plain' -> C.utf8: $cu · C: $cc   (shin is d7 a9)"
check SH5 "GNU cut -c1 in C.utf8 returns the whole letter" "$cu" "d7 a9 0a"
check SH5 "GNU cut -c1 in the C locale returns one byte" "$cc" "d7 0a"
echo "--- $pass of $((pass+fail)) checks as expected$( [ $fail -gt 0 ] && echo "; $fail NOT")"
echo "$(command grep --version | head -1) · $(col --version 2>&1 | head -1) · $(cut --version | head -1)"
[ $fail -eq 0 ]
