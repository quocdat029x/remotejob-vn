// Regression: the apply interstitial must not stick after a same-tab redirect and Back.
// Headless Chrome with the back/forward cache enabled. Needs google-chrome.
//
// Covers:
//   open -> countdown redirect -> Back -> dialog closed and the page is interactive
//   open -> continue -> Back -> same
//   open -> close button dismisses even if navigation has not finished
//   open -> Escape does the same
//   open -> backdrop does the same
//   open -> pagehide + pageshow(persisted) (mobile Safari restore semantics) closes it
import { spawn, execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, cpSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36";
const failures = [];

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function check(cond, name, detail) {
  if (cond) {
    console.log("ok", name);
    return;
  }
  failures.push(name);
  console.error("FAIL", name, detail ? JSON.stringify(detail) : "");
}

const pageScript = `
<script>
window.__show = [];
window.__reasons = null;
addEventListener("pageshow", function (e) {
  window.__show.push(!!e.persisted);
  if (!e.persisted) {
    var nav = performance.getEntriesByType("navigation")[0];
    window.__reasons = nav && nav.notRestoredReasons ? nav.notRestoredReasons : null;
  }
});
window.__snap = function () {
  var ping = document.getElementById("ping");
  var rect = ping.getBoundingClientRect();
  var hit = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
  var main = document.getElementById("main");
  return {
    path: location.pathname,
    ix: !!document.querySelector(".ix"),
    open: !!document.querySelector("dialog[open]"),
    bodyOverflow: document.body.style.overflow,
    htmlOverflow: document.documentElement.style.overflow,
    inert: !!(main && main.inert) || !!document.querySelector("[inert]"),
    marked: document.querySelectorAll("[data-ix-inert]").length,
    hitPing: !!(hit && hit.closest && hit.closest("#ping")),
    shows: window.__show.slice()
  };
};
document.getElementById("ping").addEventListener("click", function () {
  document.getElementById("pong").textContent = "pong";
});
</script>`;

function jobPage(seconds) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Job</title>
<link rel="stylesheet" href="/assets/style.css">
</head>
<body data-lang="en">
<main id="main">
  <h1>Sample role</h1>
  <p><a class="btn primary" data-out="job" id="apply" href="/company.html">View original and apply</a></p>
  <button type="button" id="ping" style="width:140px;height:44px">Ping</button>
  <output id="pong"></output>
</main>
<script type="application/json" id="rj-ix">{"label":"Ad","seconds":${seconds},"href":"/house.html","title":"A note","body":"House note","cta":"See options","go":"Continue to job","close":"Close","count":"Continuing automatically in {n}s","support":"Support","supportHref":"/support.html","first_click":true,"every_n":2,"min_gap_ms":180000}</script>
<script src="/assets/app.js" defer></script>
${pageScript}
</body>
</html>`;
}

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    this.events = [];
  }
  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((resolve, reject) => {
      ws.addEventListener("open", resolve, { once: true });
      ws.addEventListener("error", reject, { once: true });
    });
    const cdp = new Cdp(ws);
    ws.addEventListener("message", (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && cdp.pending.has(msg.id)) {
        const { resolve, reject } = cdp.pending.get(msg.id);
        cdp.pending.delete(msg.id);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result);
      } else if (msg.method) cdp.events.push(msg);
    });
    return cdp;
  }
  send(method, params = {}, sessionId) {
    const id = ++this.id;
    const payload = { id, method, params };
    if (sessionId) payload.sessionId = sessionId;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify(payload));
    });
  }
}

async function main() {
  const dir = mkdtempSync(join(tmpdir(), "rj-ix-"));
  mkdirSync(join(dir, "assets"), { recursive: true });
  cpSync(join(root, "site/assets/app.js"), join(dir, "assets/app.js"));
  cpSync(join(root, "site/assets/style.css"), join(dir, "assets/style.css"));
  writeFileSync(join(dir, "index.html"), jobPage(30));
  writeFileSync(join(dir, "fast.html"), jobPage(1));
  writeFileSync(join(dir, "company.html"), "<!doctype html><title>Company</title><p>careers</p>");
  writeFileSync(join(dir, "house.html"), "<!doctype html><title>House</title><p>house</p>");
  writeFileSync(join(dir, "support.html"), "<!doctype html><title>Support</title><p>support</p>");

  const server = spawn("python3", ["-m", "http.server", "8899", "--bind", "127.0.0.1", "--directory", dir], { stdio: "ignore" });
  const profile = mkdtempSync(join(tmpdir(), "rj-chrome-"));
  const chrome = spawn("google-chrome", [
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--no-first-run",
    "--disable-dev-shm-usage",
    `--user-data-dir=${profile}`,
    "--remote-debugging-port=9341",
    "--enable-features=BackForwardCache",
    `--user-agent=${UA}`,
    "about:blank",
  ], { stdio: "ignore" });

  let browser;
  try {
    let version;
    for (let i = 0; i < 50; i++) {
      try {
        const res = await fetch("http://127.0.0.1:9341/json/version");
        if (res.ok) { version = await res.json(); break; }
      } catch { /* chrome still starting */ }
      await sleep(100);
    }
    if (!version) throw new Error("Chrome DevTools did not start");
    browser = await Cdp.connect(version.webSocketDebuggerUrl);
    const { targetId } = await browser.send("Target.createTarget", { url: "about:blank" });
    const { sessionId } = await browser.send("Target.attachToTarget", { targetId, flatten: true });
    const send = (method, params) => browser.send(method, params, sessionId);
    await send("Page.enable");
    await send("Runtime.enable");

    async function evaluate(expression) {
      const result = await send("Runtime.evaluate", { expression, returnByValue: true });
      if (result.exceptionDetails) {
        throw new Error(result.exceptionDetails.text || "evaluate failed");
      }
      return result.result.value;
    }
    async function waitPath(path, timeout = 6000) {
      const start = Date.now();
      let last = "";
      while (Date.now() - start < timeout) {
        try {
          last = await evaluate("location.pathname");
          if (last === path) return;
        } catch { /* navigation in progress */ }
        await sleep(40);
      }
      throw new Error("timed out waiting for " + path + " (at " + last + ")");
    }
    async function openJob(path) {
      await send("Page.navigate", { url: "http://127.0.0.1:8899" + path });
      await waitPath(path);
      await sleep(50);
      const probe = await evaluate("({webdriver: navigator.webdriver, ua: navigator.userAgent, ready: !!document.querySelector('#apply')})");
      if (probe.webdriver || /headless/i.test(probe.ua)) throw new Error("bot check would skip the dialog: " + JSON.stringify(probe));
      await evaluate("localStorage.removeItem('rjvn-out-n'); localStorage.removeItem('rjvn-out-at');");
    }
    async function openDialog() {
      const snap = await evaluate(`(() => {
        document.querySelector("#apply").click();
        return window.__snap();
      })()`);
      check(snap.ix && !snap.hitPing, "dialog opens over the page", snap);
      return snap;
    }
    function unlocked(snap) {
      return snap && !snap.ix && !snap.open && !snap.inert && snap.marked === 0 &&
        snap.bodyOverflow === "" && snap.htmlOverflow === "" && snap.hitPing === true;
    }
    async function expectJob(snap) {
      if (!unlocked(snap)) return;
      try {
        await waitPath("/company.html");
      } catch (err) {
        check(false, "dialog continued to the job page", String(err));
      }
    }

    await openJob("/index.html");
    await openDialog();
    const closed = await evaluate(`(() => {
      document.querySelector("[data-ix-x]").click();
      return window.__snap();
    })()`);
    check(unlocked(closed), "open -> close button clears the dialog before navigation", closed);
    await expectJob(closed);

    await openJob("/index.html");
    await openDialog();
    const escaped = await evaluate(`(() => {
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", code: "Escape", bubbles: true, cancelable: true }));
      return window.__snap();
    })()`);
    check(unlocked(escaped), "open -> Escape clears the dialog before navigation", escaped);
    await expectJob(escaped);

    await openJob("/index.html");
    await openDialog();
    const backdrop = await evaluate(`(() => {
      document.querySelector(".ix").click();
      return window.__snap();
    })()`);
    check(unlocked(backdrop), "open -> backdrop clears the dialog before navigation", backdrop);
    await expectJob(backdrop);

    await openJob("/index.html");
    await openDialog();
    const restored = await evaluate(`(() => {
      window.dispatchEvent(new PageTransitionEvent("pagehide", { persisted: true }));
      window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
      document.querySelector("#ping").click();
      var snap = window.__snap();
      snap.pong = document.querySelector("#pong").textContent;
      return snap;
    })()`);
    check(unlocked(restored) && restored.path === "/index.html" && restored.pong === "pong",
      "open -> pagehide/pageshow persisted closes the dialog and leaves the page interactive", restored);

    await openJob("/index.html");
    await openDialog();
    const showOnly = await evaluate(`(() => {
      window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
      document.querySelector("#ping").click();
      var snap = window.__snap();
      snap.pong = document.querySelector("#pong").textContent;
      return snap;
    })()`);
    check(unlocked(showOnly) && showOnly.path === "/index.html" && showOnly.pong === "pong",
      "pageshow persisted alone closes a dialog restored from bfcache", showOnly);

    await openJob("/index.html");
    await openDialog();
    const vis = await evaluate(`(() => {
      try {
        window.__vis = "visible";
        Object.defineProperty(Document.prototype, "visibilityState", {
          configurable: true,
          get: function () { return window.__vis || "visible"; }
        });
        Object.defineProperty(Document.prototype, "hidden", {
          configurable: true,
          get: function () { return (window.__vis || "visible") === "hidden"; }
        });
      } catch (e) { return { override: String(e) }; }
      window.__vis = "hidden";
      document.dispatchEvent(new Event("visibilitychange"));
      document.querySelector("#ping").click();
      var snap = window.__snap();
      snap.pong = document.querySelector("#pong").textContent;
      snap.override = "ok";
      return snap;
    })()`);
    check(vis.override === "ok" && unlocked(vis) && vis.path === "/index.html" && vis.pong === "pong",
      "open -> visibilitychange hidden closes the dialog", vis);

    await openJob("/index.html");
    await openDialog();
    await evaluate(`document.querySelector("[data-ix-go]").click();`);
    await waitPath("/company.html");
    await evaluate("history.back();");
    await waitPath("/index.html");
    await sleep(150);
    const afterContinue = await evaluate(`(() => {
      document.querySelector("#ping").click();
      var snap = window.__snap();
      snap.pong = document.querySelector("#pong").textContent;
      return snap;
    })()`);
    check(afterContinue.shows.indexOf(true) !== -1, "continue -> Back restored the page from bfcache", afterContinue);
    check(unlocked(afterContinue) && afterContinue.pong === "pong",
      "open -> continue -> Back -> dialog closed and page interactive", afterContinue);

    await openJob("/fast.html");
    await openDialog();
    await waitPath("/company.html", 5000);
    await evaluate("history.back();");
    await waitPath("/fast.html");
    await sleep(150);
    const afterCountdown = await evaluate(`(() => {
      document.querySelector("#ping").click();
      var snap = window.__snap();
      snap.pong = document.querySelector("#pong").textContent;
      return snap;
    })()`);
    check(afterCountdown.shows.indexOf(true) !== -1, "countdown -> Back restored the page from bfcache", afterCountdown);
    check(unlocked(afterCountdown) && afterCountdown.pong === "pong",
      "open -> countdown redirect -> Back -> dialog closed and page interactive", afterCountdown);

    await openJob("/index.html");
    await openDialog();
    await evaluate(`document.querySelector("[data-ix-house]").click();`);
    await waitPath("/house.html");
    await evaluate("history.back();");
    await waitPath("/index.html");
    await sleep(150);
    const afterHouse = await evaluate("window.__snap()");
    check(!afterHouse.ix && !afterHouse.inert && afterHouse.hitPing && afterHouse.bodyOverflow === "",
      "house link -> Back does not restore a stuck dialog", afterHouse);
  } finally {
    try { if (browser) browser.ws.close(); } catch { /* socket already gone */ }
    chrome.kill("SIGKILL");
    server.kill("SIGKILL");
    await sleep(200);
    try { execFileSync("rm", ["-rf", profile, dir]); } catch { /* profile may still be settling */ }
  }

  if (failures.length) {
    console.error(failures.length + " failure(s)");
    process.exit(1);
  }
  console.log("interstitial bfcache ok");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
