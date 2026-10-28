// Progressive enhancement only: every page is fully rendered without this file.
// Adds client-side filtering, and the apply-click interstitial. No cookies.
// Cloudflare Web Analytics is injected by Pages, not by this file.
(function () {
  "use strict";
  function rjIsBot(webdriver, ua) {
    if (webdriver) return true;
    return /bot|crawl|spider|slurp|headless|phantom|semrush|ahrefs|petalbot|lighthouse|facebookexternalhit|embedly/i.test(ua || "");
  }
  function rjOutboundAdDecision(clicks, lastShownMs, nowMs, rules) {
    var cfg = rules || {};
    var everyN = parseInt(cfg.every_n != null ? cfg.every_n : cfg.everyN, 10);
    if (!everyN || everyN < 1) everyN = 2;
    var gap = parseInt(cfg.min_gap_ms != null ? cfg.min_gap_ms : cfg.minGapMs, 10);
    if (isNaN(gap) || gap < 0) gap = 180000;
    var first = cfg.first_click != null ? cfg.first_click : cfg.firstClick;
    if (first == null) first = true;
    var n = (clicks || 0) + 1;
    var due = !lastShownMs || (nowMs - lastShownMs) >= gap;
    var onCadence = first ? (n === 1 || (n - 1) % everyN === 0) : (n % everyN === 0);
    var show = onCadence && due;
    return {clicks: n, show: show, lastShownMs: show ? nowMs : (lastShownMs || 0)};
  }
  var lang = document.body.getAttribute("data-lang") || "vi";
  var L = lang === "en"
    ? { results: "results", more: "Show more", ad: "Ad", checked: "checked",
        region: { vn: "Vietnam", apac: "APAC", global: "Worldwide", other: "Other / unclear" },
        remote: { yes: "Remote", hybrid: "Hybrid", no: "Onsite", unknown: "Remote: unclear" } }
    : { results: "kết quả", more: "Xem thêm", ad: "Quảng cáo", checked: "kiểm tra",
        region: { vn: "Việt Nam", apac: "APAC", global: "Toàn cầu", other: "Khu vực khác / chưa rõ" },
        remote: { yes: "Remote", hybrid: "Hybrid", no: "Onsite", unknown: "Chưa rõ remote" } };
  var prefix = lang === "en" ? "/en" : "";

  // ---- theme toggle (the initial theme is applied by a tiny inline script in <head> to avoid a flash)
  var tb = document.getElementById("theme-toggle");
  if (tb) {
    var root = document.documentElement;
    var current = function () {
      return root.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    };
    var label = function () { tb.setAttribute("aria-pressed", current() === "dark" ? "true" : "false"); };
    tb.hidden = false;
    label();
    tb.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try { localStorage.setItem("theme", next); } catch (e) { /* storage may be disabled */ }
      label();
    });
  }

  function norm(s) {
    return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d");
  }
  function params(form) {
    var o = {};
    Array.prototype.forEach.call(form.elements, function (el) { if (el.name && el.value) o[el.name] = el.value; });
    return o;
  }
  function syncUrl(o) {
    var q = new URLSearchParams(o).toString();
    history.replaceState(null, "", location.pathname + (q ? "?" + q : ""));
  }
  function restore(form) {
    var q = new URLSearchParams(location.search);
    Array.prototype.forEach.call(form.elements, function (el) { if (el.name && q.get(el.name)) el.value = q.get(el.name); });
  }
  function fmtDate(d) { if (!d) return ""; var p = d.split("-"); return lang === "vi" ? p[2] + "/" + p[1] + "/" + p[0] : d; }
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

  // ---- company directory
  var cf = document.getElementById("co-filters");
  if (cf) {
    cf.hidden = false;
    restore(cf);
    var cards = document.querySelectorAll("#co-list > .co");
    var adCards = document.querySelectorAll("#co-list > .slot-native");
    var run = function () {
      var o = params(cf), q = norm(o.q), n = 0;
      cards.forEach(function (c) {
        var ok = (!q || norm(c.dataset.text).indexOf(q) >= 0) &&
          (!o.role || (" " + c.dataset.roles + " ").indexOf(" " + o.role + " ") >= 0) &&
          (!o.mode || (" " + c.dataset.mode + " ").indexOf(" " + o.mode + " ") >= 0) &&
          (!o.group || c.dataset.group === o.group) &&
          (!o.tz || (" " + c.dataset.tz + " ").indexOf(" " + o.tz + " ") >= 0);
        c.hidden = !ok; if (ok) n++;
      });
      var filtered = Object.keys(o).length > 0;
      adCards.forEach(function (a) { a.hidden = filtered; });
      cf.elements.count.value = n + " " + L.results;
      document.getElementById("co-empty").hidden = n > 0;
      syncUrl(o);
    };
    cf.addEventListener("input", run);
    cf.addEventListener("reset", function () { setTimeout(run, 0); });
    cf.addEventListener("submit", function (e) { e.preventDefault(); });
    run();
  }

  // ---- jobs list: page 1 is pre-rendered; filtering loads a compact index of all jobs.
  var jf = document.getElementById("job-filters");
  if (jf) {
    jf.hidden = false;
    restore(jf);
    var list = document.getElementById("job-list");
    var pager = document.querySelector(".pager");
    var moreBox = document.getElementById("job-more");
    var empty = document.getElementById("job-empty");
    var original = list.innerHTML, idx = null, shown = 50, matches = [];
    var load = function () {
      if (idx) return Promise.resolve(idx);
      return fetch(list.dataset.index).then(function (r) { return r.json(); }).then(function (d) { idx = d; return d; });
    };
    var row = function (j) {
      var co = idx.cos[j[2]] || j[2];
      return '<li class="card job-card"><a class="t" href="' + prefix + "/viec-lam/" + j[0] + '/">' + esc(j[1]) + "</a>" +
        '<div class="meta"><a class="co" href="' + prefix + "/cong-ty/" + j[2] + '/">' + esc(co) + "</a>" +
        (j[6] ? '<span class="loc">' + esc(j[6]) + "</span>" : "") + "</div>" +
        '<div class="tags"><span class="b r-' + j[3] + '">' + L.region[j[3]] + '</span><span class="b m-' + j[4] + '">' + L.remote[j[4]] + "</span>" +
        (j[8] ? '<span class="b sal">💰 ' + esc(j[8]) + "</span>" : "") +
        '<span class="b date">✓ ' + L.checked + " " + fmtDate(j[7]) + "</span></div></li>";
    };
    var render = function () {
      var every = Math.min(15, Math.max(10, idx.every || 12)), html = [];
      matches.slice(0, shown).forEach(function (j, i) {
        html.push(row(j));
        if (idx.ad && (i + 1) % every === 0 && i + 1 < Math.min(shown, matches.length))
          html.push('<li class="slot slot-native"><span class="label">' + L.ad + '</span><a href="' + prefix + idx.ad.url + '">' + esc(idx.ad[lang]) + "</a></li>");
      });
      list.innerHTML = html.join("");
      empty.hidden = matches.length > 0;
      moreBox.innerHTML = matches.length > shown ? '<button type="button" class="btn">' + L.more + " (" + (matches.length - shown) + ")</button>" : "";
    };
    moreBox.addEventListener("click", function () { shown += 50; render(); });
    var run2 = function () {
      var o = params(jf);
      syncUrl(o);
      if (!Object.keys(o).length) {
        list.innerHTML = original; moreBox.innerHTML = ""; empty.hidden = true; if (pager) pager.hidden = false; jf.elements.count.value = ""; return;
      }
      load().then(function () {
        var q = norm(o.q);
        matches = idx.jobs.filter(function (j) {
          return (!o.role || (" " + j[5] + " ").indexOf(" " + o.role + " ") >= 0) && (!o.company || j[2] === o.company) &&
            (!o.region || j[3] === o.region) && (!o.remote || j[4] === o.remote) &&
                (!q || norm(j[1] + " " + (idx.cos[j[2]] || "") + " " + j[6]).indexOf(q) >= 0) &&
            (!j[9] || o.company === j[2]);
        });
        shown = 50;
        if (pager) pager.hidden = true;
        jf.elements.count.value = matches.length + " " + L.results;
        render();
      });
    };
    var t;
    jf.addEventListener("input", function () { clearTimeout(t); t = setTimeout(run2, 150); });
    jf.addEventListener("reset", function () { setTimeout(run2, 0); });
    jf.addEventListener("submit", function (e) { e.preventDefault(); });
    if (location.search) run2();
  }

  // Outbound apply click only. The <a href> stays a normal link when JS is off.
  // Nothing here runs on load. Bots and webdriver never see the dialog.
  function storeGet(key) {
    try { return localStorage.getItem(key); } catch (e) { /* storage blocked */ }
    try { return sessionStorage.getItem(key); } catch (e2) { return null; }
  }
  function storeSet(key, val) {
    try { localStorage.setItem(key, val); return; } catch (e) { /* storage blocked */ }
    try { sessionStorage.setItem(key, val); } catch (e2) { /* storage blocked */ }
  }
  function safeHref(h) {
    if (h && h.charAt(0) === "/" && h.charAt(1) !== "/") return h;
    if (h && /^https:\/\//i.test(h)) return h;
    return prefix + "/quang-cao/";
  }
  // House or affiliate creative only. Never mount an AdSense unit in this dialog.
  var ixActive = null;
  function ixUnlock() {
    document.documentElement.style.overflow = "";
    document.body.style.overflow = "";
    var locked = document.querySelectorAll("[data-ix-inert],[inert]");
    for (var i = 0; i < locked.length; i++) {
      locked[i].inert = false;
      locked[i].removeAttribute("data-ix-inert");
    }
  }
  function ixLock() {
    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";
    var kids = document.body.children;
    for (var j = 0; j < kids.length; j++) {
      var n = kids[j];
      if (n.classList.contains("ix") || n.hasAttribute("data-ix-inert")) continue;
      n.setAttribute("data-ix-inert", "");
      n.inert = true;
    }
  }
  function ixDrop(node) {
    if (!node || !node.parentNode) return;
    if (node.open && node.close) { try { node.close(); } catch (e) { /* already closed */ } }
    node.parentNode.removeChild(node);
  }
  // Always clears the overlay. The in-flight redirect flag must not block this:
  // bfcache can restore a page whose countdown already called leave().
  function ixDismissActive() {
    var current = ixActive;
    ixActive = null;
    if (current) current.dismiss();
    ixDrop(document.querySelector(".ix"));
    ixUnlock();
  }
  function openIx(href) {
    ixDismissActive();
    var root = document.createElement("dialog");
    root.className = "ix";
    root.setAttribute("aria-modal", "true");
    root.setAttribute("aria-labelledby", "rj-ix-title");
    var house = safeHref(ixCfg.href);
    var support = "";
    if (ixCfg.support && ixCfg.supportHref) {
      support = '<p class="ix-support"><a data-ix-support href="' + esc(safeHref(ixCfg.supportHref)) + '">' + esc(ixCfg.support) + "</a></p>";
    }
    root.innerHTML = '<div class="ix-card"><div class="ix-top"><span class="label ix-label">' + esc(ixCfg.label || "Quảng cáo / Advertisement") + "</span>" +
      '<button type="button" class="btn" data-ix-x>' + esc(ixCfg.close || "Close") + "</button></div>" +
      '<h2 id="rj-ix-title">' + esc(ixCfg.title || "") + "</h2><p>" + esc(ixCfg.body || "") + "</p>" + support +
      '<div class="ix-actions">' + (ixCfg.cta ? '<a class="btn" data-ix-house href="' + esc(house) + '">' + esc(ixCfg.cta) + "</a>" : "") +
      '<button type="button" class="btn primary" data-ix-go>' + esc(ixCfg.go || "Continue to job") + "</button></div>" +
      '<p class="ix-count" id="rj-ix-count" aria-live="polite"></p></div>';
    document.body.appendChild(root);
    ixLock();
    var sent = false, timer = null;
    function dismiss() {
      if (timer) { clearInterval(timer); timer = null; }
      document.removeEventListener("keydown", onKey, true);
      ixDrop(root);
      if (ixActive === api) ixActive = null;
      ixUnlock();
    }
    function leave() {
      dismiss();
      if (sent) return;
      sent = true;
      location.assign(href);
    }
    function onKey(e) {
      if (e.key === "Escape") { e.preventDefault(); leave(); return; }
      if (e.key !== "Tab") return;
      var f = root.querySelectorAll("a[href],button:not([disabled])");
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
    var api = { dismiss: dismiss };
    ixActive = api;
    try { root.showModal(); } catch (e) { /* the fixed overlay still covers the page */ }
    document.addEventListener("keydown", onKey, true);
    root.addEventListener("cancel", function (e) { e.preventDefault(); leave(); });
    root.addEventListener("click", function (e) { if (e.target === root) leave(); });
    root.querySelector("[data-ix-x]").addEventListener("click", leave);
    root.querySelector("[data-ix-go]").addEventListener("click", leave);
    function disarmLink(link) {
      if (!link) return;
      link.addEventListener("click", function () {
        sent = true;
        if (timer) { clearInterval(timer); timer = null; }
        // After this click's default navigation is queued. Removing the anchor
        // inside the click handler can cancel it, so close on the next turn.
        setTimeout(dismiss, 0);
      });
    }
    disarmLink(root.querySelector("[data-ix-house]"));
    disarmLink(root.querySelector("[data-ix-support]"));
    var countEl = root.querySelector("#rj-ix-count");
    var left = ixCfg.seconds || 5;
    var tpl = ixCfg.count || "{n}";
    countEl.textContent = tpl.replace("{n}", String(left));
    timer = setInterval(function () {
      left -= 1;
      if (left <= 0) leave();
      else countEl.textContent = tpl.replace("{n}", String(left));
    }, 1000);
    var closeBtn = root.querySelector("[data-ix-x]");
    if (closeBtn) closeBtn.focus();
  }
  var ixNode = document.getElementById("rj-ix");
  var ixCfg = null;
  if (ixNode && !rjIsBot(navigator.webdriver, navigator.userAgent)) {
    try { ixCfg = JSON.parse(ixNode.textContent); } catch (e) { ixCfg = null; }
  }
  if (ixCfg) {
    window.addEventListener("pagehide", ixDismissActive);
    window.addEventListener("pageshow", function (ev) { if (ev.persisted) ixDismissActive(); });
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden") ixDismissActive();
    });
    document.addEventListener("click", function (ev) {
      var el = ev.target;
      if (el && !el.closest && el.parentElement) el = el.parentElement;
      if (!el || !el.closest) return;
      var a = el.closest('a[data-out="job"]');
      if (!a || ev.button !== 0) return;
      var n = parseInt(storeGet("rjvn-out-n") || "0", 10) || 0;
      var at = parseInt(storeGet("rjvn-out-at") || "0", 10) || 0;
      var d = rjOutboundAdDecision(n, at, Date.now(), ixCfg);
      storeSet("rjvn-out-n", String(d.clicks));
      var modified = ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || a.target === "_blank";
      if (!d.show || modified) return;
      ev.preventDefault();
      storeSet("rjvn-out-at", String(d.lastShownMs));
      openIx(a.href);
    });
  }

  // Dismissible support note. The head script already hides it when the choice is stored,
  // so this only handles the click and does not move layout on load.
  document.addEventListener("click", function (ev) {
    var node = ev.target;
    if (node && !node.closest && node.parentElement) node = node.parentElement;
    if (!node || !node.closest) return;
    var dismiss = node.closest("[data-support-dismiss]");
    if (dismiss) {
      var card = dismiss.closest("[data-support-nudge]");
      if (card) card.hidden = true;
      document.documentElement.dataset.support = "off";
      try { localStorage.setItem("rjvn-support-hide", "1"); } catch (e) { /* storage blocked */ }
      return;
    }
    var copyBtn = node.closest("[data-copy]");
    if (!copyBtn || copyBtn.tagName !== "BUTTON") return;
    var text = copyBtn.getAttribute("data-copy") || "";
    var done = copyBtn.getAttribute("data-copied") || "Copied";
    var original = copyBtn.getAttribute("data-label") || copyBtn.textContent;
    copyBtn.setAttribute("data-label", original);
    function mark() {
      copyBtn.textContent = done;
      window.setTimeout(function () { copyBtn.textContent = original; }, 2000);
    }
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      var copied = false;
      try { copied = document.execCommand("copy"); } catch (err) { copied = false; }
      document.body.removeChild(ta);
      if (copied) mark();
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(mark, fallback);
    else fallback();
  });

  // Sticky sidebar (ad + support card) only when the pair fits in the viewport.
  // A too-tall rail stays in normal flow so the bottom controls remain reachable
  // and the card cannot cover the footer.
  function fitRail() {
    var rail = document.querySelector(".rail");
    if (!rail || !window.matchMedia) return;
    var desktop = window.matchMedia("(min-width: 1100px)").matches;
    if (!desktop) {
      rail.classList.remove("is-tall");
      return;
    }
    rail.classList.remove("is-tall");
    var limit = window.innerHeight - 32;
    rail.classList.toggle("is-tall", rail.offsetHeight > limit);
  }
  fitRail();
  window.addEventListener("resize", fitRail);
  if (window.matchMedia) {
    var desktopQ = window.matchMedia("(min-width: 1100px)");
    if (desktopQ.addEventListener) desktopQ.addEventListener("change", fitRail);
  }
})();
