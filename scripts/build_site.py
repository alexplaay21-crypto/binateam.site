#!/usr/bin/env python3
"""Builds binateam.site from website/ into a static folder for GitHub Pages.

    python3 scripts/build_site.py              # writes _site/
    python3 scripts/build_site.py --out DIR    # writes DIR/
    python3 scripts/build_site.py --check      # also fails on broken internal links (used by CI)

Content lives in website/:
  data/site.json        settings, languages, contacts
  data/i18n.json        interface texts
  data/products.json    product catalog (each product gets a page at its "path")
  data/updates.json     updates feed
  data/roadmap.json     roadmap
  data/status.json      service status (updated by hand)
  data/community.json   community categories
  content/*.md          the website's own Privacy Policy and Terms
Product documents (sBoard's PRIVACY.md and TERMS.md) are read from the repository root.

Every page carries all languages; assets/js/boot.js shows one. Adding a language: add its code to
site.json "languages" and a text for it next to each "ru"/"en" pair — missing texts fall back to the default.
"""
import hashlib
import html
import json
import os
import re
import shutil
import sys
from datetime import date
from html.parser import HTMLParser

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "website")
ARGS = sys.argv[1:]
OUT = os.path.abspath(ARGS[ARGS.index("--out") + 1]) if "--out" in ARGS else os.path.join(ROOT, "_site")


def load(name):
    return json.load(open(os.path.join(SRC, "data", name), encoding="utf-8"))


SITE = load("site.json")
I18N = load("i18n.json")
PRODUCTS = load("products.json")
UPDATES = load("updates.json")["updates"]
ROADMAP = load("roadmap.json")["items"]
STATUS = load("status.json")
COMMUNITY = load("community.json")
LANGS = SITE["languages"]
DEFAULT = SITE["default_language"]
EMAIL = SITE["email"]
GH = SITE["github"]
SEARCH = []      # search index entries
PAGES = []       # url paths for sitemap and offline cache


# ---------- texts ----------

