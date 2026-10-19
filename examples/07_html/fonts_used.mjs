#!/usr/bin/env node
// Which fonts did the browser ACTUALLY use to draw a cantillated verse? (section 8 of the resource, claim FO1)
//
// Renders one verse (Gen 2:25: letters, nikud, te'amim, meteg) under several CSS font-family stacks in headless
// Chromium, then asks the DevTools protocol (CSS.getPlatformFontsForNode) which platform fonts drew the glyphs
// of each line, and how many glyphs each. A stack whose first font lacks the te'amim either falls back to
// another font for those clusters (two or more fonts listed for one line) or draws them with the first
// font's empty glyph (one font listed — look at fonts.png).
// Run: node fonts_used.mjs [--no-lang]        (needs chromium; Node 22+ for the built-in WebSocket)
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const verse = JSON.parse(readFileSync(join(here, "..", "data", "verses.json"), "utf8")).verses.find((v) => v.ref === "Gen 2:25").text;
const stacks = ["Arial", "Arial, sans-serif", "DejaVu Sans", "DejaVu Sans, sans-serif", "Times New Roman, serif",
  "Noto Sans Hebrew", "Ezra SIL", "Keter YG", "Liberation Mono", "monospace", "sans-serif", "serif"];
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
const lang = process.argv.includes("--no-lang") ? "" : ' lang="he"';
const html = `<!doctype html><html${lang}><head><meta charset="utf-8"></head><body dir="rtl">` +
  stacks.map((f, i) => `<p><span class="f" id="f${i}" style="font-family: ${esc(f)}; font-size: 28px">${esc(verse)}</span></p>`).join("") +
  `</body></html>`;

const work = mkdtempSync(join(tmpdir(), "fonts-used-"));
const page = join(work, "page.html");
writeFileSync(page, html);
const exe = ["chromium", "chromium-browser", "google-chrome"].find((x) => existsSync(`/usr/bin/${x}`));
if (!exe) { console.error("needs chromium"); process.exit(2); }
const proc = spawn(`/usr/bin/${exe}`, ["--headless=new", "--disable-gpu", "--remote-debugging-port=0",
  `--user-data-dir=${join(work, "profile")}`, "about:blank"], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let port;
for (let i = 0; i < 100 && !port; i++) {
  const f = join(work, "profile", "DevToolsActivePort");
  if (existsSync(f)) port = readFileSync(f, "utf8").split("\n")[0];
  else await sleep(100);
}
const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page");
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let id = 0;
const pending = new Map();
const events = [];
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } else if (m.method) events.push(m.method);
});
const send = (method, params = {}) => new Promise((r) => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });

await send("Page.enable"); await send("DOM.enable"); await send("CSS.enable");
await send("Page.navigate", { url: "file://" + page });
for (let i = 0; i < 100 && !events.includes("Page.loadEventFired"); i++) await sleep(100);
await sleep(300);
const root = (await send("DOM.getDocument", { depth: -1 })).result.root.nodeId;
const version = (await send("Browser.getVersion")).result.product;
console.log(version, lang ? '· <html lang="he">' : "· no lang attribute");
for (let i = 0; i < stacks.length; i++) {
  const node = (await send("DOM.querySelector", { nodeId: root, selector: `#f${i}` })).result.nodeId;
  const fonts = (await send("CSS.getPlatformFontsForNode", { nodeId: node })).result.fonts;
  console.log(`font-family: ${stacks[i].padEnd(26)} -> ` + fonts.map((f) => `${f.familyName} (${f.glyphCount})`).join(" + "));
}
ws.close(); proc.kill();
rmSync(work, { recursive: true, force: true });
