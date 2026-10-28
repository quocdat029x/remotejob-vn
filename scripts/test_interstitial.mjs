// Frequency cap and bot skip for the outbound-click interstitial.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createContext, runInContext } from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

// The functions live in site/assets/app.js. This test extracts them so it does not need a browser.
const app = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "../site/assets/app.js"), "utf8");

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
const gap = 10 * 60 * 1000;
const t0 = 1_700_000_000_000;

let d = decide(0, 0, t0);
assert.equal(d.show, false, "first outbound click does not show an ad");
assert.equal(d.clicks, 1);
d = decide(d.clicks, 0, t0);
assert.equal(d.show, false, "second click does not show an ad");
d = decide(d.clicks, 0, t0);
assert.equal(d.show, true, "third click shows an ad when none was shown recently");
assert.equal(d.clicks, 3);
assert.equal(d.lastShownMs, t0);

d = decide(5, t0, t0 + gap - 1);
assert.equal(d.show, false, "sixth click inside 10 minutes does not show another ad");
assert.equal(d.clicks, 6);

d = decide(8, t0, t0 + gap);
assert.equal(d.show, true, "ninth click after 10 minutes shows again");
assert.equal(d.lastShownMs, t0 + gap);

const chrome = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
assert.equal(isBot(false, chrome), false);
assert.equal(isBot(true, chrome), true, "navigator.webdriver skips the interstitial");
assert.equal(isBot(false, "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"), true);
assert.equal(isBot(false, "Mozilla/5.0 (compatible; bingbot/2.0)"), true);
assert.equal(isBot(false, "Mozilla/5.0 HeadlessChrome/120.0.0.0"), true);

console.log("interstitial policy ok");
