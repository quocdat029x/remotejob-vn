// Progressive enhancement only: every page is fully rendered without this file.
// Adds client-side filtering to the company directory and the jobs list. No tracking, no cookies.
(function () {
  "use strict";
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
            (!q || norm(j[1] + " " + (idx.cos[j[2]] || "") + " " + j[6]).indexOf(q) >= 0);
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
})();
