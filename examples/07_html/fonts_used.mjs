#!/usr/bin/env node
// Which fonts did the browser ACTUALLY use to draw a cantillated verse? (section 8 of the resource, claim FO1)
//
// Renders one verse (Gen 2:25: letters, nikud, te'amim, meteg) under several CSS font-family stacks in headless
// Chromium, then asks the DevTools protocol (CSS.getPlatformFontsForNode) which platform fonts drew the glyphs
// of each line, and how many glyphs each. A stack whose first font lacks the te'amim either falls back to
// another font for those clusters (two or more fonts listed for one line) or draws them with the first font's
// empty glyph (one font listed: look at fonts_lang_he.png and fonts_no_lang.png, made by make_pages.py). Which of
// the two happens depends on the installed fonts and the font configuration, so the table is printed, not checked.
//   FO1  A line that names one installed font which has every code point of the verse (fontconfig's fc-list says
//        which) is drawn whole by that font. A line whose font is missing, or lacks a code point, is not checked.
// Run: node fonts_used.mjs [--no-lang] [--no-user-fontconfig]     (needs chromium; Node 22+ for the built-in WebSocket)
//   --no-lang             the page has no lang attribute (by default it has <html lang="he">)
//   --no-user-fontconfig  Chromium (and fc-list) run with XDG_CONFIG_HOME pointed at an empty folder, so the user's
//                         own fontconfig rules (~/.config/fontconfig) are left out
import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

if (typeof WebSocket === "undefined") { console.error(`needs Node.js 22 or later (its built-in WebSocket); this is ${process.version}`); process.exit(2); }
const OPTIONS = ["--no-lang", "--no-user-fontconfig"];
const unknown = process.argv.slice(2).filter((a) => !OPTIONS.includes(a));
if (unknown.length) { console.error(`unknown option ${unknown.join(" ")}; the options are ${OPTIONS.join(" ")}`); process.exit(2); }
const here = dirname(fileURLToPath(import.meta.url));
const verse = JSON.parse(readFileSync(join(here, "..", "data", "verses.json"), "utf8")).verses.find((v) => v.ref === "Gen 2:25").text;
const stacks = ["Arial", "Arial, sans-serif", "DejaVu Sans", "DejaVu Sans, sans-serif", "Times New Roman, serif",
  "Noto Sans Hebrew", "Ezra SIL", "Keter YG", "Liberation Mono", "monospace", "sans-serif", "serif"];
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
const lang = process.argv.includes("--no-lang") ? "" : ' lang="he"';
const noUserConfig = process.argv.includes("--no-user-fontconfig");
const html = `<!doctype html><html${lang}><head><meta charset="utf-8"></head><body dir="rtl">` +
  stacks.map((f, i) => `<p><span class="f" id="f${i}" style="font-family: ${esc(f)}; font-size: 28px">${esc(verse)}</span></p>`).join("") +
  `</body></html>`;

const exe = ["chromium", "chromium-browser", "google-chrome"]          // the names run_all.sh looks for, on the PATH
  .flatMap((x) => (process.env.PATH ?? "").split(":").filter(Boolean).map((d) => join(d, x))).find((p) => existsSync(p));
if (!exe) { console.error("needs chromium, chromium-browser or google-chrome on the PATH"); process.exit(2); }

const work = mkdtempSync(join(tmpdir(), "fonts-used-"));
const env = { ...process.env, TMPDIR: join(work, "tmp") };            // the browser's own temporary files go here too
mkdirSync(env.TMPDIR);
if (noUserConfig) { env.XDG_CONFIG_HOME = join(work, "empty-config"); mkdirSync(env.XDG_CONFIG_HOME); }
const page = join(work, "page.html");
writeFileSync(page, html);
const proc = spawn(exe, ["--headless=new", "--disable-gpu", "--remote-debugging-port=0",
  `--user-data-dir=${join(work, "profile")}`, "about:blank"], { stdio: ["ignore", "ignore", "pipe"], env });
let said = "";                                                        // the browser's last words, for a failure
proc.stderr.on("data", (d) => { said = (said + d).slice(-4000); });
const closed = new Promise((r) => proc.once("close", r));
const running = () => proc.exitCode === null && proc.signalCode === null;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws, id = 0;

