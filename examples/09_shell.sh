#!/usr/bin/env bash
# Command-line tools and Hebrew (sections 9.5 and 10 of the resource; and, reported without checks, the font
# coverage of section 8.1 as fontconfig's fc-list gives it).
#   SH1  col -b (used by man-page pipelines) deletes Hebrew combining marks.
#   SH2  A GNU grep bracket range of Hebrew letters follows the locale: refused in C.utf8, letters in
#        en_US.utf8, raw bytes in POSIX (where it also matches a French line).
#   E5   One NUL byte makes grep treat a text file as binary; ripgrep reports it too.
#   SH4  wc -c counts bytes, wc -m characters (in a UTF-8 locale). Every code point of the Hebrew block
#        (U+0590..U+05FF: letters, points, te'amim, punctuation) is 2 bytes in UTF-8; the presentation forms
#        (U+FB1D..U+FB4F) are 3.
#   SH5  GNU cut -c counts characters in a UTF-8 locale from coreutils 9.11 on; up to 9.10, -c is the same as -b
#        (Fedora's and RHEL's builds of those versions carry a patch that counts characters). In C, bytes.
# Every command whose result depends on the locale names its locale (LC_ALL=...), so the caller's does not matter.
# A check whose tool or locale is missing is skipped, with a line that says so.
# Run: bash 09_shell.sh   (GNU grep, col, GNU coreutils, the C.UTF-8 and en_US.UTF-8 locales;
#                         ripgrep and fontconfig optional)
set -u
GREP="command grep"     # the real GNU grep, not a shell function or alias of the same name
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
pass=0; fail=0; nskip=0
check() {  # check TAG LABEL OBSERVED EXPECTED
  if [ "$3" = "$4" ]; then pass=$((pass+1)); echo "ok  [$1] $2: observed '$3'"
  else fail=$((fail+1)); echo "XX  [$1] $2: observed '$3' (expected '$4')"; fi
}
skipped() {  # skipped TAG LABEL REASON
  nskip=$((nskip+1)); echo "--  [$1] $2: skipped ($3)"
}
has_locale() { locale -a 2>/dev/null | $GREP -qixE "$1"; }       # has_locale 'en_US\.utf-?8'
c_utf8=no;  has_locale 'c\.utf-?8' && c_utf8=yes
en_utf8=no; has_locale 'en_US\.utf-?8' && en_utf8=yes
hex() { od -An -tx1 | tr -s ' \n' ' ' | sed 's/^ //; s/ $//'; }

word='שָׁלוֹם'          # shalom, with qamats, shin dot and holam: 4 letters + 3 points
plain='שלום'

# SH1 — col -b, in a UTF-8 locale (in the C locale col prints every byte of a Hebrew letter as an escape)
label="col -b on a pointed word returns the bare letters"
if ! command -v col >/dev/null; then skipped SH1 "$label" "no col: it is in util-linux, or in bsdextrautils on Debian and Ubuntu"
elif [ $c_utf8 = no ]; then skipped SH1 "$label" "the C.UTF-8 locale is not listed by locale -a"
else check SH1 "$label" "$(printf '%s\n' "$word" | LC_ALL=C.utf8 col -b)" "$plain"; fi

# SH2 — bracket ranges by locale: a range of Hebrew letters (alef..tav) against a Hebrew line and a French one
printf '%s\n' "$plain" 'café' > "$work/h.txt"
grep_range() {  # grep_range LOCALE INSTALLED WHAT EXPECTED   (the matched lines, joined by |)
  if [ "$2" = no ]; then skipped SH2 "$1: $3" "locale -a does not list $1: grep would fall back to bytes"; return; fi
  local n; n=$(LC_ALL=$1 $GREP -E '[א-ת]' "$work/h.txt" 2>&1 | tr '\n' '|')
  echo "    LC_ALL=$1  grep -E '[alef-tav]' -> $n"
  check SH2 "$1: $3" "$n" "$4"
}
grep_range C.utf8     $c_utf8  "the range is refused" "grep: Invalid collation character|"
grep_range en_US.utf8 $en_utf8 "only the Hebrew line" "$plain|"
grep_range POSIX      yes      "the range is bytes, and the French line matches too" "$plain|café|"

# E5 — a NUL byte (the message is the same in every locale; a relative file name keeps it the same on every run)
printf '%s\000%s\n' "$plain" 'עולם' > "$work/nul.txt"
check E5 "GNU grep on a file with one NUL" "$(cd "$work" && $GREP 'עולם' nul.txt 2>&1)" "grep: nul.txt: binary file matches"
check E5 "grep -a reads it as text" "$($GREP -a -c 'עולם' "$work/nul.txt")" "1"
if command -v rg >/dev/null; then
  r=$(cd "$work" && rg 'עולם' nul.txt 2>&1)
  echo "    ripgrep: $r"
  check E5 "ripgrep names the NUL" "$(case "$r" in *binary*) echo binary;; *) echo text;; esac)" "binary"
else
  skipped E5 "ripgrep names the NUL" "no rg: ripgrep is optional"
fi

