#!/usr/bin/env node
// U+2028 / U+2029 in a JSON-lines stream (section 9, claim E3).
//   JSON.stringify leaves U+2028 LINE SEPARATOR raw (it is valid JSON), and Node's readline ends a line at it,
//   so one record is read as two broken lines.
// Run: node 08_invisible.mjs
import { createInterface } from "node:readline";
import { Readable } from "node:stream";

const LS = String.fromCodePoint(0x2028);
const record = JSON.stringify({ text: "שורה" + LS + "המשך" });       // "line" + LS + "continuation"
console.log("JSON.stringify leaves U+2028 raw:", record.includes(LS));

const lines = [];
const rl = createInterface({ input: Readable.from([record + "\n"]), crlfDelay: Infinity });
for await (const line of rl) lines.push(line);
console.log("records written: 1 · lines read back by readline:", lines.length);
let parsed = 0;
for (const l of lines) { try { JSON.parse(l); parsed++; } catch { /* a broken half */ } }
console.log("lines that parse as JSON:", parsed);
const ok = record.includes(LS) && lines.length === 2 && parsed === 0;
console.log(`${ok ? "ok " : "XX "}[E3] one record, cut in two by readline, neither half parses`);
console.log(`node ${process.version}`);
process.exit(ok ? 0 : 1);