def pick(value, lang):
    """A text in one language. Strings pass through; dicts fall back to the default language."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.get(lang) or value.get(DEFAULT) or next(iter(value.values()))


def multi(value, tag="span", raw=False):
    """Renders a translatable value: one copy per language, CSS shows the active one."""
    texts = [pick(value, l) for l in LANGS]
    conv = (lambda t: t) if raw else html.escape
    if len(set(texts)) == 1:
        return conv(texts[0])
    return "".join(f'<{tag} data-lang="{l}">{conv(t)}</{tag}>' for l, t in zip(LANGS, texts))


def t(key, **fmt):
    if key not in I18N:
        raise KeyError(f"i18n.json has no text for '{key}'")
    value = I18N[key]
    if fmt:
        value = {l: pick(value, l).format(**{k: pick(v, l) for k, v in fmt.items()}) for l in LANGS}
    return value


def tm(key, tag="span", **fmt):
    return multi(t(key, **fmt), tag)


def attr(value):
    return html.escape(value, quote=True)


def fmt_date(iso):
    if not iso:
        return {l: "" for l in LANGS}
    d = date.fromisoformat(iso)
    out = {}
    for l in LANGS:
        months = pick(I18N["months"], l).split(",")
        out[l] = pick(I18N["date_format"], l).format(d=d.day, m=months[d.month - 1], y=d.year)
    return out


# ---------- icons ----------

ICONS = {
    "swipe": '<path d="M4 16c2.5-5 5-7.5 7.5-5.5S16 13 20 6"/><circle cx="20" cy="6" r="1.6"/><circle cx="4" cy="16" r="1.6"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.8 3.9 5.8 3.9 9s-1.3 6.2-3.9 9c-2.6-2.8-3.9-5.8-3.9-9S9.4 5.8 12 3z"/>',
    "translate": '<path d="M4 5h9M8.5 3v2M6 9c1.5 3 3.8 5 7 6.2M11.5 5c-.8 4-2.8 7.2-6.5 9.5"/><path d="M13 21l4-9 4 9M14.4 18h5.2"/>',
    "mic": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/>',
    "sparkle": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    "tools": '<rect x="4" y="4" width="7" height="7" rx="2"/><rect x="13" y="4" width="7" height="7" rx="2"/><rect x="4" y="13" width="7" height="7" rx="2"/><path d="M16.5 13.5v6M13.5 16.5h6"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3"/>',
    "finger": '<path d="M12 11.5v2.5M8.6 8.3a5 5 0 0 1 8.4 3.7c0 2.4-.4 4.6-1.3 6.5M7 12c0 3 .6 5.3 1.8 7.4M5 9.5a8.7 8.7 0 0 1 14 0M12 15.8c-.1 1.9-.5 3.5-1.2 4.9"/>',
    "scan": '<path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16"/><rect x="7.5" y="8.5" width="9" height="7" rx="1.5"/>',
    "buoy": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.8"/><path d="M5.6 5.6l3.7 3.7M14.7 14.7l3.7 3.7M18.4 5.6l-3.7 3.7M9.3 14.7l-3.7 3.7"/>',
    "cloud": '<path d="M7 19h10.5a4.5 4.5 0 0 0 .6-8.96A6 6 0 0 0 6.5 11.5 3.75 3.75 0 0 0 7 19z"/>',
    "shield": '<path d="M12 3l7.5 3v5.6c0 4.6-3.2 8.3-7.5 9.4-4.3-1.1-7.5-4.8-7.5-9.4V6z"/><path d="M9 12l2.2 2.2L15.5 10"/>',
    "import": '<path d="M12 3v11M7.5 9.5L12 14l4.5-4.5"/><path d="M4 15v3.5A2.5 2.5 0 0 0 6.5 21h11a2.5 2.5 0 0 0 2.5-2.5V15"/>',
    "eyeoff": '<path d="M3 3l18 18M10.6 6.2A9.5 9.5 0 0 1 12 6c4.5 0 7.6 3.3 9 6-.6 1.2-1.5 2.4-2.6 3.5M6.5 7.4C4.9 8.6 3.7 10.2 3 12c1.4 2.7 4.5 6 9 6 1.6 0 3-.4 4.3-1"/><path d="M9.9 10a3 3 0 0 0 4.1 4.1"/>',
    "phone": '<rect x="6.5" y="2.5" width="11" height="19" rx="2.5"/><path d="M10.5 18.5h3"/>',
    "gift": '<rect x="4" y="9" width="16" height="11.5" rx="2"/><path d="M3 9h18M12 9v11.5M12 9c-1.5-3.5-5.5-4.5-5.5-2S9.5 9 12 9zm0 0c1.5-3.5 5.5-4.5 5.5-2S14.5 9 12 9z"/>',
    "download": '<path d="M12 4v11M7.5 10.5L12 15l4.5-4.5M5 20h14"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M3.5 7l8.5 6 8.5-6"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "code": '<path d="M8.5 8L4.5 12l4 4M15.5 8l4 4-4 4M13.5 5l-3 14"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4L6 18M18 6l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
    "doc": '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4M10 12h5M10 15.5h5"/>',
    "bug": '<rect x="7" y="8" width="10" height="12" rx="5"/><path d="M12 8v12M7 13H3.5M20.5 13H17M7.5 9.5L5 7M16.5 9.5L19 7M8 18l-2.5 2M16 18l2.5 2M9.5 8a2.5 2.5 0 0 1 5 0"/>',
    "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.6.5 1.1 1.3 1.1 2.2h5c0-.9.5-1.7 1.1-2.2A6 6 0 0 0 12 3z"/>',
    "thumb": '<path d="M7 11v9H4v-9zM7 11l4-8c1.7 0 2.8 1.3 2.5 3L13 9h5.3a2 2 0 0 1 2 2.4l-1.3 6.6a2.5 2.5 0 0 1-2.4 2H7"/>',
    "chat": '<path d="M5 18.5V6.5A2.5 2.5 0 0 1 7.5 4h9A2.5 2.5 0 0 1 19 6.5v7a2.5 2.5 0 0 1-2.5 2.5H9z"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "box": '<path d="M4 7.5L12 3l8 4.5v9L12 21l-8-4.5z"/><path d="M4 7.5L12 12l8-4.5M12 12v9"/>',
    "map": '<path d="M9 4L3.5 6v14L9 18l6 2 5.5-2V4L15 6z"/><path d="M9 4v14M15 6v14"/>',
    "pulse": '<path d="M3 12h4l2.5-6 5 12 2.5-6h4"/>',
    "users": '<circle cx="9" cy="8.5" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 5.2a3.5 3.5 0 0 1 0 6.6M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.3a2.6 2.6 0 0 1 5 .9c0 1.8-2.5 2.3-2.5 3.8M12 17h.01"/>',
    "home": '<path d="M4 11l8-7 8 7v9h-5.5v-6h-5v6H4z"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v4.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10"/>',
    "github": '<path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>',
}

LOGO = ('<svg viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="bt-g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#C9BEFF"/><stop offset=".55" stop-color="#8F7CFF"/><stop offset="1" stop-color="#5B45D9"/></linearGradient></defs>'
        '<rect width="64" height="64" rx="17" fill="url(#bt-g)"/>'
        '<path d="M23 17v30M23 17h11.5a7.5 7.5 0 0 1 0 15H23M23 32h13a7.5 7.5 0 0 1 0 15H23" fill="none" stroke="#fff" '
        'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def icon(name):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def img(src, alt, size, lazy=False, cls=""):
    """<picture> with a WebP copy when one sits next to the PNG."""
    webp = os.path.splitext(src)[0] + ".webp"
    load_attr = ' loading="lazy" decoding="async"' if lazy else ""
    tag = f'<img src="/{src}" alt="{attr(alt)}" width="{size}" height="{size}"{load_attr}{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>'
    if os.path.exists(os.path.join(SRC, webp)):
        return f'<picture><source srcset="/{webp}" type="image/webp">{tag}</picture>'
    return tag


# ---------- page frame ----------

NAV = [("/", "nav_home", "home"), ("/products/", "nav_products", "box"), ("/updates/", "nav_updates", "pulse"),
       ("/roadmap/", "nav_roadmap", "map"), ("/status/", "nav_status", "pulse"), ("/community/", "nav_community", "users"),
       ("/about/", "nav_about", "info"), ("/support/", "nav_support", "help")]
HEADER_NAV = ["/products/", "/updates/", "/roadmap/", "/status/", "/community/", "/about/", "/support/"]


def lang_buttons():
    return "".join(f'<button type="button" data-set-lang="{l}" aria-pressed="false" lang="{l}">{l.upper()}</button>' for l in LANGS)


def verification_tags():
    """Ownership tags for search engines: site.json -> "verification": {"google": "...", "yandex": "...", "bing": "..."}."""
    names = {"google": "google-site-verification", "yandex": "yandex-verification", "bing": "msvalidate.01"}
    return "".join(f'\n<meta name="{names[k]}" content="{attr(v)}">' for k, v in SITE.get("verification", {}).items() if v and k in names)


def structured_data(url):
    """Tells search engines that Bina Team is an organisation with this site, so the name finds it."""
    if url != "/":
        return ""
    org = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": SITE["domain"] + "/#org", "name": SITE["name"], "url": SITE["domain"] + "/",
         "logo": SITE["domain"] + "/assets/icons/icon-512.png", "sameAs": [SITE["github"]["repo"]]},
        {"@type": "WebSite", "@id": SITE["domain"] + "/#site", "name": SITE["name"], "alternateName": ["Bina Team official", "Bina Team — официальный сайт"],
         "url": SITE["domain"] + "/", "publisher": {"@id": SITE["domain"] + "/#org"}},
    ]}
    return '\n<script type="application/ld+json">' + json.dumps(org, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def page(url, title, desc, body, section=None, index=True, kind="page", search_text=None):
    """url: '/path/'. title/desc: {lang: text}. section: nav url to mark as current."""
    section = section or url
    if index:
        PAGES.append(url)
    if search_text is not None:
        SEARCH.append({"k": kind, "u": url, "w": 2, "t": {l: pick(title, l).split(" — ")[0] for l in LANGS},
                       "x": {l: pick(search_text, l) for l in LANGS}})
    full = {l: (pick(title, l) if pick(title, l).endswith(SITE["name"]) or pick(title, l).startswith(SITE["name"]) else f"{pick(title, l)} — {SITE['name']}") for l in LANGS}
    hide = "".join(f'html:not([lang="{l}"]) [data-lang="{l}"]{{display:none!important}}' for l in LANGS)
    meta_attrs = "".join(f' data-title-{l}="{attr(full[l])}" data-desc-{l}="{attr(pick(desc, l))}"' for l in LANGS)
    head_nav = "".join(f'<a href="{u}"{" aria-current=" + chr(34) + "page" + chr(34) if u == section else ""}>{tm(k)}</a>'
                       for u, k, _ in NAV if u in HEADER_NAV)
    drawer_nav = "".join(f'<a href="{u}"{" aria-current=" + chr(34) + "page" + chr(34) if u == section else ""}>{tm(k)}{icon("arrow")}</a>'
                         for u, k, _ in NAV)
    search_strings = {k: I18N[f"search_{k}"] for k in ("hint", "nothing", "loading", "error",
                                                       "kind_page", "kind_product", "kind_update", "kind_roadmap", "kind_doc")}
    boot = open(os.path.join(SRC, "assets", "js", "boot.js"), encoding="utf-8").read()
    canonical = SITE["domain"] + url
    footer_cols = [
        ("footer_company", [("/about/", tm("nav_about")), ("/updates/", tm("nav_updates")), ("/roadmap/", tm("nav_roadmap")), ("/status/", tm("nav_status"))]),
        ("footer_products", [("/products/", tm("footer_catalog"))] + [("/" + p["path"], multi(p["name"])) for p in PRODUCTS["products"]]),
        ("footer_help", [("/support/", tm("nav_support")), ("/community/", tm("nav_community")), ("/privacy/", tm("doc_privacy")), ("/terms/", tm("doc_terms"))]),
    ]
    cols = "".join(f'<div><h2>{tm(h)}</h2><ul>' + "".join(f'<li><a href="{u}">{n}</a></li>' for u, n in links) + "</ul></div>"
                   for h, links in footer_cols)
    return f"""<!doctype html>
