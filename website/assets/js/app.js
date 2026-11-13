/* Site behaviour: language and theme switches, mobile menu, scroll reveal, list filters, offline support. */
(function () {
  "use strict";
  var root = document.documentElement;

  function save(key, value) { try { localStorage.setItem(key, value); } catch (e) {} }

  /* ---------- language ---------- */
  function applyLang(lang) {
    root.lang = lang;
    var title = root.getAttribute("data-title-" + lang);
    if (title) document.title = title;
    var desc = root.getAttribute("data-desc-" + lang);
    var meta = document.querySelector('meta[name="description"]');
    if (desc && meta) meta.setAttribute("content", desc);
    document.querySelectorAll("[data-set-lang]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-set-lang") === lang));
    });
    document.querySelectorAll("[data-placeholder-" + lang + "]").forEach(function (el) {
      el.setAttribute("placeholder", el.getAttribute("data-placeholder-" + lang));
    });
    document.dispatchEvent(new CustomEvent("langchange", { detail: lang }));
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-set-lang]");
    if (!b) return;
    var lang = b.getAttribute("data-set-lang");
    save("lang", lang);
    applyLang(lang);
  });

  /* ---------- theme ---------- */
  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", theme === "light" ? "#F7F6FB" : "#0C0D16");
    document.querySelectorAll("[data-theme-toggle]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(theme === "light"));
    });
  }
  document.addEventListener("click", function (e) {
    if (!e.target.closest("[data-theme-toggle]")) return;
    var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
    save("theme", next);
    applyTheme(next);
  });
  if (window.matchMedia) {
    var mq = matchMedia("(prefers-color-scheme: light)");
    var follow = function (ev) {
      var saved = null;
      try { saved = localStorage.getItem("theme"); } catch (e) {}
      if (saved !== "light" && saved !== "dark") applyTheme(ev.matches ? "light" : "dark");
    };
    if (mq.addEventListener) mq.addEventListener("change", follow);
  }

  /* ---------- mobile menu ---------- */
  var drawer = document.getElementById("drawer");
  var menuBtn = document.querySelector("[data-menu]");
  function setMenu(open) {
    if (!drawer || !menuBtn) return;
    drawer.hidden = !open;
    menuBtn.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("no-scroll", open);
  }
  if (menuBtn) menuBtn.addEventListener("click", function () { setMenu(drawer.hidden); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && drawer && !drawer.hidden) setMenu(false); });
  window.addEventListener("resize", function () { if (window.innerWidth > 1180) setMenu(false); });

  /* ---------- filters ----------
     <div data-filters="#list"> holds rows [data-key]; each row has chips [data-value] ("all" matches everything).
     Items in the list carry data-<key>="value" (space-separated for several values). */
  document.querySelectorAll("[data-filters]").forEach(function (box) {
    var list = document.querySelector(box.getAttribute("data-filters"));
    if (!list) return;
    var empty = document.querySelector(box.getAttribute("data-empty") || "#none");
    var state = {};
    function run() {
      var shown = 0;
      list.querySelectorAll("[data-item]").forEach(function (item) {
        var visible = Object.keys(state).every(function (key) {
          var want = state[key];
          if (want === "all") return true;
          return (item.getAttribute("data-" + key) || "").split(" ").indexOf(want) >= 0;
        });
        item.hidden = !visible;
        if (visible) shown++;
      });
      list.querySelectorAll("[data-count-of]").forEach(function (counter) {
        var col = document.getElementById(counter.getAttribute("data-count-of"));
        if (col) counter.textContent = col.querySelectorAll("[data-item]:not([hidden])").length;
      });
      if (empty) empty.hidden = shown > 0;
    }
    box.querySelectorAll("[data-key]").forEach(function (row) {
      var key = row.getAttribute("data-key");
      state[key] = "all";
      row.addEventListener("click", function (e) {
        var chip = e.target.closest("[data-value]");
        if (!chip) return;
        state[key] = chip.getAttribute("data-value");
        row.querySelectorAll("[data-value]").forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
        run();
      });
    });
    // A filter can be preset from the address, e.g. /updates/?product=sboard
    try {
      var params = new URLSearchParams(location.search);
      box.querySelectorAll("[data-key]").forEach(function (row) {
        var v = params.get(row.getAttribute("data-key"));
        var chip = v && row.querySelector('[data-value="' + v.replace(/"/g, "") + '"]');
        if (chip) chip.click();
      });
    } catch (e) {}
    run();
  });

  /* ---------- document anchors ----------
     Sections are numbered per language (#ru-3, #en-3). A link to one language jumps to the same section in the shown one. */
  function jump(hash) {
    var m = /^#([a-z]{2,3})-(\d+)$/.exec(hash || "");
    if (!m) return false;
    var el = document.getElementById(root.lang + "-" + m[2]) || document.getElementById(m[1] + "-" + m[2]);
    if (!el) return false;
    el.scrollIntoView();
    return true;
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest('a[href*="#"]');
    if (!a) return;
    var url = new URL(a.getAttribute("href"), location.href);
    if (url.pathname === location.pathname && /^#[a-z]{2,3}-\d+$/.test(url.hash)) {
      e.preventDefault();
      history.replaceState(null, "", url.hash);
      jump(url.hash);
    }
  });
  window.addEventListener("load", function () { if (location.hash) jump(location.hash); });

  /* ---------- reveal on scroll ---------- */
  var items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); seen.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });
    items.forEach(function (el) { seen.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- offline support ---------- */
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
    var hadController = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.register("/sw.js").catch(function () {});
    navigator.serviceWorker.addEventListener("controllerchange", function () {
      if (!hadController) { hadController = true; return; }
      var toast = document.getElementById("update-toast");
      if (toast) toast.hidden = false;
    });
  }
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-reload]")) location.reload();
  });

  applyLang(root.lang);
  applyTheme(root.getAttribute("data-theme") || "dark");
})();
