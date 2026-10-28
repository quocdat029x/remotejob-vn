// Frequency cap and bot skip for the outbound-click interstitial.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createContext, runInContext } from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

// The functions live in site/assets/app.js. This test extracts them so it does not need a browser.
const app = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "../site/assets/app.js"), "utf8");
const root = dirname(fileURLToPath(import.meta.url));

function extract(source, name) {
  const start = source.indexOf("function " + name);
  if (start < 0) throw new Error("missing " + name);
  const brace = source.indexOf("{", start);
  let depth = 0;
  for (let i = brace; i < source.length; i++) {
    if (source[i] === "{") depth++;
    else if (source[i] === "}") {
      depth--;
      if (depth === 0) return source.slice(start, i + 1);
    }
  }
  throw new Error("unclosed " + name);
}

const ctx = {};
runInContext(extract(app, "rjOutboundAdDecision") + "\n" + extract(app, "rjIsBot"), createContext(ctx));
const decide = ctx.rjOutboundAdDecision;
const isBot = ctx.rjIsBot;
const shipped = { first_click: true, every_n: 2, min_gap_ms: 180000 };
const gap = shipped.min_gap_ms;
const t0 = 1_700_000_000_000;

let d = decide(0, 0, t0, shipped);
assert.equal(d.show, true, "first outbound click shows an ad");
assert.equal(d.clicks, 1);
assert.equal(d.lastShownMs, t0);

d = decide(d.clicks, d.lastShownMs, t0 + 1000, shipped);
assert.equal(d.show, false, "the click after the first is not on the every-2 cadence");
assert.equal(d.clicks, 2);
assert.equal(d.lastShownMs, t0, "a skipped click does not move the gap");

d = decide(2, t0, t0 + gap - 1, shipped);
assert.equal(d.show, false, "third click inside 3 minutes does not show");
assert.equal(d.clicks, 3);
assert.equal(d.lastShownMs, t0);

d = decide(2, t0, t0 + gap, shipped);
assert.equal(d.show, true, "third click after 3 minutes shows again");
assert.equal(d.lastShownMs, t0 + gap);

d = decide(3, t0 + gap, t0 + gap + gap, shipped);
assert.equal(d.show, false, "fourth click is off cadence even after the gap");
assert.equal(d.clicks, 4);

d = decide(4, t0, t0 + gap - 1, shipped);
assert.equal(d.show, false, "fifth click inside the gap stays hidden");
d = decide(4, t0, t0 + gap, shipped);
assert.equal(d.show, true, "fifth click after the gap shows");
assert.equal(d.clicks, 5);

const legacy = { first_click: false, every_n: 3, min_gap_ms: 600000 };
d = decide(0, 0, t0, legacy);
assert.equal(d.show, false, "with first_click off, click 1 waits for every_n");
d = decide(1, 0, t0, legacy);
assert.equal(d.show, false);
d = decide(2, 0, t0, legacy);
assert.equal(d.show, true, "every 3rd click still works when configured");
assert.equal(d.clicks, 3);
d = decide(5, t0, t0 + 600000 - 1, legacy);
assert.equal(d.show, false, "legacy 10 minute gap still applies when configured");

d = decide(0, 0, t0);
assert.equal(d.show, true, "missing rules use the shipped first-click default");
d = decide(2, t0, t0 + 180000, {});
assert.equal(d.show, true, "missing rules use a 3 minute gap and every 2nd click");

const config = JSON.parse(readFileSync(join(root, "../site.config.json"), "utf8"));
assert.equal(config.interstitial.first_click, true);
assert.equal(config.interstitial.every_n, 2);
assert.equal(config.interstitial.min_gap_ms, 180000);
assert.equal(app.includes("adsbygoogle"), false, "the interstitial script never loads AdSense");

const chrome = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
assert.equal(isBot(false, chrome), false);
assert.equal(isBot(true, chrome), true, "navigator.webdriver skips the interstitial");
assert.equal(isBot(false, "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"), true);
assert.equal(isBot(false, "Mozilla/5.0 (compatible; bingbot/2.0)"), true);
assert.equal(isBot(false, "Mozilla/5.0 HeadlessChrome/120.0.0.0"), true);

console.log("interstitial policy ok");