<html lang="{DEFAULT}" data-langs="{",".join(LANGS)}" data-default-lang="{DEFAULT}"{meta_attrs}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(full[DEFAULT])}</title>
<meta name="description" content="{attr(pick(desc, DEFAULT))}">
<meta name="robots" content="{"index, follow, max-image-preview:large" if index else "noindex"}">
<link rel="canonical" href="{canonical}">{verification_tags()}{structured_data(url)}
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:title" content="{attr(full[DEFAULT])}">
<meta property="og:description" content="{attr(pick(desc, DEFAULT))}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE['domain']}/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0C0D16">
<meta name="color-scheme" content="dark light">
<link rel="icon" href="/assets/icons/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/icons/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="stylesheet" href="/assets/css/site.css">
<style>{hide}</style>
<script>{boot}</script>
<script src="/assets/js/app.js" defer></script>
<script src="/assets/js/search.js" defer></script>
</head>
<body>
<a class="skip" href="#main">{tm("skip")}</a>
<div class="glow" aria-hidden="true"></div>
<header class="site-header"><div class="wrap">
<a class="logo" href="/" aria-label="{SITE['name']}">{LOGO}<span>{SITE['name']}</span></a>
<nav class="main-nav" aria-label="Main">{head_nav}</nav>
<div class="header-tools">
<button class="search-btn" type="button" data-search-open aria-label="Search">{icon("search")}<span class="txt">{tm("search_button")}</span><kbd>/</kbd></button>
<div class="lang-switch" role="group" aria-label="Language">{lang_buttons()}</div>
<button class="icon-btn theme-btn" type="button" data-theme-toggle aria-pressed="false" aria-label="Theme"><span class="moon">{icon("moon")}</span><span class="sun">{icon("sun")}</span></button>
<button class="icon-btn menu-btn" type="button" data-menu aria-expanded="false" aria-controls="drawer" aria-label="Menu">{icon("menu")}</button>
</div>
</div></header>
<div class="drawer" id="drawer" hidden><nav aria-label="Mobile">{drawer_nav}</nav>
<div class="drawer-tools"><div class="lang-switch" role="group" aria-label="Language">{lang_buttons()}</div>
<button class="icon-btn theme-btn" type="button" data-theme-toggle aria-pressed="false" aria-label="Theme"><span class="moon">{icon("moon")}</span><span class="sun">{icon("sun")}</span></button></div></div>
<main id="main">
{body}
</main>
<footer class="site-footer"><div class="wrap">
<div class="foot-grid">
<div><a class="logo" href="/">{LOGO}<span>{SITE['name']}</span></a><p>{tm("footer_about")}</p></div>
{cols}
</div>
<div class="foot-bottom"><span>© {date.today().year} {SITE['name']}</span><span><a href="mailto:{EMAIL}">{EMAIL}</a></span></div>
</div></footer>
<dialog class="search-dialog" id="search" aria-label="Search">
<div class="search-top">{icon("search")}<input type="search" autocomplete="off" spellcheck="false" aria-label="Search"{"".join(f' data-placeholder-{l}="{attr(pick(I18N["search_placeholder"], l))}"' for l in LANGS)} placeholder="{attr(pick(I18N["search_placeholder"], DEFAULT))}"><button class="close" type="button" data-search-close>Esc</button></div>
<div class="search-body" role="listbox"></div>
</dialog>
<script type="application/json" id="search-strings">{json.dumps(search_strings, ensure_ascii=False)}</script>
<div class="toast" id="update-toast" role="status" hidden>{tm("update_ready")}<button class="btn small primary" type="button" data-reload>{tm("update_reload")}</button></div>
</body>
</html>
"""


def head(eyebrow_key, title_key, text_key=None, title_value=None, text_value=None):
    title = multi(title_value) if title_value is not None else tm(title_key)
    text = multi(text_value) if text_value is not None else (tm(text_key) if text_key else "")
    return (f'<div class="wrap page-head reveal"><div class="eyebrow">{tm(eyebrow_key)}</div><h1>{title}</h1>'
            + (f"<p>{text}</p>" if text else "") + "</div>")


def sec_head(title_key, text_key=None, more=None):
    more_html = f'<a class="more" href="{more[0]}">{tm(more[1])}{icon("arrow")}</a>' if more else ""
    text = f"<p>{tm(text_key)}</p>" if text_key else ""
    return f'<div class="sec-head reveal"><div><h2>{tm(title_key)}</h2>{text}</div>{more_html}</div>'


# ---------- shared pieces ----------

def product(pid):
    for p in PRODUCTS["products"]:
        if p["id"] == pid:
            return p
    return None


def product_name(pid):
    if pid == "website":
        return t("product_website")
    p = product(pid)
    return p["name"] if p else pid


STATUS_KEYS = {"released": "st_released", "beta": "st_beta", "in-development": "st_in_development", "planned": "st_planned",
               "completed": "st_completed", "in-progress": "st_in_progress", "on-hold": "st_on_hold",
               "operational": "st_operational", "degraded": "st_degraded", "partial-outage": "st_partial_outage",
               "major-outage": "st_major_outage", "maintenance": "st_maintenance"}


def badge(status):
    return f'<span class="badge s-{status}">{tm(STATUS_KEYS[status])}</span>'


def sorted_updates():
    return sorted(UPDATES, key=lambda u: u["date"], reverse=True)


def update_mini(u):
    d = fmt_date(u["date"])
    version = f' · {u["version"]}' if u.get("version") else ""
    return f"""<a class="card update-mini reveal" href="/updates/#{u['id']}">
<time datetime="{u['date']}">{multi(d)}</time>
<h3>{multi(u['title'])}</h3><p>{multi(u['description'])}</p>
<div class="faint" style="font-size:13.5px;margin-top:auto">{multi(product_name(u['product']))}{version}</div></a>"""


def task_card(item, mini=False):
    eta = multi(fmt_date(item["eta"])) if item.get("eta") and re.match(r"\d{4}-\d\d-\d\d$", item["eta"]) else (
        html.escape(item["eta"]) if item.get("eta") else tm("eta_unknown"))
    eta_label = tm("eta_done") if item["status"] == "completed" else tm("eta")
    if mini:
        return f"""<div class="card task reveal"><div class="icon-tile">{icon("map")}</div><div>
<h4>{multi(item['title'])}</h4><p>{multi(item['description'])}</p>
<div class="foot" style="justify-content:flex-start">{badge(item['status'])}<span>{multi(item['category'])}</span></div></div></div>"""
    return f"""<article class="card task" id="{item['id']}" data-item data-status="{item['status']}" data-product="{item['product']}">
{badge(item['status'])}<h4>{multi(item['title'])}</h4><p>{multi(item['description'])}</p>
<div class="foot"><span>{multi(item['category'])}{"" if pick(item['category'], DEFAULT) == pick(product_name(item['product']), DEFAULT) else " · " + multi(product_name(item['product']))}</span><span>{eta_label}: {eta}</span></div></article>"""


# ---------- documents ----------

def inline(text):
    out = html.escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w@./])([\w.+-]+@[\w-]+\.[\w.]+[a-z])", r'<a href="mailto:\1">\1</a>', out)
    out = re.sub(r"(?<![\w@/])((?:docs\.github\.com|github\.com)/[\w./#-]*[\w/])", r'<a href="https://\1" rel="noopener">\1</a>', out)
    return out


def render_md(md, lang):
    """The small Markdown subset of LegalDocs.kt and website/content: ### headings, _date_, • bullets, paragraphs."""
    when, toc, out, items, plain = "", [], [], [], []

    def flush():
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in md.strip().split("\n"):
        s = line.strip()
        if s == "---" or s.startswith("<!--") or s.startswith("# ") or s.startswith("## "):
            continue
        if s.startswith("### "):
            flush()
            toc.append((f"{lang}-{len(toc) + 1}", s[4:]))
            plain.append([s[4:], ""])
            out.append(f'<h3 id="{lang}-{len(toc)}">{inline(s[4:])}</h3>')
        elif s.startswith("_") and s.endswith("_") and not when:
            when = s.strip("_")
        elif s.startswith("• "):
            items.append(s[2:])
            if plain:
                plain[-1][1] += " " + s[2:]
        elif not s:
            flush()
        else:
            flush()
            first = len(toc) == 1 and not any(o.startswith("<p") for o in out)
            out.append(f'<p{" class=" + chr(34) + "intro" + chr(34) if first else ""}>{inline(s)}</p>')
            if plain:
                plain[-1][1] += " " + s
    flush()
    return when, toc, "\n".join(out), plain


