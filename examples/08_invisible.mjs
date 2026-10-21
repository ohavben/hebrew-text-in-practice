#!/usr/bin/env node
// U+2028 / U+2029 in a JSON-lines stream (section 9, claim E3).
//   JSON.stringify leaves U+2028 LINE SEPARATOR and U+2029 PARAGRAPH SEPARATOR raw (they are valid JSON).
//   From Node.js 24 on, readline ends a line at them, so one record is read as two broken lines and neither
//   parses. Node.js 23 and earlier end a line only at a line feed or a carriage return: the record comes back
//   whole. Each check says which version ran and what that version is expected to do.
// Run: node 08_invisible.mjs
import { createInterface } from "node:readline";
import { Readable } from "node:stream";

const major = Number(process.versions.node.split(".")[0]);
const splits = major >= 24;                  // Node.js 24 added U+2028 and U+2029 to readline's line ends
const [wantLines, wantParsed] = splits ? [2, 0] : [1, 1];
const results = [];
for (const cp of [0x2028, 0x2029]) {
  const sep = String.fromCodePoint(cp);
  const record = JSON.stringify({ text: "שורה" + sep + "המשך" });       // "line" + separator + "continuation"
  const lines = [];
  const rl = createInterface({ input: Readable.from([record + "\n"]), crlfDelay: Infinity });
  for await (const line of rl) lines.push(line);
  let parsed = 0;
  for (const l of lines) { try { JSON.parse(l); parsed++; } catch { /* a broken half */ } }
  const ok = record.includes(sep) && lines.length === wantLines && parsed === wantParsed;
  results.push(ok);
  console.log(`${ok ? "ok " : "XX "}[E3] U+${cp.toString(16).toUpperCase()} in one JSON record: written raw ${record.includes(sep)} · ` +
    `lines read back by readline ${lines.length} · lines that parse ${parsed}` +
    ` (Node ${major}: expected ${wantLines} and ${wantParsed}; ${splits ? "from Node 24 on, readline ends a line there" : "before Node 24, readline does not end a line there"})`);
}
const bad = results.filter((x) => !x).length;
console.log(`--- ${results.length - bad} of ${results.length} checks as expected${bad ? `; ${bad} NOT` : ""}`);
console.log(`node ${process.version}`);
process.exit(bad ? 1 : 0);