# SH4 — bytes and characters
check SH4 "wc -c of the pointed word (bytes)" "$(printf '%s' "$word" | wc -c)" "14"
if [ $c_utf8 = yes ]; then
  check SH4 "wc -m in a UTF-8 locale (characters)" "$(printf '%s' "$word" | LC_ALL=C.utf8 wc -m)" "7"
  bytes_of() {  # bytes_of FIRST LAST: each code point written as UTF-8 by printf, counted by wc -c, summed by length
    ( export LC_ALL=C.utf8
      for ((cp=$1; cp<=$2; cp++)); do printf "\\U$(printf %08x "$cp")" | wc -c; done ) |
      sort -n | uniq -c | awk '{printf "%s%d of %d bytes", (NR>1?", ":""), $1, $2}'
  }
  check SH4 "every code point of the Hebrew block U+0590..U+05FF, in UTF-8" "$(bytes_of $((0x590)) $((0x5FF)))" "112 of 2 bytes"
  check SH4 "every code point of the presentation forms U+FB1D..U+FB4F, in UTF-8" "$(bytes_of $((0xFB1D)) $((0xFB4F)))" "51 of 3 bytes"
else
  for what in "wc -m in a UTF-8 locale (characters)" "every code point of the Hebrew block U+0590..U+05FF, in UTF-8" \
              "every code point of the presentation forms U+FB1D..U+FB4F, in UTF-8"; do
    skipped SH4 "$what" "the C.UTF-8 locale is not listed by locale -a"
  done
fi
check SH4 "wc -m in the C locale (bytes again)" "$(printf '%s' "$word" | LC_ALL=C wc -m)" "14"

# SH5 — cut -c, by locale and by version
cv=$(cut --version 2>/dev/null | head -1)
if [ "${cv#*GNU coreutils}" = "$cv" ]; then
  skipped SH5 "GNU cut -c1 in C.utf8" "this cut is not GNU coreutils"
  skipped SH5 "GNU cut -c1 in the C locale returns one byte" "this cut is not GNU coreutils"
else
  ver=${cv##* }; IFS=. read -r major minor _ <<< "$ver"; minor=${minor%%[!0-9]*}
  ids=" $($GREP -E '^(ID|ID_LIKE)=' /etc/os-release 2>/dev/null | cut -d= -f2 | tr -d '"' | tr '\n' ' ') "
  patched=no; case "$ids" in *" fedora "*|*" rhel "*) patched=yes;; esac       # Fedora, RHEL and their rebuilds
  if [ "${major:-0}" -lt 9 ] || { [ "${major:-0}" -eq 9 ] && [ "${minor:-0}" -le 10 ]; }; then
    if [ $patched = yes ]; then what="coreutils $ver, a Fedora or RHEL build: the whole letter"; want='d7 a9 0a'
    else what="coreutils $ver (9.10 or earlier: -c is -b): one byte"; want='d7 0a'; fi
  else what="coreutils $ver (9.11 or later): the whole letter"; want='d7 a9 0a'; fi
  cc=$(printf '%s\n' "$plain" | LC_ALL=C cut -c1 | hex)
  if [ $c_utf8 = yes ]; then
    cu=$(printf '%s\n' "$plain" | LC_ALL=C.utf8 cut -c1 | hex)
    echo "    cut -c1 of '$plain' -> C.utf8: $cu · C: $cc   (shin is d7 a9)"
    check SH5 "GNU cut -c1 in C.utf8, $what" "$cu" "$want"
  else
    skipped SH5 "GNU cut -c1 in C.utf8, $what" "the C.UTF-8 locale is not listed by locale -a"
  fi
  check SH5 "GNU cut -c1 in the C locale returns one byte" "$cc" "d7 0a"
fi

# Section 8.1 — which installed fonts have the te'amim, by fontconfig, for the families the page names.
# Reported, not checked: the installed fonts differ from system to system.
if command -v fc-list >/dev/null; then
  fc_has() { [ -n "$(fc-list ":family=$1${2:+:charset=$2}" family)" ] && echo yes || echo no; }   # fc_has FAMILY [HEX]
  echo "    $(fc-list --version 2>&1 | head -1), for the fonts of section 8.1: Hebrew letters (U+05D0) · etnachta (U+0591)"
  for fam in Arial 'Times New Roman' 'Courier New' 'DejaVu Sans' 'Open Sans' 'David CLM' 'Miriam CLM' 'Aharoni CLM' \
             'Noto Sans Hebrew' 'Noto Serif Hebrew' 'Ezra SIL' 'Keter YG' 'Frank Ruehl CLM' 'Liberation Sans' \
             'Liberation Serif' 'Liberation Mono'; do
    if [ "$(fc_has "$fam")" = no ]; then echo "      $fam: not installed"
    else echo "      $fam: letters $(fc_has "$fam" 5d0) · etnachta $(fc_has "$fam" 591)"; fi
  done
  echo "      families with U+0591: $(fc-list ':charset=591' family | sort -u | wc -l) · with U+0591 and U+05C3" \
       "(fc-list ':charset=591 5c3' family): $(fc-list ':charset=591 5c3' family | sort -u | wc -l)"
else
  echo "    no fc-list here: the font coverage of section 8.1 is not reported"
fi
echo "--- $pass of $((pass+fail)) checks as expected$( [ $fail -gt 0 ] && echo "; $fail NOT")$( [ $nskip -gt 0 ] && echo "; $nskip skipped")"
echo "$(command grep --version | head -1) · $(command -v col >/dev/null && col --version 2>&1 | head -1 || echo 'no col') · $(cut --version | head -1)$(command -v rg >/dev/null && echo " · $(rg --version | head -1)")"
[ $fail -eq 0 ]
