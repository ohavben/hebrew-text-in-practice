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

const bad = results.filter((x) => !x).length;
console.log(`--- ${results.length - bad} of ${results.length} checks as expected${bad ? `; ${bad} NOT` : ""}`);
console.log(`node ${process.version}, ICU ${process.versions.icu}, Unicode ${process.versions.unicode}`);
process.exit(bad ? 1 : 0);