def split_product_doc(spec):
    text = open(os.path.join(ROOT, spec["source"]), encoding="utf-8").read()
    ru_h, en_h = spec["ru_heading"], spec["en_heading"]
    ru = text[text.index(f"\n{ru_h}\n") + len(ru_h) + 2:text.index(f"\n{en_h}\n")]
    en = text[text.index(f"\n{en_h}\n") + len(en_h) + 2:]
    return {"ru": ru, "en": en}


def doc_page(url, texts, title, scope_note, others, section=None):
    """texts: {lang: markdown}. others: [(url, {lang: name})]."""
    sides, articles = [], []
    for lang in LANGS:
        md = texts.get(lang) or texts[DEFAULT]
        when, toc, body, plain = render_md(md, lang)
        chips = "".join(f'<li><a href="#{i}">{inline(x)}</a></li>' for i, x in toc)
        links = "".join(f'<a href="{u}">{html.escape(pick(n, lang))} →</a>' for u, n in others)
        sides.append(f'<div data-lang="{lang}"><p class="label">{html.escape(pick(I18N["doc_contents"], lang))}</p><ol>{chips}</ol>'
                     f'<div class="other">{links}</div></div>')
        articles.append(f"""<article class="card doc" data-lang="{lang}">
<p class="date">{html.escape(when)}</p>
{body}
</article>""")
        for n, (heading, text) in enumerate(plain, 1):
            anchor = f"{url}#{DEFAULT}-{n}"
            entry = next((e for e in SEARCH if e["u"] == anchor), None)
            if entry is None:
                entry = {"k": "doc", "u": anchor, "t": {}, "x": {}}
                SEARCH.append(entry)
            entry["t"][lang] = f"{pick(title, lang)}: {heading}"
            entry["x"][lang] = text.strip()
    body = f"""{head("doc_eyebrow", None, title_value=title, text_value=scope_note)}
<div class="wrap"><div class="doc-layout">
<aside class="card doc-side" aria-label="Contents">{"".join(sides)}</aside>
<div>{"".join(articles)}</div>
</div></div>"""
    return page(url, title, scope_note, body, section=section)


# ---------- pages ----------

def home():
    feat = product(PRODUCTS["featured"])
    latest = sorted_updates()[0]
    upcoming = [i for i in ROADMAP if i["status"] in ("in-progress", "planned")][:4]
    principles = [("eyeoff", "p1"), ("phone", "p2"), ("gift", "p3"), ("chat", "p4")]
    points = feat["feature_groups"][0]["items"][:2] + feat["feature_groups"][1]["items"][:2]
    body = f"""<div class="wrap">
<section class="hero">
<div class="reveal">
<div class="hero-mark">{LOGO}<span>{tm("home_badge")}</span></div>
<h1><span class="accent">{SITE['name']}</span></h1>
<p class="lead">{tm("home_lead")}</p>
<div class="actions"><a class="btn primary" href="/products/">{tm("home_cta_products")}{icon("arrow")}</a>
<a class="btn" href="/about/">{tm("home_cta_about")}</a></div>
</div>
<div class="composition reveal" aria-hidden="true">
<div class="comp-main">{img(feat["icon"], "", 148)}</div>
<div class="comp-card c2"><div class="k">{tm("home_latest")}</div><div class="v">{multi(latest["title"])}</div>
<div class="k" style="margin-top:4px">{multi(fmt_date(latest["date"]))}</div></div>
<div class="comp-card c1"><div class="row">{img(feat["icon"], "", 34)}<div><div class="v">{multi(feat["name"])} {feat["version"]}</div>
<div class="k">{multi(feat["platform"])}</div></div>{badge(feat["status"])}</div></div>
</div>
</section>

<section class="sec" aria-labelledby="featured-h">
<div class="sec-head reveal"><div><div class="eyebrow">{tm("home_featured_eyebrow")}</div><h2 id="featured-h">{multi(feat["name"])}</h2></div>
<a class="more" href="/products/">{tm("home_all_products")}{icon("arrow")}</a></div>
<div class="card featured reveal">
<div class="info">
<div class="title">{img(feat["icon"], pick(feat["name"], DEFAULT), 64, lazy=True)}<div><h3>{multi(feat["name"])}</h3><div class="faint">{multi(feat["platform"])}</div></div></div>
<p>{multi(feat["description"])}</p>
<div class="meta">{badge(feat["status"])}<span class="badge plain">{tm("version")} {feat["version"]}</span><span class="badge plain">{multi(feat["price"])}</span></div>
<div class="actions"><a class="btn primary" href="/{feat["path"]}">{tm("learn_more")}{icon("arrow")}</a>
<a class="btn" href="{feat["download"]}" rel="noopener">{icon("download")}{tm("download_apk")}</a></div>
</div>
<div class="points">{"".join(f'<div class="point"><div class="icon-tile">{icon(p["icon"])}</div><div><h4>{multi(p["title"])}</h4><p>{multi(p["text"])}</p></div></div>' for p in points)}</div>
</div>
<div class="card facts reveal" style="margin-top:16px">{"".join(f'<div class="fact"><b>{html.escape(f["value"])}</b><span>{multi(f)}</span></div>' for f in feat["facts"])}</div>
</section>

<section class="sec">
{sec_head("home_updates_title", "home_updates_text", ("/updates/", "all_updates"))}
<div class="grid-3">{"".join(update_mini(u) for u in sorted_updates()[:3])}</div>
</section>

<section class="sec">
{sec_head("home_roadmap_title", "home_roadmap_text", ("/roadmap/", "full_roadmap"))}
<div class="road-mini grid-2">{"".join(task_card(i, mini=True) for i in upcoming)}</div>
</section>

<section class="sec">
{sec_head("home_why_title")}
<div class="grid-4">{"".join(f'<div class="card pad principle reveal"><div class="icon-tile">{icon(i)}</div><h3>{tm(k + "_title")}</h3><p>{tm(k + "_text")}</p></div>' for i, k in principles)}</div>
</section>

<section class="sec">
<div class="card contact-band reveal"><div><h2>{tm("contact_title")}</h2><p>{tm("contact_text")}</p></div>
<div class="actions"><a class="btn primary" href="mailto:{EMAIL}">{icon("mail")}{EMAIL}</a><a class="btn" href="/community/">{icon("users")}{tm("nav_community")}</a></div></div>
</section>
</div>"""
    return page("/", t("home_title"), t("home_desc"), body,
                search_text={l: pick(t("home_lead"), l) for l in LANGS})


