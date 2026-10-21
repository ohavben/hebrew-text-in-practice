#!/usr/bin/env node
// JavaScript regular expressions and Hebrew (section 4, claim S1).
//   S1  \b and \w are ASCII-only in JavaScript — with and without the u flag — so \b never fires next to a
//       Hebrew letter. A Unicode-aware boundary has to be written with lookarounds over \p{L} and \p{M}.
// Run: node 04_search.mjs
import { readFileSync } from "node:fs";

const verses = JSON.parse(readFileSync(new URL("./data/verses.json", import.meta.url), "utf8")).verses;
const results = [];
const check = (tag, label, observed, expected) => {
  const ok = JSON.stringify(observed) === JSON.stringify(expected);
  results.push(ok);
  console.log(`${ok ? "ok " : "XX "}[${tag}] ${label}: observed ${JSON.stringify(observed)}${ok ? "" : `  (expected ${JSON.stringify(expected)})`}`);
};

const s = "אך זה הדבר";                                         // SYNTHETIC: "but this is the thing"
check("S1", "/^אך\\b/ on a Hebrew sentence", /^אך\b/.test(s), false);
check("S1", "/^אך\\b/u (the u flag does not change \\b)", /^אך\b/u.test(s), false);
check("S1", "/\\w/ matches a Hebrew letter", /\w/.test("א"), false);
check("S1", "/^אך(?=\\s|$)/ — an explicit boundary instead", /^אך(?=\s|$)/.test(s), true);

// a Unicode boundary: not preceded / followed by a letter or a mark
const word = (w) => new RegExp(`(?<![\\p{L}\\p{M}])${w}(?![\\p{L}\\p{M}])`, "u");
check("S1", "Unicode-aware boundary finds the whole word", word("זה").test(s), true);
check("S1", "and does not match inside a longer word", word("דב").test(s), false);

// on pointed text: the points are \p{M}, so the boundary must allow them inside the word
const g = verses.find((v) => v.ref === "Gen 2:25").text;
const first = g.split(" ")[0];
check("S1", "\\b-delimited \\w+ finds no word in pointed Gen 2:25", (g.match(/\b\w+\b/g) || []).length, 0);
check("S1", "[\\p{L}\\p{M}]+ returns the pointed word whole", g.match(/[\p{L}\p{M}]+/u)[0] === first, true);

// F2 (section 2.2): the boundary after a folded query. Strip the points (category Mn) and the maqaf stays: a
// whitespace lookahead misses the word before it, a lookahead that refuses a following letter or mark does not.
const FINALS = new RegExp("[" + String.fromCodePoint(0x5DA, 0x5DD, 0x5DF, 0x5E3, 0x5E5) + "]", "g");
const fold = (t) => t.replace(FINALS, (c) => String.fromCodePoint(c.codePointAt(0) + 1));   // final form -> medial form
const g26 = fold(verses.find((v) => v.ref === "Gen 2:6").text.replace(/\p{Mn}/gu, ""));
const from = fold(String.fromCodePoint(0x5DE, 0x5DF));                                         // "from", folded
const count = (look) => (g26.match(new RegExp(from + look, "gu")) || []).length;
check("F2", "Gen 2:6 without its points (the maqaf kept): the folded query \"from\" followed by (?![\\p{L}\\p{M}])", count("(?![\\p{L}\\p{M}])"), 1);
check("F2", "the same query followed by a whitespace lookahead (?!\\S)", count("(?!\\S)"), 0);

const bad = results.filter((x) => !x).length;
console.log(`--- ${results.length - bad} of ${results.length} checks as expected${bad ? `; ${bad} NOT` : ""}`);
console.log(`node ${process.version}, ICU ${process.versions.icu}, Unicode ${process.versions.unicode}`);
process.exit(bad ? 1 : 0);
