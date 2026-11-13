/* Runs in <head> before the page is drawn: picks the language and the theme so nothing flashes.
   Language: ?lang= → saved choice → browser language → default. Theme: saved choice → system setting. */
(function () {
  var root = document.documentElement;
  var langs = (root.getAttribute("data-langs") || "ru,en").split(",");
  var fallback = root.getAttribute("data-default-lang") || langs[0];
  function ok(l) { return langs.indexOf(l) >= 0; }
  function store(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  var lang = null;
  try { lang = new URLSearchParams(location.search).get("lang"); } catch (e) {}
  if (!ok(lang)) lang = store("lang");
  if (!ok(lang)) {
    var nav = ((navigator.languages && navigator.languages[0]) || navigator.language || "").toLowerCase();
    var base = nav.split("-")[0];
    // Russian is the default for the CIS languages that read it more often than English.
    if (["uk", "be", "kk", "ky", "tg", "uz", "az", "hy", "ka"].indexOf(base) >= 0) base = "ru";
    lang = ok(base) ? base : (base ? "en" : fallback);
    if (!ok(lang)) lang = fallback;
  }
  root.lang = lang;
  var theme = store("theme");
  if (theme !== "light" && theme !== "dark") {
    theme = window.matchMedia && matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }
  root.setAttribute("data-theme", theme);
  root.classList.add("js");
})();