def products_page():
    items = PRODUCTS["products"]
    types = [("all", "filter_all"), ("app", "type_app"), ("game", "type_game")]
    counts = {"all": len(items), "app": sum(p["type"] == "app" for p in items), "game": sum(p["type"] == "game" for p in items)}
    chips = "".join(f'<button class="chip" type="button" data-value="{v}" aria-pressed="{str(v == "all").lower()}">{tm(k)}<span class="count">{counts[v]}</span></button>'
                    for v, k in types)
    cards = ""
    for p in items:
        gp = f'<a class="btn small" href="{p["google_play"]}" rel="noopener">Google Play</a>' if p.get("google_play") else ""
        cards += f"""<article class="card product-card reveal" data-item data-type="{p['type']}">
<div class="top">{img(p["icon"], pick(p["name"], DEFAULT), 56, lazy=True)}<div><h3>{multi(p["name"])}</h3><div class="type">{tm("type_" + p["type"])} · {multi(p["platform"])}</div></div></div>
<p>{multi(p["tagline"])}</p>
<div class="meta">{badge(p["status"])}<span class="badge plain">{tm("version")} {p["version"]}</span><span class="badge plain">{multi(p["price"])}</span></div>
<div class="links"><a class="btn small primary" href="/{p['path']}">{tm("learn_more")}</a>
<a class="btn small" href="{p['download']}" rel="noopener">{icon("download")}{tm("download_apk")}</a>{gp}
<a class="btn small ghost" href="/{p['support']}">{tm("nav_support")}</a></div>
</article>"""
        SEARCH.append({"k": "product", "u": "/" + p["path"], "w": 3, "t": {l: pick(p["name"], l) for l in LANGS},
                       "x": {l: " ".join([pick(p["tagline"], l), pick(p["description"], l)] +
                                         [pick(i["title"], l) + " " + pick(i["text"], l) for g in p["feature_groups"] for i in g["items"]]) for l in LANGS}})
    body = f"""{head("nav_products", "products_title", "products_text")}
<div class="wrap">
<div class="filters reveal" data-filters="#product-list" data-empty="#products-empty"><div class="filter-row" data-key="type"><span class="label">{tm("filter_type")}</span><div class="chips">{chips}</div></div></div>
<div class="grid-3" id="product-list">{cards}
<div class="add-slot reveal">{icon("box")}<div>{tm("products_more")}</div></div></div>
<div class="empty" id="products-empty" hidden>{tm("products_empty")}</div>
</div>"""
    return page("/products/", t("nav_products"), t("products_text"), body,
                search_text={l: pick(t("products_text"), l) for l in LANGS})


def product_page(p):
    url = "/" + p["path"]
    actions = [f'<a class="btn primary" href="{p["download"]}" rel="noopener">{icon("download")}{tm("download_apk")}</a>']
    if p.get("google_play"):
        actions.append(f'<a class="btn" href="{p["google_play"]}" rel="noopener">Google Play</a>')
    actions.append(f'<a class="btn" href="/{p["support"]}">{icon("help")}{tm("nav_support")}</a>')
    if p.get("source"):
        actions.append(f'<a class="btn ghost" href="{p["source"]}" rel="noopener">{icon("code")}{tm("source_code")}</a>')
    spec = [("version", p["version"]), ("status", None), ("platform", p["platform"]), ("price", p["price"])]
    spec_html = "".join(f'<div><dt>{tm("spec_" + k)}</dt><dd>{badge(p["status"]) if k == "status" else multi(v)}</dd></div>' for k, v in spec)
    groups = "".join(f"""<section class="sec">{f'<div class="sec-head reveal"><div><h2>{multi(g["title"])}</h2></div></div>'}
<div class="grid-3">{"".join(f'<div class="card pad feature reveal"><div class="icon-tile">{icon(i["icon"])}</div><h3>{multi(i["title"])}</h3><p>{multi(i["text"])}</p></div>' for i in g["items"])}</div></section>"""
                     for g in p["feature_groups"])
    if p["screenshots"]:
        def shot(s):
            # A plain path is the same picture for every language; {"file": {lang: path}} gives one
            # per language, and a language without its own shows the English picture.
            if isinstance(s, str):
                return f'<img src="/assets/products/{p["id"]}/{s}" alt="" loading="lazy" decoding="async">'
            def own(value, lang):
                return value.get(lang) or value.get("en") or pick(value, lang)
            files = [own(s["file"], l) for l in LANGS]
            tags = [f'<img src="/assets/products/{p["id"]}/{f}" alt="{html.escape(own(s.get("alt", {}), l), quote=True)}" width="540" height="960" loading="lazy" decoding="async"'
                    for l, f in zip(LANGS, files)]
            if len(set(files)) == 1:
                return tags[0] + ">"
            return "".join(f'{tag} data-lang="{l}">' for l, tag in zip(LANGS, tags))
        shots = "".join(shot(s) for s in p["screenshots"])
        shots_html = f'<div class="shots">{shots}</div>'
    else:
        shots_html = f'<div class="notice">{icon("info")}<div>{tm("shots_soon")}</div></div>'
    ups = [u for u in sorted_updates() if u["product"] == p["id"]][:3]
    road = [i for i in ROADMAP if i["product"] == p["id"] and i["status"] != "completed"]
    faq = "".join(f'<details class="card reveal"><summary>{multi(f["q"])}</summary><p>{multi(f["a"])}</p></details>' for f in p.get("faq", []))
    docs = "".join(f"""<a class="card doc-link reveal" href="{url}{kind}/"><div class="icon-tile">{icon("doc")}</div>
<div><h3>{tm("doc_" + kind)}</h3><p>{tm("doc_product_note", name=p["name"])}</p></div>{icon("arrow").replace("<svg", "<svg class=" + chr(34) + "arrow" + chr(34), 1)}</a>"""
                   for kind in p.get("documents", {}))
    body = f"""<div class="wrap">
<section class="product-hero">
<div class="reveal">
<div class="title">{img(p["icon"], pick(p["name"], DEFAULT), 80)}<div><div class="eyebrow" style="margin:0 0 6px">{tm("type_" + p["type"])}</div><h1>{multi(p["name"])}</h1></div></div>
<p class="tagline">{multi(p["tagline"])}</p>
<p class="desc">{multi(p["description"])}</p>
<div class="actions">{"".join(actions)}</div>
</div>
<dl class="card spec reveal">{spec_html}</dl>
</section>
<div class="card facts reveal">{"".join(f'<div class="fact"><b>{html.escape(f["value"])}</b><span>{multi(f)}</span></div>' for f in p["facts"])}</div>
<section class="sec"><div class="sec-head reveal"><div><h2>{tm("screenshots")}</h2></div></div>{shots_html}</section>
{groups}
<section class="sec">
{sec_head("product_updates", None, (f"/updates/?product={p['id']}", "all_updates"))}
<div class="grid-3">{"".join(update_mini(u) for u in ups)}</div>
</section>
{f'<section class="sec">{sec_head("product_roadmap", None, ("/roadmap/", "full_roadmap"))}<div class="road-mini grid-2">{"".join(task_card(i, mini=True) for i in road)}</div></section>' if road else ""}
{f'<section class="sec"><div class="sec-head reveal"><div><h2>{tm("faq")}</h2></div></div><div class="faq">{faq}</div></section>' if faq else ""}
<section class="sec"><div class="sec-head reveal"><div><h2>{tm("product_docs", name=p["name"])}</h2><p>{tm("product_docs_text")}</p></div></div><div class="doc-links">{docs}</div></section>
</div>"""
    title = {l: f"{pick(p['name'], l)} — {pick(p['tagline'], l)}" for l in LANGS}
    out = {p["path"] + "index.html": page(url, title, p["description"], body, section="/products/")}
    others_base = [(url, p["name"])]
    for kind, spec_doc in p.get("documents", {}).items():
        texts = split_product_doc(spec_doc)
        others = [(f"{url}{k}/", t("doc_" + k)) for k in p["documents"] if k != kind] + others_base + [(f"/{kind}/", t("doc_site_" + kind))]
        title_doc = {l: f"{pick(t('doc_' + kind), l)} {pick(p['name'], l)}" for l in LANGS}
        out[f"{p['path']}{kind}/index.html"] = doc_page(f"{url}{kind}/", texts, title_doc, t("doc_product_scope", name=p["name"]), others, section="/products/")
    return out


