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
  // Facet query: OR within a key, AND across keys. Values stay comma-separated.
  function rjKeys() {
    return ["role", "skill", "tz", "level", "company", "region", "remote", "group", "salary", "posted"];
  }
  function rjFold(s) {
    return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d");
  }
  function rjBlank() {
    var s = {q: ""}, keys = rjKeys(), i;
    for (i = 0; i < keys.length; i++) s[keys[i]] = [];
    return s;
  }
  function rjParseFacetQuery(search) {
    var s = rjBlank(), raw = (search || "").replace(/^\?/, ""), i, part, eq, key, val, seen, bits, n, bit;
    if (!raw) return s;
    var parts = raw.split("&");
    for (i = 0; i < parts.length; i++) {
      part = parts[i];
      if (!part) continue;
      eq = part.indexOf("=");
      key = decodeURIComponent(eq < 0 ? part : part.slice(0, eq));
      val = decodeURIComponent((eq < 0 ? "" : part.slice(eq + 1)).replace(/\+/g, " "));
      if (key === "q") { s.q = val; continue; }
      if (rjKeys().indexOf(key) < 0) continue;
      seen = {};
      bits = val.split(",");
      for (n = 0; n < bits.length; n++) {
        bit = bits[n].replace(/^\s+|\s+$/g, "");
        if (!bit || seen[bit]) continue;
        seen[bit] = 1;
        s[key].push(bit);
      }
    }
    return s;
  }
  function rjSerializeFacetQuery(state) {
    var parts = [], keys = rjKeys(), i, vals;
    if (state.q) parts.push("q=" + encodeURIComponent(state.q));
    for (i = 0; i < keys.length; i++) {
      vals = state[keys[i]] || [];
      if (vals.length) parts.push(keys[i] + "=" + vals.map(encodeURIComponent).join(","));
    }
    return parts.join("&");
  }
  function rjHave(job, key) {
    var v = job[key];
    if (v == null || v === "") return [];
    return typeof v === "string" ? [v] : v;
  }
  function rjDays(day, today) {
    if (!day || !today) return null;
    var a = Date.parse(String(day).slice(0, 10) + "T00:00:00Z");
    var b = Date.parse(String(today).slice(0, 10) + "T00:00:00Z");
    if (isNaN(a) || isNaN(b)) return null;
    return Math.round((b - a) / 86400000);
  }
  function rjJobMatches(job, state, today, ignoreAgg) {
    var keys, i, key, want, age, ok, have, hit, w, n;
    state = state || {};
    if (job.agg && !ignoreAgg && (state.company || []).indexOf(job.company) < 0) return false;
    if (rjFold(state.q || "") && rjFold(job.text || "").indexOf(rjFold(state.q || "")) < 0) return false;
    keys = rjKeys();
    for (i = 0; i < keys.length; i++) {
      key = keys[i];
      want = state[key];
      if (!want || !want.length) continue;
      if (key === "posted") {
        age = rjDays(job.posted, today);
        ok = false;
        if (age != null && age >= 0) for (n = 0; n < want.length; n++) if (age <= (+want[n] || 0)) ok = true;
        if (!ok) return false;
        continue;
      }
      have = rjHave(job, key);
      hit = false;
      for (w = 0; w < want.length; w++) if (have.indexOf(want[w]) >= 0) { hit = true; break; }
      if (!hit) return false;
    }
    return true;
  }
  function rjFacetCounts(jobs, state, facet, today, buckets) {
    var scoped = rjBlank(), keys = rjKeys(), i, counts = {}, job, ignore, age, have, t, b, list;
    scoped.q = state.q || "";
    for (i = 0; i < keys.length; i++) if (keys[i] !== facet) scoped[keys[i]] = (state[keys[i]] || []).slice();
    list = buckets || ["7", "30", "90"];
    for (i = 0; i < jobs.length; i++) {
      job = jobs[i];
      ignore = facet === "company" && job.agg;
      if (!rjJobMatches(job, scoped, today, ignore)) continue;
      if (facet === "posted") {
        age = rjDays(job.posted, today);
        if (age == null || age < 0) continue;
        for (b = 0; b < list.length; b++) if (age <= (+list[b] || 0)) counts[list[b]] = (counts[list[b]] || 0) + 1;
        continue;
      }
      have = rjHave(job, facet);
      for (t = 0; t < have.length; t++) counts[have[t]] = (counts[have[t]] || 0) + 1;
    }
    return counts;
  }
  var lang = document.body.getAttribute("data-lang") || "vi";
  var L = lang === "en"
    ? { results: "results", more: "Show more", ad: "Ad", checked: "checked",
        filters: "Filters", apply: "Apply", clear: "Clear", clearAll: "Clear all", close: "Close",
        find: "Search", remove: "Remove",
        region: { vn: "Vietnam", apac: "APAC", global: "Worldwide", other: "Other / unclear" },
        remote: { yes: "Remote", hybrid: "Hybrid", no: "Onsite", unknown: "Remote: unclear" } }
    : { results: "kết quả", more: "Xem thêm", ad: "Quảng cáo", checked: "kiểm tra",
        filters: "Bộ lọc", apply: "Áp dụng", clear: "Xóa", clearAll: "Xóa tất cả", close: "Đóng",
        find: "Tìm", remove: "Bỏ",
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

  function norm(s) { return rjFold(s); }
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

  // ---- jobs list: page 1 is pre-rendered. Facets OR within a key and AND across keys.
  var jf = document.getElementById("job-filters");
  if (jf) {
    var list = document.getElementById("job-list"), pager = document.querySelector(".pager"), more = document.getElementById("job-more"), empty = document.getElementById("job-empty");
    var bar = document.getElementById("job-facets"), chips = document.getElementById("job-active"), openBtn = document.getElementById("job-filters-open"), clearBtn = document.getElementById("job-clear"), sheet = document.getElementById("job-sheet"), sheetBody = document.getElementById("job-sheet-body");
    var qInput = jf.querySelector('input[name="q"]'), original = list.innerHTML, idx = null, jobs = [], shown = 50, matches = [], draft = null, qt, barNext = bar.nextSibling;
    var state = rjParseFacetQuery(location.search);
    if (qInput) qInput.value = state.q || "";
    function today() { var d = new Date(); return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2); }
    function tok(s) { return s ? String(s).split(" ").filter(Boolean) : []; }
    function jobOf(r) { return {row: r, company: r[2], region: r[3], remote: r[4], role: tok(r[5]), agg: r[9] ? 1 : 0, skill: tok(r[10]), tz: tok(r[11]), level: tok(r[12]), group: r[13] || "", posted: r[14] || "", salary: r[8] ? "yes" : "", text: (r[1] || "") + " " + ((idx.cos && idx.cos[r[2]]) || "") + " " + (r[6] || "")}; }
    function nActive(st) { var n = st.q ? 1 : 0, k = rjKeys(), i; for (i = 0; i < k.length; i++) n += (st[k[i]] || []).length; return n; }
    function nMatch(st) { var t = today(), n = 0, i; for (i = 0; i < jobs.length; i++) if (rjJobMatches(jobs[i], st, t)) n++; return n; }
    function buckets(key) { var boxes, o, i; if (key !== "posted") return null; boxes = bar.querySelectorAll('.facet[data-k="posted"] input'); o = []; for (i = 0; i < boxes.length; i++) o.push(boxes[i].value); return o; }
    function labelOf(key, value) { var box; if (key === "q") return value; box = bar.querySelector('.facet[data-k="' + key + '"] input[value="' + value + '"]'); return box ? box.parentNode.querySelector(".lab").textContent : value; }
    function refresh(st) {
      var t, nodes, i, node, key, counts, sel, btn, num, boxes, b, box, on, c;
      if (!idx) return;
      t = today(); nodes = bar.querySelectorAll(".facet");
      for (i = 0; i < nodes.length; i++) {
        node = nodes[i]; key = node.getAttribute("data-k"); counts = rjFacetCounts(jobs, st, key, t, buckets(key)); sel = st[key] || [];
        btn = node.querySelector(".facet-btn");
        if (btn) { btn.setAttribute("aria-pressed", sel.length ? "true" : "false"); num = btn.querySelector(".n"); if (num) num.textContent = sel.length ? String(sel.length) : ""; }
        boxes = node.querySelectorAll('input[type="checkbox"]');
        for (b = 0; b < boxes.length; b++) { box = boxes[b]; on = sel.indexOf(box.value) >= 0; c = counts[box.value] || 0; box.checked = on; box.disabled = !on && !c; box.parentNode.classList.toggle("is-zero", !c && !on); num = box.parentNode.querySelector(".n"); if (num) num.textContent = String(c); }
      }
    }
    function paintChips() {
      var h = "", keys = rjKeys(), i, n, v, text, badge = document.getElementById("job-filters-n"), nAct;
      function aq(s) { return esc(s).replace(/"/g, "&quot;"); }
      if (state.q) h += '<button type="button" class="chip-x" data-k="q" aria-label="' + aq(L.remove + " " + state.q) + '">' + esc(state.q) + " ×</button>";
      for (i = 0; i < keys.length; i++) for (n = 0; n < (state[keys[i]] || []).length; n++) { v = state[keys[i]][n]; text = labelOf(keys[i], v); h += '<button type="button" class="chip-x" data-k="' + keys[i] + '" data-v="' + aq(v) + '" aria-label="' + aq(L.remove + " " + text) + '">' + esc(text) + " ×</button>"; }
      chips.innerHTML = h; nAct = nActive(state); clearBtn.hidden = !nAct; if (badge) badge.textContent = nAct ? String(nAct) : ""; if (openBtn) openBtn.setAttribute("aria-pressed", nAct ? "true" : "false");
    }
    function row(j) {
      var co = idx.cos[j[2]] || j[2];
      return '<li class="card job-card"><a class="t" href="' + prefix + "/viec-lam/" + j[0] + '/">' + esc(j[1]) + '</a><div class="meta"><a class="co" href="' + prefix + "/cong-ty/" + j[2] + '/">' + esc(co) + "</a>" + (j[6] ? '<span class="loc">' + esc(j[6]) + "</span>" : "") + '</div><div class="tags"><span class="b r-' + j[3] + '">' + (L.region[j[3]] || "") + '</span><span class="b m-' + j[4] + '">' + (L.remote[j[4]] || "") + "</span>" + (j[8] ? '<span class="b sal">💰 ' + esc(j[8]) + "</span>" : "") + '<span class="b date">✓ ' + L.checked + " " + fmtDate(j[7]) + "</span></div></li>";
    }
    function render() {
      var every = Math.min(15, Math.max(10, idx.every || 12)), html = [], i;
      for (i = 0; i < matches.length && i < shown; i++) { html.push(row(matches[i])); if (idx.ad && (i + 1) % every === 0 && i + 1 < Math.min(shown, matches.length)) html.push('<li class="slot slot-native"><span class="label">' + L.ad + '</span><a href="' + prefix + idx.ad.url + '">' + esc(idx.ad[lang]) + "</a></li>"); }
      list.innerHTML = html.join(""); empty.hidden = matches.length > 0; more.innerHTML = matches.length > shown ? '<button type="button" class="btn">' + L.more + " (" + (matches.length - shown) + ")</button>" : "";
    }
    function run2() {
      var t, i; if (!idx) return;
      if (!nActive(state)) { list.innerHTML = original; more.innerHTML = ""; empty.hidden = true; if (pager) pager.hidden = false; jf.elements.count.value = ""; return; }
      t = today(); matches = []; for (i = 0; i < jobs.length; i++) if (rjJobMatches(jobs[i], state, t)) matches.push(jobs[i].row);
      shown = 50; if (pager) pager.hidden = true; jf.elements.count.value = matches.length + " " + L.results; render();
    }
    function commit(mode) {
      var q = rjSerializeFacetQuery(state), next = location.pathname + (q ? "?" + q : "");
      refresh(state); paintChips();
      if (mode && next !== location.pathname + location.search) history[(mode === "replace" && history.state && history.state.rjf) ? "replaceState" : "pushState"]({rjf: 1}, "", next);
      run2();
    }
    function closePops() { var p = bar.querySelectorAll(".facet-pop"), b = bar.querySelectorAll(".facet-btn"), i; for (i = 0; i < p.length; i++) p[i].hidden = true; for (i = 0; i < b.length; i++) b[i].setAttribute("aria-expanded", "false"); }
    function setVal(st, key, value, on) { var list, at; if (key === "q") { st.q = on ? value : ""; return; } list = st[key]; at = list.indexOf(value); if (on && at < 0) list.push(value); if (!on && at >= 0) list.splice(at, 1); }
    function sheetNote() { var a = sheet.querySelector("[data-sheet-apply]"); if (qInput) draft.q = qInput.value; if (a) a.textContent = L.apply + " · " + nMatch(draft) + " " + L.results; refresh(draft); }
    function park(inSheet) {
      var pops, i;
      if (inSheet) { sheetBody.appendChild(bar); pops = bar.querySelectorAll(".facet-pop"); for (i = 0; i < pops.length; i++) pops[i].hidden = false; }
      else { barNext.parentNode.insertBefore(bar, barNext); closePops(); }
    }
    jf.addEventListener("change", function (e) {
      var box = e.target, facet, st;
      if (!box || box.type !== "checkbox") return;
      facet = box.closest(".facet"); if (!facet) return;
      st = (sheet.open && draft) ? draft : state;
      setVal(st, facet.getAttribute("data-k"), box.value, box.checked);
      if (st === draft) sheetNote(); else commit("push");
    });
    bar.addEventListener("input", function (e) {
      var n, labs, i; if (!e.target.classList || !e.target.classList.contains("facet-q")) return;
      n = rjFold(e.target.value); labs = e.target.parentNode.querySelectorAll("label.opt");
      for (i = 0; i < labs.length; i++) labs[i].hidden = !!(n && rjFold(labs[i].getAttribute("data-t")).indexOf(n) < 0);
    });
    bar.addEventListener("click", function (e) {
      var btn = e.target.closest(".facet-btn"), pop, first;
      if (!btn || sheet.open) return;
      pop = document.getElementById(btn.getAttribute("aria-controls"));
      if (btn.getAttribute("aria-expanded") === "true") { closePops(); return; }
      closePops(); btn.setAttribute("aria-expanded", "true"); pop.hidden = false; first = pop.querySelector("input"); if (first) first.focus();
    });
    bar.addEventListener("keydown", function (e) {
      var pop, boxes, all, i, at, next;
      if (sheet.open) return;
      if (e.key === "Escape") { pop = e.target.closest && e.target.closest(".facet-pop"); closePops(); if (pop) { var b = document.getElementById(pop.getAttribute("aria-labelledby")); if (b) b.focus(); } return; }
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      pop = e.target.closest && e.target.closest(".facet-pop");
      if (!pop) { if (e.key === "ArrowDown" && e.target.classList && e.target.classList.contains("facet-btn")) { e.preventDefault(); e.target.click(); } return; }
      boxes = []; all = pop.querySelectorAll('input[type="checkbox"]');
      for (i = 0; i < all.length; i++) if (!all[i].disabled && !all[i].parentNode.hidden) boxes.push(all[i]);
      if (!boxes.length) return;
      e.preventDefault(); at = boxes.indexOf(document.activeElement); next = e.key === "ArrowDown" ? at + 1 : at - 1;
      if (next < 0) next = boxes.length - 1; if (next >= boxes.length) next = 0; boxes[next].focus();
    });
    document.addEventListener("click", function (e) { if (!sheet.open && !bar.contains(e.target)) closePops(); });
    chips.addEventListener("click", function (e) {
      var b = e.target.closest(".chip-x"); if (!b) return;
      if (b.getAttribute("data-k") === "q") { state.q = ""; if (qInput) qInput.value = ""; } else setVal(state, b.getAttribute("data-k"), b.getAttribute("data-v"), false);
      commit("push");
    });
    function clearAll() { state = rjBlank(); draft = null; if (qInput) qInput.value = ""; if (sheet.open) sheet.close(); commit("push"); }
    clearBtn.addEventListener("click", clearAll);
    if (empty) empty.addEventListener("click", function (e) { if (e.target.closest("[data-job-clear]")) clearAll(); });
    sheet.addEventListener("click", function (e) {
      var keys, i, keep;
      if (e.target === sheet || (e.target.closest && e.target.closest("[data-sheet-x]"))) { sheet.close(); return; }
      if (e.target.closest && e.target.closest("[data-sheet-clear]")) { keep = draft ? draft.q : ""; draft = rjBlank(); draft.q = keep || ""; sheetNote(); return; }
      if (!e.target.closest || !e.target.closest("[data-sheet-apply]")) return;
      keys = rjKeys(); for (i = 0; i < keys.length; i++) state[keys[i]] = (draft[keys[i]] || []).slice(); draft = null; sheet.close(); commit("push");
    });
    sheet.addEventListener("close", function () { draft = null; park(false); if (openBtn) openBtn.setAttribute("aria-expanded", "false"); refresh(state); });
    if (openBtn) openBtn.addEventListener("click", function () {
      draft = rjParseFacetQuery("?" + rjSerializeFacetQuery(state)); park(true); sheetNote();
      if (sheet.showModal) sheet.showModal(); openBtn.setAttribute("aria-expanded", "true");
    });
    if (qInput) qInput.addEventListener("input", function () { state.q = qInput.value; if (draft) sheetNote(); clearTimeout(qt); qt = setTimeout(function () { commit("replace"); }, 200); });
    jf.addEventListener("submit", function (e) { e.preventDefault(); });
    window.addEventListener("popstate", function () { clearTimeout(qt); state = rjParseFacetQuery(location.search); if (qInput) qInput.value = state.q || ""; if (sheet.open) sheet.close(); commit(""); });
    more.addEventListener("click", function () { shown += 50; render(); });
    fetch(list.dataset.index).then(function (r) { return r.json(); }).then(function (d) {
      var i; idx = d; jobs = []; for (i = 0; i < idx.jobs.length; i++) jobs.push(jobOf(idx.jobs[i]));
      jf.hidden = false; if (openBtn) openBtn.hidden = false; commit("");
    }).catch(function () {});
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