// Close the browser and wait until it has exited before removing its profile: it writes there on its way out, so
// removing the folder while it still runs fails (ENOTEMPTY) or leaves the folder behind.
async function finish(status) {
  if (running()) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ id: ++id, method: "Browser.close" }));
    else proc.kill();
    const timer = setTimeout(() => proc.kill("SIGKILL"), 10000);
    await closed; clearTimeout(timer);
  }
  if (ws) ws.close();
  rmSync(work, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  process.exit(status);
}
async function failed(what) {                                         // one plain line, then the browser's own lines
  if (!running()) await closed;
  const last = said.trim().split("\n").filter(Boolean).slice(-3);
  const why = /sandbox/.test(said) ? "its sandbox could not start (as root, or in a container); Chromium starts there only with --no-sandbox"
    : /Socket path too long/.test(said) ? "the path of its socket was too long; set TMPDIR to a short directory"
    : last.length ? "its last lines are below" : "it said nothing";
  console.error(`${exe} ${what}: ${why}` + last.map((l) => "\n    " + l).join(""));
  await finish(2);
}

let port;
for (let i = 0; i < 100 && !port && running(); i++) {
  const f = join(work, "profile", "DevToolsActivePort");
  if (existsSync(f)) port = readFileSync(f, "utf8").split("\n")[0];
  else await sleep(100);
}
if (!port) await failed(running() ? "gave no DevTools port in 10 seconds" : `did not start (exit status ${proc.exitCode ?? proc.signalCode})`);

const pending = new Map();
const events = [];
const send = (method, params = {}) => new Promise((r) => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
const drawn = [];
let version;
try {
  const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page");
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.addEventListener("open", r, { once: true }); ws.addEventListener("error", j, { once: true }); });
  ws.addEventListener("message", (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } else if (m.method) events.push(m.method);
  });
  await send("Page.enable"); await send("DOM.enable"); await send("CSS.enable");
  await send("Page.navigate", { url: "file://" + page });
  for (let i = 0; i < 100 && !events.includes("Page.loadEventFired"); i++) await sleep(100);
  await sleep(300);
  const root = (await send("DOM.getDocument", { depth: -1 })).result.root.nodeId;
  version = (await send("Browser.getVersion")).result.product;
  for (let i = 0; i < stacks.length; i++) {
    const node = (await send("DOM.querySelector", { nodeId: root, selector: `#f${i}` })).result.nodeId;
    drawn.push((await send("CSS.getPlatformFontsForNode", { nodeId: node })).result.fonts);
  }
} catch (e) {
  await failed(`did not answer over the DevTools protocol (${e.message || e.type || e})`);
}
console.log(version, (lang ? '· <html lang="he">' : "· no lang attribute") + (noUserConfig ? " · user fontconfig ignored" : ""));
for (let i = 0; i < stacks.length; i++) {
  console.log(`font-family: ${stacks[i].padEnd(26)} -> ` + drawn[i].map((f) => `${f.familyName} (${f.glyphCount})`).join(" + "));
}

// FO1 — the lines that name one font, which fontconfig says is installed with every code point of the verse
const cps = [...new Set([...verse].filter((c) => c !== " ").map((c) => c.codePointAt(0).toString(16)))].sort();
const fcList = (pattern) => {                                         // the families fc-list finds, or null without fc-list
  const r = spawnSync("fc-list", [pattern, "family"], { encoding: "utf8", env });
  return r.error ? null : r.stdout.trim();
};
const results = [];
let unchecked = 0;
for (let i = 0; i < stacks.length; i++) {
  const f = stacks[i];
  if (f.includes(",") || ["monospace", "sans-serif", "serif"].includes(f)) continue;     // one named font only
  const installed = fcList(`:family=${f}`);
  const reason = installed === null ? "no fc-list to ask" : !installed ? "not installed"
    : !fcList(`:family=${f}:charset=${cps.join(" ")}`) ? `fontconfig: it lacks some of the verse's ${cps.length} code points` : null;
  if (reason) { unchecked++; console.log(`--  [FO1] font-family: ${f}: not checked (${reason})`); continue; }
  const names = drawn[i].map((x) => x.familyName);
  const ok = names.length === 1 && names[0] === f;
  results.push(ok);
  console.log(`${ok ? "ok " : "XX "}[FO1] font-family: ${f}, installed with all ${cps.length} code points of the verse: drawn by it alone: ` +
    `observed ${JSON.stringify(names)}${ok ? "" : `  (expected ${JSON.stringify([f])})`}`);
}
const bad = results.filter((x) => !x).length;
console.log(`--- ${results.length - bad} of ${results.length} checks as expected${bad ? `; ${bad} NOT` : ""}${unchecked ? `; ${unchecked} not checked` : ""}`);
await finish(bad ? 1 : 0);