def updates_page():
    cats = [("all", "filter_all")] + [(c, "cat_" + c) for c in ("release", "feature", "fix", "website")]
    prods = [("all", None)] + [(p["id"], p["name"]) for p in PRODUCTS["products"]] + [("website", t("product_website"))]
    cat_chips = "".join(f'<button class="chip" type="button" data-value="{v}" aria-pressed="{str(v == "all").lower()}">{tm(k)}</button>' for v, k in cats)
    prod_chips = "".join(f'<button class="chip" type="button" data-value="{v}" aria-pressed="{str(v == "all").lower()}">{tm("filter_all") if n is None else multi(n)}</button>' for v, n in prods)
    entries = ""
    for u in sorted_updates():
        d = fmt_date(u["date"])
        feats = "".join(f"<li>{multi(x)}</li>" for x in u.get("features", []))
        fixes = "".join(f"<li>{multi(x)}</li>" for x in u.get("fixes", []))
        lists = ""
        if feats or fixes:
            lists = '<div class="lists">' + (f'<div><h4>{tm("new_features")}</h4><ul class="tick">{feats}</ul></div>' if feats else "") + \
                    (f'<div><h4>{tm("fixes")}</h4><ul class="tick fix">{fixes}</ul></div>' if fixes else "") + "</div>"
        version = f'<span class="badge plain">{tm("version")} {u["version"]}</span>' if u.get("version") else ""
        entries += f"""<article class="card update reveal" id="{u['id']}" data-item data-category="{u['category']}" data-product="{u['product']}">
<div><time datetime="{u['date']}">{multi(d)}</time><div class="tags"><span class="badge plain">{multi(product_name(u['product']))}</span>{version}<span class="badge s-planned">{tm("cat_" + u["category"])}</span></div></div>
<div><h3>{multi(u['title'])}</h3><p>{multi(u['description'])}</p>{lists}</div>
</article>"""
        SEARCH.append({"k": "update", "u": f"/updates/#{u['id']}", "t": {l: pick(u["title"], l) for l in LANGS},
                       "x": {l: " ".join([pick(u["description"], l)] + [pick(x, l) for x in u.get("features", []) + u.get("fixes", [])]) for l in LANGS}})
    body = f"""{head("nav_updates", "updates_title", "updates_text")}
<div class="wrap">
<div class="filters reveal" data-filters="#updates-list" data-empty="#updates-empty">
<div class="filter-row" data-key="category"><span class="label">{tm("filter_category")}</span><div class="chips">{cat_chips}</div></div>
<div class="filter-row" data-key="product"><span class="label">{tm("filter_product")}</span><div class="chips">{prod_chips}</div></div>
</div>
<div class="timeline" id="updates-list">{entries}</div>
<div class="empty" id="updates-empty" hidden>{tm("updates_empty")}</div>
<p class="faint" style="margin-top:18px;font-size:14px">{tm("updates_source")}</p>
</div>"""
    return page("/updates/", t("nav_updates"), t("updates_text"), body, search_text={l: pick(t("updates_text"), l) for l in LANGS})


def roadmap_page():
    order = ["in-progress", "planned", "on-hold", "completed"]
    status_chips = "".join(f'<button class="chip" type="button" data-value="{v}" aria-pressed="{str(v == "all").lower()}">{tm("filter_all") if v == "all" else tm(STATUS_KEYS[v])}</button>'
                           for v in ["all"] + order)
    prods = [("all", None)] + [(p["id"], p["name"]) for p in PRODUCTS["products"]] + [("website", t("product_website"))]
    prod_chips = "".join(f'<button class="chip" type="button" data-value="{v}" aria-pressed="{str(v == "all").lower()}">{tm("filter_all") if n is None else multi(n)}</button>' for v, n in prods)
    cols = ""
    for s in order:
        items = [i for i in ROADMAP if i["status"] == s]
        cards = "".join(task_card(i) for i in items)
        cols += f"""<div class="column" id="col-{s}"><h3>{tm(STATUS_KEYS[s])}<span class="count" data-count-of="col-{s}">{len(items)}</span></h3>
<div class="stack">{cards or f'<div class="faint" style="font-size:14px;padding:8px">{tm("roadmap_column_empty")}</div>'}</div></div>"""
    for i in ROADMAP:
        SEARCH.append({"k": "roadmap", "u": f"/roadmap/#{i['id']}", "t": {l: pick(i["title"], l) for l in LANGS},
                       "x": {l: pick(i["description"], l) + " " + pick(i["category"], l) for l in LANGS}})
    body = f"""{head("nav_roadmap", "roadmap_title", "roadmap_text")}
<div class="wrap" id="roadmap-board">
<div class="filters reveal" data-filters="#roadmap-board" data-empty="#roadmap-empty">
<div class="filter-row" data-key="status"><span class="label">{tm("filter_status")}</span><div class="chips">{status_chips}</div></div>
<div class="filter-row" data-key="product"><span class="label">{tm("filter_product")}</span><div class="chips">{prod_chips}</div></div>
</div>
<div class="board">{cols}</div>
<div class="empty" id="roadmap-empty" hidden style="margin-top:14px">{tm("roadmap_empty")}</div>
<p class="faint" style="margin-top:18px;font-size:14px">{tm("roadmap_note")}</p>
</div>"""
    return page("/roadmap/", t("nav_roadmap"), t("roadmap_text"), body, search_text={l: pick(t("roadmap_text"), l) for l in LANGS})


SEVERITY = ["operational", "maintenance", "degraded", "partial-outage", "major-outage"]


def status_page():
    services = STATUS["services"]
    worst = max((s["status"] for s in services), key=SEVERITY.index) if services else "operational"
    updated = fmt_date(STATUS["updated"])
    rows = "".join(f"""<div class="service"><div><h3>{multi(s['name'])}</h3><p>{multi(s['description'])}</p></div>{badge(s['status'])}</div>""" for s in services)
    incidents = ""
    for inc in STATUS.get("incidents", []):
        incidents += f"""<article class="card pad reveal"><div class="faint" style="font-size:14px">{multi(fmt_date(inc['date']))}</div>
<h3 style="font-size:17px;margin:6px 0">{multi(inc['title'])} {badge(inc['status'])}</h3><p class="muted">{multi(inc['text'])}</p></article>"""
    legend = "".join(f'<div style="display:flex;gap:10px;align-items:baseline">{badge(s)}<span class="muted" style="font-size:14px">{tm("legend_" + s.replace("-", "_"))}</span></div>' for s in SEVERITY)
    body = f"""{head("nav_status", "status_title", "status_text")}
<div class="wrap" style="display:grid;gap:16px">
<div class="card overall s-{worst} reveal"><span class="dot" aria-hidden="true"></span><div><h2>{tm("overall_" + worst.replace("-", "_"))}</h2>
<p>{tm("status_updated", when=updated)}</p></div></div>
<div class="notice reveal">{icon("info")}<div>{tm("status_manual", email=EMAIL)}</div></div>
<div class="card services reveal">{rows}</div>
<section class="sec" style="padding-bottom:0"><div class="sec-head reveal"><div><h2>{tm("incidents")}</h2></div></div>
{incidents or f'<div class="empty reveal">{tm("incidents_none")}</div>'}</section>
<section class="sec"><div class="sec-head reveal"><div><h2>{tm("legend")}</h2></div></div><div class="card pad legend reveal" style="display:grid;gap:12px">{legend}</div></section>
</div>"""
    return page("/status/", t("nav_status"), t("status_text"), body, search_text={l: pick(t("status_text"), l) for l in LANGS})


