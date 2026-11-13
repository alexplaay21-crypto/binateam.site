/* Instant site search over a local index (/search-index.json), built with the site. Works offline once cached. */
(function () {
  "use strict";
  var dialog = document.getElementById("search");
  if (!dialog) return;
  var input = dialog.querySelector("input");
  var body = dialog.querySelector(".search-body");
  var strings = JSON.parse(document.getElementById("search-strings").textContent);
  var index = null, loading = null, selected = -1;

  function lang() { return document.documentElement.lang; }
  function s(key) { var v = strings[key] || {}; return v[lang()] || v.en || key; }
  function norm(t) { return (t || "").toLowerCase().replace(/ё/g, "е"); }
  function esc(t) { return t.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function load() {
    if (index) return Promise.resolve(index);
    if (!loading) {
      loading = fetch("/search-index.json").then(function (r) { return r.json(); }).then(function (data) {
        index = data.map(function (e) {
          var n = {};
          Object.keys(e.t).forEach(function (l) { n[l] = { t: norm(e.t[l]), x: norm(e.x[l] || "") }; });
          e.n = n;
          return e;
        });
        return index;
      }).catch(function (err) { loading = null; throw err; });
    }
    return loading;
  }

  /* Wraps every term in <mark>, working on the original text so case and letters are kept. */
  function mark(text, terms) {
    var low = norm(text), hits = [];
    terms.forEach(function (term) {
      var from = 0, at;
      while (term && (at = low.indexOf(term, from)) >= 0) { hits.push([at, at + term.length]); from = at + term.length; }
    });
    if (!hits.length) return esc(text);
    hits.sort(function (a, b) { return a[0] - b[0]; });
    var out = "", pos = 0;
    hits.forEach(function (h) {
      if (h[0] < pos) return;
      out += esc(text.slice(pos, h[0])) + "<mark>" + esc(text.slice(h[0], h[1])) + "</mark>";
      pos = h[1];
    });
    return out + esc(text.slice(pos));
  }

  function snippet(text, terms) {
    var low = norm(text), first = -1;
    terms.forEach(function (t) { var i = low.indexOf(t); if (i >= 0 && (first < 0 || i < first)) first = i; });
    if (first < 0) return text.slice(0, 150) + (text.length > 150 ? "…" : "");
    var start = Math.max(0, first - 50), end = Math.min(text.length, first + 110);
    return (start > 0 ? "…" : "") + text.slice(start, end) + (end < text.length ? "…" : "");
  }

  function render(query) {
    var terms = norm(query).split(/\s+/).filter(Boolean);
    selected = -1;
    if (!terms.length) { body.innerHTML = '<div class="search-hint">' + esc(s("hint")) + "</div>"; return; }
    var l = lang();
    var found = [];
    index.forEach(function (e) {
      var here = e.n[l] || e.n.en;
      var other = Object.keys(e.n).filter(function (k) { return k !== l; }).map(function (k) { return e.n[k]; });
      var score = 0;
      var all = terms.every(function (term) {
        var inTitle = here.t.indexOf(term) >= 0, inText = here.x.indexOf(term) >= 0;
        var elsewhere = other.some(function (o) { return o.t.indexOf(term) >= 0 || o.x.indexOf(term) >= 0; });
        if (inTitle) score += here.t.indexOf(term) === 0 ? 6 : 4;
        else if (inText) score += 1;
        else if (elsewhere) score += 0.5;
        return inTitle || inText || elsewhere;
      });
      if (all) found.push({ e: e, score: score + (e.w || 0) });
    });
    if (!found.length) { body.innerHTML = '<div class="search-hint">' + esc(s("nothing")) + "</div>"; return; }
    found.sort(function (a, b) { return b.score - a.score; });
    var order = ["page", "product", "update", "roadmap", "doc"], html = "";
    order.forEach(function (kind) {
      var group = found.filter(function (f) { return f.e.k === kind; }).slice(0, 8);
      if (!group.length) return;
      html += '<div class="search-group">' + esc(s("kind_" + kind)) + "</div>";
      group.forEach(function (f) {
        var t = f.e.t[l] || f.e.t.en, x = f.e.x[l] || f.e.x.en || "";
        html += '<a class="result" role="option" href="' + esc(f.e.u) + '"><div class="t">' + mark(t, terms) + "</div>" +
          (x ? '<div class="s">' + mark(snippet(x, terms), terms) + "</div>" : "") + "</a>";
      });
    });
    body.innerHTML = html;
  }

  function open() {
    if (dialog.open) return;
    if (dialog.showModal) dialog.showModal(); else dialog.setAttribute("open", "");
    input.value = "";
    input.focus();
    body.innerHTML = '<div class="search-hint">' + esc(s("loading")) + "</div>";
    load().then(function () { render(input.value); })
      .catch(function () { body.innerHTML = '<div class="search-hint">' + esc(s("error")) + "</div>"; });
  }
  function close() { if (dialog.open) dialog.close ? dialog.close() : dialog.removeAttribute("open"); }

  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-search-open]")) { e.preventDefault(); open(); }
    if (e.target.closest("[data-search-close]")) close();
  });
  dialog.addEventListener("click", function (e) {
    if (e.target === dialog) close();
    else if (e.target.closest(".result")) close();
  });
  document.addEventListener("keydown", function (e) {
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target.tagName || "")) || e.target.isContentEditable;
    if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) { e.preventDefault(); open(); }
    else if (e.key === "/" && !typing && !dialog.open) { e.preventDefault(); open(); }
  });
  input.addEventListener("input", function () { if (index) render(input.value); });
  input.addEventListener("keydown", function (e) {
    var results = body.querySelectorAll(".result");
    if (!results.length) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      selected = (selected + (e.key === "ArrowDown" ? 1 : -1) + results.length) % results.length;
      results.forEach(function (r, i) { r.setAttribute("aria-selected", String(i === selected)); });
      results[selected].scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter") {
      e.preventDefault();
      (results[selected] || results[0]).click();
    }
  });
  document.addEventListener("langchange", function () { if (dialog.open && index) render(input.value); });
})();