def issue_url(template, title=""):
    from urllib.parse import quote
    q = f"?template={template}" + (f"&title={quote(title)}" if title else "")
    return f"{GH['issues']}/new{q}"


def issue_search(query):
    from urllib.parse import quote
    return f"{GH['issues']}?q={quote(query)}"


def community_page():
    ideas_all = issue_search('is:issue is:open "[idea]" in:title sort:reactions-+1-desc')
    actions = [
        ("bulb", "comm_idea_title", "comm_idea_text", issue_url("idea.yml", "[idea] "), "comm_idea_btn"),
        ("bug", "comm_bug_title", "comm_bug_text", issue_url("bug.yml", "[bug] "), "comm_bug_btn"),
        ("thumb", "comm_vote_title", "comm_vote_text", ideas_all, "comm_vote_btn"),
    ]
    if GH.get("discussions_enabled"):
        actions.append(("chat", "comm_disc_title", "comm_disc_text", GH["discussions"], "comm_disc_btn"))
    cards = "".join(f"""<div class="card channel reveal"><div class="icon-tile">{icon(i)}</div><h3>{tm(a)}</h3><p>{tm(b)}</p>
<div class="actions"><a class="btn primary small" href="{u}" rel="noopener">{tm(c)}{icon("external")}</a></div></div>""" for i, a, b, u, c in actions)
    cats = ""
    for c in COMMUNITY["categories"]:
        tag = f"[{c['tag']}]"
        cats += f"""<div class="card cat-card reveal"><div class="icon-tile">{icon(c['icon'])}</div><h3>{multi(c['name'])}</h3>
<div class="links"><a class="btn small" href="{issue_search(f'is:issue "{tag}" in:title sort:reactions-+1-desc')}" rel="noopener">{tm("comm_cat_see")}</a>
<a class="btn small primary" href="{issue_url("idea.yml", f"[idea] {tag} ")}" rel="noopener">{tm("comm_cat_suggest")}</a></div></div>"""
    disc_note = "" if GH.get("discussions_enabled") else f'<p class="faint" style="font-size:14px;margin-top:12px">{tm("comm_disc_off")}</p>'
    body = f"""{head("nav_community", "comm_title", "comm_text")}
<div class="wrap">
<div class="grid-3">{cards}</div>
{disc_note}
<section class="sec"><div class="sec-head reveal"><div><h2>{tm("comm_cats_title")}</h2><p>{tm("comm_cats_text")}</p></div></div><div class="grid-2">{cats}</div></section>
<section class="sec"><div class="sec-head reveal"><div><h2>{tm("comm_how_title")}</h2></div></div>
<ol class="steps reveal"><li>{tm("comm_how_1")}</li><li>{tm("comm_how_2")}</li><li>{tm("comm_how_3")}</li><li>{tm("comm_how_4")}</li></ol></section>
<div class="notice reveal">{icon("shield")}<div>{tm("comm_rules")}</div></div>
</div>"""
    return page("/community/", t("nav_community"), t("comm_text"), body, search_text={l: pick(t("comm_text"), l) + " " + pick(t("comm_how_1"), l) for l in LANGS})


def about_page():
    facts = [(k, v) for k, v in SITE["about"].items() if not k.startswith("_") and v]
    facts_html = ""
    if facts:
        facts_html = '<div class="card facts reveal" style="margin-top:24px">' + "".join(
            f'<div class="fact"><b>{multi(v)}</b><span>{tm("about_fact_" + k)}</span></div>' for k, v in facts) + "</div>"
    principles = [("eyeoff", "p1"), ("phone", "p2"), ("gift", "p3"), ("chat", "p4")]
    prods = "".join(f"""<a class="card product-card reveal" href="/{p['path']}"><div class="top">{img(p["icon"], pick(p["name"], DEFAULT), 56, lazy=True)}
<div><h3>{multi(p["name"])}</h3><div class="type">{tm("type_" + p["type"])} · {multi(p["platform"])}</div></div></div><p>{multi(p["tagline"])}</p></a>""" for p in PRODUCTS["products"])
    body = f"""{head("nav_about", "about_title", "about_text")}
<div class="wrap">
<div class="prose reveal"><p>{tm("about_p1")}</p><p>{tm("about_p2")}</p></div>
{facts_html}
<section class="sec"><div class="sec-head reveal"><div><h2>{tm("home_why_title")}</h2></div></div>
<div class="grid-4">{"".join(f'<div class="card pad principle reveal"><div class="icon-tile">{icon(i)}</div><h3>{tm(k + "_title")}</h3><p>{tm(k + "_text")}</p></div>' for i, k in principles)}</div></section>
<section class="sec"><div class="sec-head reveal"><div><h2>{tm("nav_products")}</h2></div></div><div class="grid-3">{prods}</div></section>
<div class="card contact-band reveal"><div><h2>{tm("contact_title")}</h2><p>{tm("contact_text")}</p></div>
<div class="actions"><a class="btn primary" href="mailto:{EMAIL}">{icon("mail")}{EMAIL}</a><a class="btn" href="{GH['repo']}" rel="noopener">{icon("github")}GitHub</a></div></div>
</div>"""
    return page("/about/", t("nav_about"), t("about_text"), body,
                search_text={l: " ".join(pick(t(k), l) for k in ("about_text", "about_p1", "about_p2")) for l in LANGS})


def support_page():
    channels = [
        ("mail", "sup_mail_title", "sup_mail_text", f"mailto:{EMAIL}", EMAIL, False),
        ("bug", "sup_bug_title", "sup_bug_text", issue_url("bug.yml", "[bug] "), t("comm_bug_btn"), True),
        ("bulb", "sup_idea_title", "sup_idea_text", "/community/", t("nav_community"), False),
        ("pulse", "sup_status_title", "sup_status_text", "/status/", t("nav_status"), False),
    ]
    cards = "".join(f"""<div class="card channel reveal"><div class="icon-tile">{icon(i)}</div><h3>{tm(a)}</h3><p>{tm(b)}</p>
<div class="actions"><a class="btn small{' primary' if n == 0 else ''}" href="{u}"{' rel="noopener"' if ext else ''}>{multi(label) if isinstance(label, dict) else html.escape(label)}</a></div></div>"""
                    for n, (i, a, b, u, label, ext) in enumerate(channels))
    prod_blocks = ""
    for p in PRODUCTS["products"]:
        faq = "".join(f'<details class="card reveal"><summary>{multi(f["q"])}</summary><p>{multi(f["a"])}</p></details>' for f in p.get("faq", []))
        docs = "".join(f'<a class="btn small" href="/{p["path"]}{k}/">{tm("doc_" + k)}</a>' for k in p.get("documents", {}))
        prod_blocks += f"""<section class="sec" id="{p['id']}"><div class="sec-head reveal"><div><h2>{tm("sup_product_title", name=p["name"])}</h2><p>{tm("sup_product_text")}</p></div></div>
<ol class="steps reveal"><li>{tm("sup_steps_1")}</li><li>{tm("sup_steps_2")}</li><li>{tm("sup_steps_3")}</li></ol>
<div class="faq" style="margin-top:16px">{faq}</div>
<div class="actions reveal" style="margin-top:16px"><a class="btn small primary" href="/{p['path']}">{multi(p["name"])}</a>{docs}</div></section>"""
    body = f"""{head("nav_support", "sup_title", "sup_text")}
<div class="wrap">
<div class="grid-4">{cards}</div>
<div class="notice reveal" style="margin-top:16px">{icon("shield")}<div>{tm("sup_privacy")}</div></div>
{prod_blocks}
</div>"""
    return page("/support/", t("nav_support"), t("sup_text"), body,
                search_text={l: " ".join(pick(t(k), l) for k in ("sup_text", "sup_mail_text", "sup_bug_text", "sup_steps_1")) for l in LANGS})


def site_doc(kind):
    texts = {l: open(os.path.join(SRC, "content", f"{kind}.{l}.md"), encoding="utf-8").read()
             for l in LANGS if os.path.exists(os.path.join(SRC, "content", f"{kind}.{l}.md"))}
    other = "terms" if kind == "privacy" else "privacy"
    others = [(f"/{other}/", t("doc_" + other))] + [(f"/{p['path']}{kind}/", t("doc_product_link", name=p["name"]))
                                                     for p in PRODUCTS["products"] if kind in p.get("documents", {})]
    return doc_page(f"/{kind}/", texts, t("doc_site_" + kind), t("doc_site_scope"), others)


def not_found():
    body = f"""<div class="wrap page-head" style="text-align:center;padding:110px 0 60px">
<div class="eyebrow">404</div><h1 style="margin:0 auto">{tm("nf_title")}</h1><p style="margin:16px auto 28px">{tm("nf_text")}</p>
<div class="actions" style="justify-content:center"><a class="btn primary" href="/">{tm("nav_home")}</a><a class="btn" href="/products/">{tm("nav_products")}</a>
<button class="btn" type="button" data-search-open>{icon("search")}{tm("search_button")}</button></div></div>"""
    return page("/404.html", t("nf_title"), t("nf_text"), body, index=False)


def offline():
    body = f"""<div class="wrap page-head" style="text-align:center;padding:110px 0 60px">
<div class="eyebrow">{tm("off_eyebrow")}</div><h1 style="margin:0 auto">{tm("off_title")}</h1><p style="margin:16px auto 28px">{tm("off_text")}</p>
<div class="actions" style="justify-content:center"><button class="btn primary" type="button" data-reload>{tm("off_retry")}</button><a class="btn" href="/">{tm("nav_home")}</a></div></div>"""
    return page("/offline.html", t("off_title"), t("off_text"), body, index=False)


# ---------- service files ----------

def manifest():
    return json.dumps({
        "name": SITE["name"], "short_name": SITE["name"], "lang": DEFAULT,
        "description": pick(t("home_desc"), DEFAULT),
        "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#0C0D16", "theme_color": "#0C0D16",
        "icons": [
            {"src": "/assets/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/assets/icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }, ensure_ascii=False, indent=2)


def service_worker(version, files):
    sw = open(os.path.join(SRC, "sw.js"), encoding="utf-8").read()
    return sw.replace("__VERSION__", version).replace("__PRECACHE__", json.dumps(files, indent=0))


# ---------- checks ----------

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for key in ("href", "src", "srcset"):
            if a.get(key):
                self.links.append(a[key].split(" ")[0])


def check(out_dir):
    problems, external, ids = [], set(), {}
    pages = {}
    for dirpath, _, files in os.walk(out_dir):
        for f in files:
            if f.endswith(".html"):
                path = os.path.join(dirpath, f)
                p = Links()
                p.feed(open(path, encoding="utf-8").read())
                rel = "/" + os.path.relpath(path, out_dir).replace(os.sep, "/")
                pages[rel] = p
                ids[rel] = p.ids
    for rel, p in pages.items():
        for link in p.links:
            if link.startswith(("mailto:", "tel:", "data:", "#")):
                if link.startswith("#") and link[1:] and link[1:] not in p.ids and not re.match(r"#(ru|en)-\d+$", link):
                    problems.append(f"{rel}: missing anchor {link}")
                continue
            if link.startswith(("http://", "https://")):
                external.add(link)
                continue
            target, _, anchor = link.split("?")[0].partition("#")
            if not target.startswith("/"):
                problems.append(f"{rel}: relative link {link}")
                continue
            fs = os.path.join(out_dir, target.lstrip("/"))
            page_key = target if target.endswith(".html") else target.rstrip("/") + "/index.html" if not os.path.isfile(fs) else target
            if not (os.path.isfile(fs) or os.path.isfile(os.path.join(fs, "index.html"))):
                problems.append(f"{rel}: broken link {link}")
            elif anchor and page_key in ids and anchor not in ids[page_key]:
                problems.append(f"{rel}: missing anchor {link}")
    return problems, sorted(external)


# ---------- build ----------

def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(OUT, "assets"), ignore=shutil.ignore_patterns("*.md", "boot.js"))
    files = {
        "index.html": home(),
        "products/index.html": products_page(),
        "updates/index.html": updates_page(),
        "roadmap/index.html": roadmap_page(),
        "status/index.html": status_page(),
        "community/index.html": community_page(),
        "about/index.html": about_page(),
        "support/index.html": support_page(),
        "privacy/index.html": site_doc("privacy"),
        "terms/index.html": site_doc("terms"),
    }
    for p in PRODUCTS["products"]:
        files.update(product_page(p))
    files["404.html"] = not_found()
    files["offline.html"] = offline()
    files["search-index.json"] = json.dumps(SEARCH, ensure_ascii=False, separators=(",", ":"))
    files["manifest.webmanifest"] = manifest()
    files["robots.txt"] = f"User-agent: *\nAllow: /\n\nSitemap: {SITE['domain']}/sitemap.xml\n"
    today = max([u["date"] for u in UPDATES] + [STATUS["updated"]])
    files["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                            "".join(f"  <url><loc>{SITE['domain']}{u}</loc><lastmod>{today}</lastmod></url>\n" for u in PAGES) + "</urlset>\n")
    files["CNAME"] = SITE["domain"].split("://")[1] + "\n"
    for rel, text in files.items():
        path = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(text)
    # Offline cache: every page, asset and the search index. The version changes whenever any file changes.
    cached = sorted(set(PAGES + ["/offline.html", "/404.html", "/search-index.json", "/manifest.webmanifest"] +
                        ["/" + os.path.relpath(os.path.join(d, f), OUT).replace(os.sep, "/")
                         for d, _, fs in os.walk(os.path.join(OUT, "assets")) for f in fs if not f.endswith("og.png")]))
    digest = hashlib.sha256()
    for d, _, fs in sorted(os.walk(OUT)):
        for f in sorted(fs):
            digest.update(open(os.path.join(d, f), "rb").read())
    open(os.path.join(OUT, "sw.js"), "w", encoding="utf-8").write(service_worker(digest.hexdigest()[:12], cached))
    print(f"built {len(files) + 1} files into {os.path.relpath(OUT, ROOT)}: {len(PAGES)} pages, {len(SEARCH)} search entries")

    problems, external = check(OUT)
    for p in problems:
        print("LINK:", p)
    print(f"internal links: {'ok' if not problems else str(len(problems)) + ' problems'}; external links: {len(external)}")
    if "--list-external" in ARGS:
        print("\n".join(external))
    if "--check" in ARGS and problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
