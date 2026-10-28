#!/usr/bin/env python3
"""Static site generator for RemoteJob VN. Stdlib only (Pillow optional, for the OG image).

Reads data/*.json and site.config.json, writes pre-rendered HTML to dist/.
Every page is complete HTML; site/assets/app.js only adds client-side filtering.

Usage: python3 scripts/build.py [--out dist] [--today YYYY-MM-DD]
"""
import argparse, datetime, hashlib, html, json, os, re, shutil, sys, unicodedata
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import adsense  # noqa: E402
import jobfilter as jf  # noqa: E402
import legal_pages  # noqa: E402
import llms  # noqa: E402
import support_page  # noqa: E402
from site_text import T, MODE_LABELS, TZ_LABELS, ROLE_PAGES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))
SITE = CFG["SITE_URL"].rstrip("/")
NAME = CFG["SITE_NAME"]
LANGS = ("vi", "en")
REGION_ORDER = {"vn": 0, "apac": 1, "global": 2, "other": 3}
REMOTE_ORDER = {"yes": 0, "hybrid": 1, "unknown": 2, "no": 3}
e = html.escape


# ---------------------------------------------------------------- helpers
def slugify(text, limit=70):
    t = (text or "").replace("đ", "d").replace("Đ", "D")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if len(t) > limit:
        t = t[:limit].rsplit("-", 1)[0]
    return t or "job"


def assign_job_paths(jobs):
    """Public path for each job key. Collision suffixes match the page builder."""
    used = set()
    out = {}
    for job in sorted(jobs, key=lambda item: item["key"]):
        base = slugify(job["company_slug"] + "-" + job["title"], 80)
        slug = base if base not in used else base + "-" + hashlib.sha1(job["key"].encode()).hexdigest()[:6]
        used.add(slug)
        out[job["key"]] = f"/viec-lam/{slug}/"
    return out


# English legal pages use translated slugs (/en/privacy/), not the Vietnamese path.
LEGAL_PATHS = {
    "privacy": {"vi": "/chinh-sach-bao-mat/", "en": "/privacy/"},
    "terms": {"vi": "/dieu-khoan/", "en": "/terms/"},
    "contact": {"vi": "/lien-he/", "en": "/contact/"},
}
FRESH = {}


def legal_href(lang, key):
    return url_for(lang, LEGAL_PATHS[key][lang])


def load(rel, default=None):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def mode_tags(text):
    s = (text or "").lower()
    tags = []
    if "trực tiếp" in s or "direct" in s:
        tags.append("direct")
    if "eor" in s:
        tags.append("eor")
    if "contractor" in s or "hợp đồng" in s:
        tags.append("contractor")
    if "freelance" in s:
        tags.append("freelance")
    if "agency" in s or "nền tảng" in s or "staffing" in s:
        tags.append("agency")
    if not tags or s.strip() == "chưa xác minh":
        tags.append("unverified")
    return tags


def tz_tags(text):
    s = (text or "").lower()
    tags = []
    if re.search(r"giờ vn|utc\+7|gmt\+7|vn/sg|giờ việt", s):
        tags.append("vn")
    if re.search(r"apac|apj|châu á|asia|ấn độ|nhật|úc", s):
        tags.append("apac")
    if re.search(r"\beu\b|châu âu|anh\b", s):
        tags.append("eu")
    if re.search(r"mỹ|\bus\b|est\b|pacific|châu mỹ", s):
        tags.append("us")
    if re.search(r"async|toàn cầu|tự chọn|tùy khách", s):
        tags.append("async")
    return tags or ["unknown"]


def url_for(lang, path):
    """path is a site path like '/cong-ty/x/'; returns the language-specific path."""
    return path if lang == "vi" else "/en" + path


def absu(lang, path):
    return SITE + url_for(lang, path)


def fmt_date(d, lang):
    if not d:
        return "—"
    y, m, dd = d[:10].split("-")
    return f"{dd}/{m}/{y}" if lang == "vi" else d[:10]


# ---------------------------------------------------------------- layout
def _minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>])\s*", r"\1", css)
    return css.replace(";}", "}").strip()


CSS = _minify_css(open(os.path.join(ROOT, "site", "assets", "style.css"), encoding="utf-8").read())
CSS_HASH = hashlib.sha1(CSS.encode()).hexdigest()[:10]
JS = open(os.path.join(ROOT, "site", "assets", "app.js"), encoding="utf-8").read()
JS_HASH = hashlib.sha1(JS.encode()).hexdigest()[:10]
# Runs before first paint so the saved theme never flashes. Its SHA-256 is allowed in the CSP (site/_headers).
# Theme plus the dismissed support note, both before first paint so neither flashes or shifts layout.
THEME_BOOT = "try{var t=localStorage.getItem('theme');if(t==='dark'||t==='light')document.documentElement.dataset.theme=t;if(localStorage.getItem('rjvn-support-hide')==='1')document.documentElement.dataset.support='off'}catch(e){}"
THEME_BOOT_SHA = "sha256-" + __import__("base64").b64encode(hashlib.sha256(THEME_BOOT.encode()).digest()).decode()

LOGO = ('<svg viewBox="0 0 64 64" aria-hidden="true" focusable="false"><rect width="64" height="64" rx="14" fill="#0f766e"/>'
        '<path d="M14 40c6-12 12-18 18-18s12 6 18 18" fill="none" stroke="#5eead4" stroke-width="5" stroke-linecap="round"/>'
        '<circle cx="32" cy="22" r="6" fill="#fff"/><path d="M18 46h28" stroke="#fff" stroke-width="5" stroke-linecap="round"/></svg>')
ICON_SUN = '<svg class="theme-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
ICON_MOON = '<svg class="theme-dark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
AVATAR_COLORS = ["#0f766e", "#4338ca", "#b91c1c", "#a16207", "#7e22ce", "#0369a1", "#15803d", "#be185d", "#c2410c", "#334155"]


def initials(name):
    words = re.findall(r"[A-Za-z0-9À-ỹ]+", re.sub(r"\(.*?\)", "", name or ""))
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def avatar(c, size=""):
    col = AVATAR_COLORS[int(hashlib.md5(c["slug"].encode()).hexdigest(), 16) % len(AVATAR_COLORS)]
    return f'<span class="avatar {size}" style="background:{col}" aria-hidden="true">{e(initials(c["name"]))}</span>'


def head_tags(lang, path, title, desc, noindex=False, jsonld=None, og_type="website", alt=True, alternates=None):
    out = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{e(title)}</title>",
        f'<meta name="description" content="{e(desc)}">',
        f"<script>{THEME_BOOT}</script>",
        f'<link rel="stylesheet" href="/assets/style.{CSS_HASH}.css">',
    ]
    if alt:
        out.append(f'<link rel="canonical" href="{e(absu(lang, path))}">')
    if noindex:
        out.append('<meta name="robots" content="noindex,follow">')
    if alt:
        alts = alternates or {"vi": path, "en": path}
        out += [f'<link rel="alternate" hreflang="vi" href="{e(absu("vi", alts["vi"]))}">',
                f'<link rel="alternate" hreflang="en" href="{e(absu("en", alts["en"]))}">',
                f'<link rel="alternate" hreflang="x-default" href="{e(absu("vi", alts["vi"]))}">']
    client = adsense.client_id(CFG)
    if client:
        # Publisher id, Auto ads loader. Manual units are pushed from the end of body.
        out += [adsense.meta_tag(client), adsense.loader_tag(client)]
    out += [
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="{e(NAME)}">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{e(absu(lang, path))}">',
        f'<meta property="og:image" content="{SITE}/og-default.png">',
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{e(NAME)}">',
        f'<meta property="og:locale" content="{"vi_VN" if lang == "vi" else "en_US"}">',
        f'<meta property="og:locale:alternate" content="{"en_US" if lang == "vi" else "vi_VN"}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(title)}">',
        f'<meta name="twitter:description" content="{e(desc)}">',
        f'<meta name="twitter:image" content="{SITE}/og-default.png">',
        '<meta name="theme-color" content="#0f766e" media="(prefers-color-scheme: light)">',
        '<meta name="theme-color" content="#0b1120" media="(prefers-color-scheme: dark)">',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
        '<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
        '<link rel="manifest" href="/site.webmanifest">',
    ]
    for block in jsonld or []:
        out.append('<script type="application/ld+json">' + json.dumps(block, ensure_ascii=False).replace("</", "<\\/") + "</script>")
    return "\n".join(out)


def page(lang, path, title, desc, body, *, crumbs=None, noindex=False, jsonld=None, js=True, aside=None, og_type="website", alt=True, alternates=None):
    t = T[lang]
    nav = [("/cong-ty/", t["nav_companies"]), ("/viec-lam/", t["nav_jobs"]),
           ("/viec-lam-remote/", t["nav_roles"]), ("/cong-cu/", t["nav_tools"]),
           ("/dang-tin/", t["nav_post"]), ("/gioi-thieu/", t["nav_about"]),
           (support_page.PATHS[lang], t["nav_support"])]
    other = "en" if lang == "vi" else "vi"
    nav_parts = []
    for p, lbl in nav:
        attrs = f' href="{url_for(lang, p)}"'
        if p == support_page.PATHS[lang]:
            attrs = ' class="nav-support"' + attrs
        if path == p or (p != "/" and path.startswith(p)):
            attrs += ' aria-current="page"'
        nav_parts.append(f"<a{attrs}>{e(lbl)}</a>")
    navhtml = "".join(nav_parts)
    ld = list(jsonld or [])
    crumbhtml = ""
    if crumbs:
        items = [(t["home_crumb"], "/")] + crumbs
        crumbhtml = '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + "".join(
            f'<li><a href="{url_for(lang, p)}">{e(n)}</a></li>' if i < len(items) - 1 else f'<li aria-current="page">{e(n)}</li>'
            for i, (n, p) in enumerate(items)) + "</ol></nav>"
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": absu(lang, p)} for i, (n, p) in enumerate(items)]})
    main = f'<div class="layout{" with-aside" if aside else ""}"><main id="main">{crumbhtml}{body}</main>'
    if aside:
        # Ad stays in .side (hidden under 1100px, which also skips an AdSense request).
        # The support card is a sibling so small screens can show it without the ad.
        main += (f'<div class="rail"><aside class="side" aria-label="{e(t["ad"])}">{aside}</aside>'
                 f'{support_page.sidebar_card(lang)}</div>')
    main += "</div>"
    script = (ix_script(lang) + f'\n<script src="/assets/app.{JS_HASH}.js" defer></script>') if js else ""
    # Manual AdSense units are pushed only when a slot id exists. The apply-click
    # dialog is a house creative and must not be queued as an ad unit.
    if any(adsense.slot_id(CFG, name) for name in adsense.SIZES):
        script = adsense.push_tag() + ("\n" + script if script else "")
    L = lambda p: url_for(lang, p)
    repo = e(CFG["REPO_URL"])
    privacy_blurb = t["footer_privacy_ads"] if adsense.client_id(CFG) else t["footer_privacy"]
    other_path = (alternates or {}).get(other, path)
    footer = f"""<footer class="foot"><div class="wrap"><div class="cols">
<div><a class="brand" href="{L('/')}">{LOGO}<span>RemoteJob <b>VN</b></span></a><p class="muted" style="margin-top:12px;max-width:42ch">{e(t['site_tag'])}. {e(privacy_blurb)}</p></div>
<nav aria-label="{e(t['ft_explore'])}"><h2>{e(t['ft_explore'])}</h2><ul><li><a href="{L('/cong-ty/')}">{e(t['nav_companies'])}</a></li><li><a href="{L('/viec-lam/')}">{e(t['nav_jobs'])}</a></li><li><a href="{L('/viec-lam-remote/')}">{e(t['nav_roles'])}</a></li><li><a href="{L('/cong-cu/')}">{e(t['nav_tools'])}</a></li></ul></nav>
<nav aria-label="{e(t['ft_project'])}"><h2>{e(t['ft_project'])}</h2><ul><li><a href="{url_for(lang, support_page.PATHS[lang])}">{e(t['ft_support'])}</a></li><li><a href="{L('/gioi-thieu/')}">{e(t['nav_about'])}</a></li><li><a href="{L('/dang-tin/')}">{e(t['nav_post'])}</a></li><li><a href="{repo}/blob/main/CONTRIBUTING.md" rel="noopener">{e(t['ft_contribute'])}</a></li><li><a href="{repo}" rel="noopener">GitHub</a></li><li><a href="/sitemap.xml">Sitemap</a></li></ul></nav>
<nav aria-label="{e(t['ft_legal'])}"><h2>{e(t['ft_legal'])}</h2><ul><li><a href="{legal_href(lang, 'privacy')}">{e(t['ft_privacy'])}</a></li><li><a href="{legal_href(lang, 'terms')}">{e(t['ft_terms'])}</a></li><li><a href="{legal_href(lang, 'contact')}">{e(t['ft_contact'])}</a></li><li><a href="{L('/cong-cu/')}#disclosure">{e(t['ft_disclosure'])}</a></li><li><a href="{L('/quang-cao/')}">{e(t['ads_title'])}</a></li><li><a href="{L('/gioi-thieu/')}#license">{e(t['ft_license'])}</a></li></ul></nav>
</div><p class="fine">{e(t['footer'])}</p><p class="fine status">{e(FRESH.get(lang, ''))}</p></div></footer>"""
    return f"""<!doctype html>
<html lang="{lang}">
<head>
{head_tags(lang, path, title, desc, noindex, ld, og_type, alt, alternates)}
</head>
<body data-lang="{lang}">
<a class="skip" href="#main">{e(t['skip'])}</a>
<header class="top"><div class="wrap">
<a class="brand" href="{L('/')}" aria-label="RemoteJob VN – {e(t['nav_home'])}">{LOGO}<span>RemoteJob <b>VN</b></span></a>
<nav class="nav" aria-label="{e(t['nav_main'])}">{navhtml}</nav>
<div class="tools"><button class="iconbtn" type="button" id="theme-toggle" hidden aria-label="{e(t['theme'])}" title="{e(t['theme'])}">{ICON_SUN}{ICON_MOON}</button>
<a class="iconbtn" href="{url_for(other, other_path) if alt else url_for(other, '/')}" hreflang="{other}" lang="{other}" title="{e(t['switch_label'])}">{t['switch']}</a></div>
</div></header>
<div class="wrap">{main}</div>
{footer}
{script}
</body>
</html>
"""


# ---------------------------------------------------------------- components
def ad_unit(lang, placement, tag=None):
    """AdSense markup for a configured slot id. None keeps the house creative."""
    client = adsense.client_id(CFG)
    slot = adsense.slot_id(CFG, placement)
    if not (client and slot):
        return None
    width, height = adsense.SIZES[placement]
    cls = {"sidebar": "slot slot-side adsense", "native": "slot slot-native adsense", "bottom": "slot slot-bottom adsense"}[placement]
    inner = f'<span class="label">{e(T[lang]["ad"])}</span>{adsense.ins_html(client, slot, width, height)}'
    if tag:
        return f'<{tag} class="{cls}" data-ad="1">{inner}</{tag}>'
    return f'<div class="{cls}">{inner}</div>'


def sidebar_house_text(lang, slot):
    """House line for one language. Vietnamese must not repeat the English sentence."""
    text = str((slot or {}).get(lang) or "").strip()
    en = str((slot or {}).get("en") or "").strip()
    if lang == "vi" and (not text or text == en or text.lower().startswith("advertise here")):
        return "Quảng cáo tại đây: tiếp cận kỹ sư remote ở Việt Nam."
    return text


def ad_sidebar(lang, ads):
    if not ads.get("enabled"):
        return None
    unit = ad_unit(lang, "sidebar")
    if unit:
        return unit
    t = T[lang]
    s = ads["sidebar"]
    return (f'<div class="slot slot-side"><span><span class="label">{e(t["ad"])}</span></span>'
            f'<div class="ph">300 × 250</div><a href="{url_for(lang, s["url"])}">{e(sidebar_house_text(lang, s))}</a></div>')


def ad_native(lang, ads, tag="li"):
    unit = ad_unit(lang, "native", tag=tag)
    if unit:
        return unit
    t = T[lang]
    n = ads["native"]
    return (f'<{tag} class="slot slot-native" data-ad="1"><span class="label">{e(t["ad"])}</span>'
            f'<a href="{url_for(lang, n["url"])}">{e(n[lang])}</a></{tag}>')


def ad_bottom(lang, ads):
    if not ads.get("enabled"):
        return ""
    unit = ad_unit(lang, "bottom")
    if unit:
        return unit
    return ('<div class="slot slot-bottom"><span class="label">' + e(T[lang]["ad"]) + "</span><a href=\""
            + url_for(lang, ads["native"]["url"]) + "\">" + e(ads["native"][lang]) + "</a></div>")


def with_native(rows, lang, ads, tag="li"):
    if not ads.get("enabled"):
        return "".join(rows)
    k = max(10, min(15, int(ads.get("native_every", 12))))
    out = []
    for i, r in enumerate(rows, 1):
        out.append(r)
        if i % k == 0 and i < len(rows):
            out.append(ad_native(lang, ads, tag))
    return "".join(out)


def badge(text, cls=""):
    return f'<span class="b {cls}">{e(text)}</span>'


def job_badges(j, lang):
    t = T[lang]
    out = badge(t["region_" + j["region"]], "r-" + j["region"])
    out += badge(t["remote_" + j["remote"]], "m-" + j["remote"])
    if j.get("salary"):
        out += badge("💰 " + j["salary"], "sal")
    return out


def job_row(j, co, lang):
    t = T[lang]
    loc = f'<span class="loc">{e(j["location"])}</span>' if j.get("location") else ""
    return (f'<li class="card job-card"><a class="t" href="{url_for(lang, j["path"])}">{e(j["title"])}</a>'
            f'<div class="meta"><a class="co" href="{url_for(lang, "/cong-ty/" + co["slug"] + "/")}">{e(co["name"])}</a>{loc}</div>'
            f'<div class="tags">{job_badges(j, lang)}<span class="b date">✓ {e(t["checked_short"])} {fmt_date(j["last_checked"], lang)}</span></div></li>')


def company_card(c, lang, njobs):
    t = T[lang]
    roles = " ".join(c["hires_roles"])
    modes = " ".join(c["_modes"])
    tzs = " ".join(c["_tz"])
    text = " ".join([c["name"], c["hq"], c["remote_policy"], c["vn_hiring_mode"], c["timezone_note"], roles]).lower()
    v = badge("✓ " + t["verified"], "ok") if c["verified"] else badge(t["unverified"], "warn")
    if company_is_aggregator(c):
        v = badge(t["kind_aggregator"], "warn") + v
    jobs = f'<span class="nj">{njobs} {e(t["jobs_word"])}</span>' if njobs else ""
    mode = "".join(badge(MODE_LABELS[m][0 if lang == "vi" else 1], "mode") for m in c["_modes"][:2])
    return (f'<li class="card co-card co" data-roles="{e(roles)}" data-mode="{e(modes)}" data-group="{c["group"]}" data-tz="{e(tzs)}" data-text="{e(text)}">'
            f'{avatar(c)}<div style="min-width:0"><div class="co-top">'
            f'<a class="t" href="{url_for(lang, "/cong-ty/" + c["slug"] + "/")}">{e(c["name"])}</a>{jobs}</div>'
            f'<div class="meta"><span>{e(c["hq"])}</span><span>{e(c["timezone_note"])}</span></div>'
            f'<p class="desc">{e(c["remote_policy"])}</p>'
            f'<div class="tags">{v}{mode}{"".join(badge(r, "role") for r in c["hires_roles"][:4])}</div></div></li>')


def pager(lang, base, n, total):
    t = T[lang]
    if total <= 1:
        return ""
    href = lambda k: url_for(lang, base if k == 1 else f"{base}trang/{k}/")
    parts = []
    if n > 1:
        parts.append(f'<a rel="prev" href="{href(n - 1)}" aria-label="{e(t["prev"])}">←</a>')
    lo, hi = max(1, n - 2), min(total, n + 2)
    last = 0
    for k in sorted(set([1, total] + list(range(lo, hi + 1)))):
        if k - last > 1:
            parts.append('<span class="gap" aria-hidden="true">…</span>')
        parts.append(f'<span aria-current="page">{k}</span>' if k == n else f'<a href="{href(k)}" aria-label="{e(t["page"])} {k}">{k}</a>')
        last = k
    if n < total:
        parts.append(f'<a rel="next" href="{href(n + 1)}" aria-label="{e(t["next"])}">→</a>')
    return f'<nav class="pager" aria-label="{e(t["page"])}">{"".join(parts)}</nav>'


def select(name, label, options, lang):
    t = T[lang]
    opts = f'<option value="">{e(t["all"])}</option>' + "".join(f'<option value="{e(v)}">{e(lbl)}</option>' for v, lbl in options)
    return f'<label>{e(label)}<select name="{name}">{opts}</select></label>'


def empty_state(lang, extra=""):
    t = T[lang]
    return f'<div class="empty"><b>{e(t["empty_title"])}</b>{e(t["empty_body"])}{extra}</div>'


ADS = {}


def company_is_aggregator(company):
    """Job boards are flagged kind=aggregator. Omitted kind means a direct employer."""
    return (company or {}).get("kind") == "aggregator"


def jobs_for_default_listings(jobs, co_by):
    """Mixed lists (home, /viec-lam/, role pages) show direct employers only."""
    return [j for j in jobs if not company_is_aggregator(co_by.get(j.get("company_slug")))]


def ix_script(lang):
    """JSON config for the click interstitial. Empty when site.config.json disables it.

    The dialog itself is created by app.js on click, so this tag is not visible content
    and does not participate in layout.
    """
    if not CFG.get("outbound_interstitial"):
        return ""
    t = T[lang]
    ix = (ADS or {}).get("interstitial") or {}
    copy = ix.get(lang) or {}
    try:
        seconds = int(ix.get("seconds", 5))
    except (TypeError, ValueError):
        seconds = 5
    seconds = max(3, min(15, seconds))
    href = ix.get("href") or "/quang-cao/"
    if isinstance(href, str) and href.startswith("/") and not href.startswith("//"):
        href = url_for(lang, href)
    elif not (isinstance(href, str) and href.startswith("https://")):
        href = url_for(lang, "/quang-cao/")
    payload = {
        "label": ix.get("label") or "Quảng cáo / Advertisement",
        "seconds": seconds,
        "href": href,
        "title": copy.get("title") or t["ix_title"],
        "body": copy.get("body") or t["ix_body"],
        "cta": copy.get("cta") or t["ix_cta"],
        "go": copy.get("continue") or t["ix_go"],
        "close": copy.get("close") or t["ix_close"],
        "count": copy.get("countdown") or t["ix_count"],
        "support": t["ix_support"],
        "supportHref": url_for(lang, support_page.PATHS[lang]),
    }
    raw = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return f'<script type="application/json" id="rj-ix">{raw}</script>'


# ---------------------------------------------------------------- build
def main():
    global ADS
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    ap.add_argument("--today", default=os.environ.get("BUILD_DATE") or datetime.date.today().isoformat())
    a = ap.parse_args()
    OUT, TODAY = a.out, a.today
    today_d = datetime.date.fromisoformat(TODAY)

    companies = load("data/companies.json")
    jobs_all = load("data/jobs.json", [])
    sources = {s["slug"]: s for s in load("data/sources.json", [])}
    ads = load("data/ads.json", {"enabled": False})
    ADS = ads
    affiliates = load("data/affiliates.json", {"categories": []})
    sponsored = load("data/sponsored.json", {"max_featured": 0, "items": []})
    co_by = {c["slug"]: c for c in companies}
    for c in companies:
        c["_modes"] = mode_tags(c["vn_hiring_mode"])
        c["_tz"] = tz_tags(c["timezone_note"])

    # --- classify jobs: active (listed + sitemap), gone (noindex page, not listed), dropped (no page)
    stale_cut = (today_d - datetime.timedelta(days=CFG["JOB_STALE_DAYS"])).isoformat()
    keep_cut = (today_d - datetime.timedelta(days=CFG["REMOVED_PAGE_KEEP_DAYS"])).isoformat()
    active, gone = [], []
    used = set()
    for j in sorted(jobs_all, key=lambda x: x["key"]):
        if j["company_slug"] not in co_by:
            continue
        base = slugify(j["company_slug"] + "-" + j["title"], 80)
        s = base if base not in used else base + "-" + hashlib.sha1(j["key"].encode()).hexdigest()[:6]
        used.add(s)
        j["slug"] = s
        j["path"] = f"/viec-lam/{s}/"
        is_open = j.get("status", "open") == "open" and j.get("last_checked", "") >= stale_cut
        if is_open:
            active.append(j)
        elif (j.get("removed_on") or j.get("last_checked", "")) >= keep_cut:
            gone.append(j)
    sort_key = lambda j: (REGION_ORDER[j["region"]], REMOTE_ORDER[j["remote"]], co_by[j["company_slug"]]["name"].lower(), j["title"].lower())
    active.sort(key=sort_key)
    jobs_by_co = defaultdict(list)
    for j in active:
        jobs_by_co[j["company_slug"]].append(j)
    jobs_updated = max([j["last_checked"] for j in active] or [TODAY])
    # Aggregators (job boards) keep their own pages but do not fill mixed lists.
    agg_slugs = {c["slug"] for c in companies if company_is_aggregator(c)}
    listed = jobs_for_default_listings(active, co_by)
    global FRESH
    api_count = sum(1 for s in sources.values() if s.get("method") == "api" or s.get("ats") in jf.API_ATS)
    checked_dates = [s.get("last_checked") or "" for s in sources.values()] + [j.get("last_checked") or "" for j in active]
    last_data = max([d for d in checked_dates if d] or [TODAY])
    status_doc = load("data/status.json", {}) or {}
    FRESH = {
        lang: T[lang]["status_line"].format(
            date=fmt_date(last_data, lang), api=api_count, sources=len(sources), jobs=len(listed))
        for lang in LANGS
    }

    # --- role pages (direct employers only)
    roles = []
    for slug, vi, en, tagset, rx, co_roles in ROLE_PAGES:
        crx = re.compile(rx, re.I)
        js = [j for j in listed if (set(j["roles"]) & tagset) or crx.search(j["title"])]
        cos = [c for c in companies if not company_is_aggregator(c) and set(c["hires_roles"]) & co_roles]
        roles.append(dict(slug=slug, vi=vi, en=en, jobs=js, keys={j["key"] for j in js}, companies=cos, co_roles=co_roles))
    role_by_hr = defaultdict(list)
    for r in roles:
        for hr in r["co_roles"]:
            role_by_hr[hr].append(r)

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    sitemap = {"vi": [], "en": []}

    def write(lang, path, content, lastmod=None, index=True, alternates=None):
        fp = os.path.join(OUT, url_for(lang, path).lstrip("/"), "index.html") if path.endswith("/") else os.path.join(OUT, url_for(lang, path).lstrip("/"))
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8") as fh:
            fh.write(content)
        if index:
            sitemap[lang].append((path, lastmod or TODAY, alternates))

    # --- sponsored
    feat = [s for s in sponsored.get("items", []) if s["starts"] <= TODAY <= s["expires"]][: int(sponsored.get("max_featured", 0))]

    def featured_block(lang):
        if not feat:
            return ""
        t = T[lang]
        rows = "".join(
            f'<li class="card featured"><span class="label sp">{e(t["sponsored"])}</span> '
            f'<a class="t" href="{e(s["url"])}" rel="sponsored nofollow noopener">{e(s["title"])}</a>'
            f'<div class="meta"><span>{e(s["company_name"])}</span>{"<span>" + e(s["location"]) + "</span>" if s.get("location") else ""}</div>'
            f'{"<p class=small style=margin-top:8px>" + e(s["blurb"]) + "</p>" if s.get("blurb") else ""}'
            f'{"<div class=tags>" + badge("💰 " + s["salary"], "sal") + "</div>" if s.get("salary") else ""}</li>' for s in feat)
        return f'<section class="feat" aria-label="{e(t["featured"])}"><h2>{e(t["featured"])}</h2><ul class="list">{rows}</ul></section>'

    n_vn = sum(1 for j in listed if j["region"] in ("vn", "apac"))
    role_opts_jobs = sorted({r for j in active for r in j["roles"]})
    co_role_counts = Counter(r for c in companies for r in c["hires_roles"])

    for lang in LANGS:
        t = T[lang]
        side = ad_sidebar(lang, ads)
        # ---------------- home
        top = [j for j in listed if j["region"] in ("vn", "apac") and j["remote"] in ("yes", "hybrid")][:12]
        role_links = "".join(f'<li><a class="chip" href="{url_for(lang, "/viec-lam-remote/" + r["slug"] + "/")}">{e(r[lang])} <span class="n">{len(r["jobs"])}</span></a></li>' for r in roles)
        grpA = [c for c in companies if c["group"] == "A"][:10]
        lead_key = "home_lead_ads" if adsense.client_id(CFG) else "home_lead"
        desc_key = "home_desc_ads" if adsense.client_id(CFG) else "home_desc"
        body = f"""<section class="hero"><h1>{e(t['home_h1'])}</h1><p class="lead">{e(t[lead_key])}</p>
<form class="hero-search" action="{url_for(lang, '/viec-lam/')}" method="get" role="search"><label class="sr" for="hq">{e(t['search'])}</label>
<input id="hq" type="search" name="q" placeholder="{e(t['hero_search_ph'])}" autocomplete="off"><button class="btn primary" type="submit">{e(t['hero_btn'])}</button></form>
<ul class="chips" aria-label="{e(t['browse_roles'])}">{role_links}</ul>
<ul class="stats"><li><b>{len(companies)}</b> {e(t['stat_companies'])}</li><li><b>{len(listed)}</b> {e(t['stat_jobs'])}</li><li><b>{n_vn}</b> {e(t['stat_vn'])}</li><li><b>{fmt_date(jobs_updated, lang)}</b> {e(t['updated'])}</li></ul>
{f'<p class="muted small">{e(t["home_agg_note"])}</p>' if agg_slugs else ''}</section>
{support_page.nudge(lang)}
{featured_block(lang)}
<section><h2>{e(t['latest_vn'])}</h2><ul class="list grid2">{with_native([job_row(j, co_by[j['company_slug']], lang) for j in top], lang, ads)}</ul>
<p style="margin-top:16px"><a class="btn" href="{url_for(lang, '/viec-lam/')}">{e(t['see_all_jobs'])} →</a></p></section>
<section><h2>{e(t['group_A'])}</h2><ul class="list grid2">{''.join(company_card(c, lang, len(jobs_by_co[c['slug']])) for c in grpA)}</ul>
<p style="margin-top:16px"><a class="btn" href="{url_for(lang, '/cong-ty/')}">{e(t['see_all_companies'])} →</a></p></section>
<p class="note" style="margin-top:32px">{e(t['contrib_cta'])} <a href="{e(CFG['REPO_URL'])}/blob/main/CONTRIBUTING.md" rel="noopener">CONTRIBUTING.md</a></p>"""
        ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": NAME, "url": absu(lang, "/"), "inLanguage": lang}]
        write(lang, "/", page(lang, "/", t["home_title"], t[desc_key].format(n=len(companies), j=len(listed)), body, jsonld=ld, aside=side), jobs_updated)

        # ---------------- company directory
        mode_opts = [(k, MODE_LABELS[k][0 if lang == "vi" else 1]) for k in MODE_LABELS]
        tz_opts = [(k, TZ_LABELS[k][0 if lang == "vi" else 1]) for k in TZ_LABELS]
        role_opts = [(r, f"{r} ({n})") for r, n in sorted(co_role_counts.items(), key=lambda x: (-x[1], x[0]))]
        form = f"""<form class="filters" id="co-filters" hidden role="search">
<label class="q">{e(t['search'])}<input type="search" name="q" placeholder="{e(t['search_ph'])}"></label>
{select('role', t['f_role'], role_opts, lang)}{select('mode', t['f_mode'], mode_opts, lang)}
{select('group', t['f_group'], [('A', t['group_A']), ('B', t['group_B'])], lang)}{select('tz', t['f_tz'], tz_opts, lang)}
<div class="row-end"><output name="count" aria-live="polite"></output><button type="reset">{e(t['reset'])}</button></div></form>"""
        cards = [company_card(c, lang, len(jobs_by_co[c["slug"]])) for c in sorted(companies, key=lambda c: (c["group"], company_is_aggregator(c), -len(jobs_by_co[c["slug"]]), c["name"].lower()))]
        body = f"""<div class="pagehead"><h1>{e(t['companies_h1'])}</h1><p class="lead">{e(t['companies_desc'].format(n=len(companies)))}</p></div>{form}
<ul class="list" id="co-list">{with_native(cards, lang, ads)}</ul><div id="co-empty" hidden>{empty_state(lang)}</div>"""
        ld = [{"@context": "https://schema.org", "@type": "ItemList", "numberOfItems": len(companies),
               "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": absu(lang, f"/cong-ty/{c['slug']}/")} for i, c in enumerate(companies)]}]
        write(lang, "/cong-ty/", page(lang, "/cong-ty/", t["companies_title"].format(n=len(companies)), t["companies_desc"].format(n=len(companies)), body,
                                      crumbs=[(t["nav_companies"], "/cong-ty/")], jsonld=ld, js=True, aside=side),
              max(c["last_checked"] for c in companies))

        # ---------------- company pages
        for c in companies:
            path = f"/cong-ty/{c['slug']}/"
            cj = jobs_by_co[c["slug"]]
            src = sources.get(c["slug"])
            if not src:
                srcnote = f'<p class="note">{e(t["no_auto"])}</p>'
            elif src.get("status") == "error":
                srcnote = f'<p class="note warn">{e(t["fetch_error"])}</p>'
            else:
                srcnote = f'<p class="muted">{e(t["jobs_fetched"])}: {fmt_date(src.get("last_checked"), lang)}</p>'
            if company_is_aggregator(c):
                srcnote = f'<p class="note">{e(t["agg_list_note"])}</p>' + srcnote
            role_links_c = " ".join(
                (f'<a class="b role" href="{url_for(lang, "/viec-lam-remote/" + role_by_hr[r][0]["slug"] + "/")}">{e(r)}</a>' if role_by_hr.get(r) else badge(r, "role"))
                for r in c["hires_roles"])
            site_link = f'<a href="{e(c["website"])}" rel="noopener">{e(c["website"])}</a>' if c["website"] else "—"
            facts = [(t["hq"], e(c["hq"])), (t["remote_policy"], e(c["remote_policy"])), (t["hiring_mode"], e(c["vn_hiring_mode"])),
                     (t["timezone"], e(c["timezone_note"])), (t["salary"], e(c["salary_public"])), (t["roles"], role_links_c),
                     (t["website"], site_link), (t["careers"], f'<a href="{e(c["careers_url"])}" rel="noopener">{e(c["careers_url"])}</a>'),
                     (t["sources"], "<br>".join(f'<a href="{e(u)}" rel="noopener nofollow">{e(u)}</a>' for u in c["source_urls"])),
                     (t["last_checked"], fmt_date(c["last_checked"], lang))]
            dl = "".join(f"<dt>{e(k)}</dt><dd>{v}</dd>" for k, v in facts)
            jl = f'<ul class="list">{"".join(job_row(j, c, lang) for j in cj)}</ul>' if cj else f'<div class="empty"><b>{e(t["no_jobs"])}</b><a href="{e(c["careers_url"])}" rel="noopener">{e(t["careers"])} ↗</a></div>'
            rel = sorted((x for x in companies if x["slug"] != c["slug"]),
                         key=lambda x: (company_is_aggregator(x), -len(set(x["hires_roles"]) & set(c["hires_roles"])) - (x["group"] == c["group"]), -len(jobs_by_co[x["slug"]]), x["name"].lower()))[:6]
            relhtml = "".join(company_card(x, lang, len(jobs_by_co[x["slug"]])) for x in rel)
            v = badge("✓ " + t["verified"], "ok") if c["verified"] else badge(t["unverified"], "warn")
            if company_is_aggregator(c):
                v = badge(t["kind_aggregator"], "warn") + v
            note_lang = '<p class="muted small">(Company facts are written in Vietnamese.)</p>' if lang == "en" else ""
            body = f"""<div class="detail-head">{avatar(c, 'lg')}<div><h1>{e(c['name'])}</h1><div class="tags">{badge(t['group_' + c['group']])}{v}{''.join(badge(MODE_LABELS[m][0 if lang == 'vi' else 1], 'mode') for m in c['_modes'])}</div></div></div>
<div class="cta"><a class="btn primary" href="{e(c['careers_url'])}" rel="noopener">{e(t['careers'])} ↗</a>{('<a class="btn" href="' + e(c['website']) + '" rel="noopener">' + e(t['website']) + ' ↗</a>') if c['website'] else ''}<a class="btn" href="#jobs">{e(t['open_jobs'])} ({len(cj)})</a></div>
<div class="panel"><dl class="facts">{dl}</dl>{note_lang}</div>
<section><h2 id="jobs">{e(t['open_jobs'])} ({len(cj)})</h2>{srcnote}{jl}</section>
<section><h2>{e(t['related'])}</h2><ul class="list grid2">{relhtml}</ul></section>
<p style="margin-top:24px" class="small"><a href="{e(CFG['REPO_URL'])}/edit/main/data/companies.json" rel="noopener">✎ {e(t['edit'])}</a></p>
{ad_bottom(lang, ads)}"""
            org = {"@context": "https://schema.org", "@type": "Organization", "name": c["name"], "url": c["website"] or c["careers_url"],
                   "sameAs": [u for u in [c["careers_url"]] if u and u != c["website"]]}
            if not org["sameAs"]:
                del org["sameAs"]
            title = (f"{c['name']}: việc làm remote, chính sách remote & tuyển ở Việt Nam" if lang == "vi"
                     else f"{c['name']}: remote jobs, remote policy & hiring in Vietnam")
            desc = (f"{c['name']} ({c['hq']}) – {c['remote_policy']}. Hình thức tuyển ở VN: {c['vn_hiring_mode']}. {len(cj)} việc làm remote đang mở." if lang == "vi"
                    else f"{c['name']} ({c['hq']}): remote policy, how they hire people in Vietnam, time zone, and {len(cj)} open remote jobs.")
            write(lang, path, page(lang, path, title, desc[:300], body, crumbs=[(t["nav_companies"], "/cong-ty/"), (c["name"], path)], jsonld=[org], og_type="profile", aside=side),
                  max([c["last_checked"]] + [j["last_checked"] for j in cj]))

        # ---------------- job listing (paginated)
        per = CFG["JOBS_PER_PAGE"]
        total = max(1, -(-len(listed) // per))
        co_opts = [(c["slug"], c["name"]) for c in sorted(companies, key=lambda c: c["name"].lower()) if jobs_by_co[c["slug"]]]
        jform = f"""<form class="filters" id="job-filters" hidden role="search">
<label class="q">{e(t['search'])}<input type="search" name="q" placeholder="{e(t['search_jobs_ph'])}"></label>
{select('role', t['f_role'], [(r, r) for r in role_opts_jobs], lang)}{select('company', t['f_company'], co_opts, lang)}
{select('region', t['f_region'], [(k, t['region_' + k]) for k in REGION_ORDER], lang)}
{select('remote', t['f_remote'], [(k, t['remote_' + k]) for k in REMOTE_ORDER], lang)}
<div class="row-end"><output name="count" aria-live="polite"></output><button type="reset">{e(t['reset'])}</button></div></form>"""
        for n in range(1, total + 1):
            path = "/viec-lam/" if n == 1 else f"/viec-lam/trang/{n}/"
            chunk = listed[(n - 1) * per: n * per]
            ptxt = "" if n == 1 else f" – {t['page']} {n}"
            agg_note = f'<p class="note">{e(t["jobs_agg_note"])}</p>' if agg_slugs and n == 1 else ""
            body = f"""<div class="pagehead"><h1>{e(t['jobs_h1'])}{e(ptxt)}</h1><p class="lead">{e(t['jobs_desc'].format(n=len(listed), d=fmt_date(jobs_updated, lang)))}</p>{agg_note}</div>
{support_page.nudge(lang)}
{featured_block(lang) if n == 1 else ''}{jform if n == 1 else ''}
<div id="job-empty" hidden>{empty_state(lang)}</div><ul class="list" id="job-list" data-index="/data/jobs-index.json">{with_native([job_row(j, co_by[j['company_slug']], lang) for j in chunk], lang, ads)}</ul>
<div id="job-more" class="loadmore"></div>{pager(lang, '/viec-lam/', n, total)}"""
            title = t["jobs_title"].format(page=ptxt) + (" | RemoteJob VN" if lang == "en" else " | việc làm remote Việt Nam")
            write(lang, path, page(lang, path, title, t["jobs_desc"].format(n=len(listed), d=fmt_date(jobs_updated, lang)), body,
                                   crumbs=[(t["nav_jobs"], "/viec-lam/")] + ([(f"{t['page']} {n}", path)] if n > 1 else []), js=(n == 1), aside=side), jobs_updated)

        # ---------------- job pages
        gone_keys = {j["key"] for j in gone}
        for j in active + gone:
            c = co_by[j["company_slug"]]
            path = j["path"]
            is_gone = j["key"] in gone_keys
            others = [x for x in jobs_by_co[c["slug"]] if x is not j][:8]
            jr = set(j["roles"]) - {"other", "engineering"}
            sim = [x for x in listed if x["company_slug"] != c["slug"] and set(x["roles"]) & jr and x["region"] == j["region"]][:6] if jr else []
            rlinks = [r for r in roles if j["key"] in r["keys"]] if not is_gone else []
            facts = [(t["f_company"], f'<a href="{url_for(lang, "/cong-ty/" + c["slug"] + "/")}">{e(c["name"])}</a>'),
                     (t["location"], e(j.get("location") or "—")), (t["f_region"], e(t["region_" + j["region"]])),
                     (t["f_remote"], e(t["remote_" + j["remote"]]))]
            if j.get("salary"):
                facts.append((t["salary"], e(j["salary"])))
            if j.get("date_posted"):
                facts.append((t["posted"], fmt_date(j["date_posted"], lang)))
            facts += [(t["first_seen"], fmt_date(j.get("first_seen"), lang)), (t["last_checked"], fmt_date(j["last_checked"], lang)),
                      (t["hiring_mode"], e(c["vn_hiring_mode"])), (t["timezone"], e(c["timezone_note"]))]
            if rlinks:
                facts.append((t["f_role"], " ".join(f'<a class="b role" href="{url_for(lang, "/viec-lam-remote/" + r["slug"] + "/")}">{e(r[lang])}</a>' for r in rlinks)))
            dl = "".join(f"<dt>{e(k)}</dt><dd>{v}</dd>" for k, v in facts)
            desc_html = (f'<section><h2>{e(t["description"])}</h2><p class="excerpt">{e(j["description"])}</p><p class="muted small">{e(t["excerpt_note"])}</p></section>' if j.get("description") else "")
            banner = f'<p class="note warn" role="status">{e(t["removed"])}</p>' if is_gone else ""
            if company_is_aggregator(c) and not is_gone:
                banner += f'<p class="note">{e(t["agg_job_note"])}</p>'
            apply = "" if is_gone else f'<div class="cta"><a class="btn primary" data-out="job" href="{e(j["url"])}" rel="noopener nofollow">{e(t["apply"])} ↗</a><a class="btn" href="{url_for(lang, "/cong-ty/" + c["slug"] + "/")}">{e(c["name"])}</a></div>'
            more = (f'<section><h2>{e(t["more_at"])} {e(c["name"])}</h2><ul class="list">{"".join(job_row(x, c, lang) for x in others)}</ul>'
                    f'<p><a href="{url_for(lang, "/cong-ty/" + c["slug"] + "/")}#jobs">{e(c["name"])} →</a></p></section>') if others else ""
            simh = f'<section><h2>{e(t["similar"])}</h2><ul class="list grid2">{"".join(job_row(x, co_by[x["company_slug"]], lang) for x in sim)}</ul></section>' if sim else ""
            body = f"""<div class="detail-head">{avatar(c, 'lg')}<div><h1>{e(j['title'])}</h1><p class="muted" style="margin:0 0 8px"><a href="{url_for(lang, '/cong-ty/' + c['slug'] + '/')}">{e(c['name'])}</a>{(' · ' + e(j['location'])) if j.get('location') else ''}</p>
<div class="tags">{job_badges(j, lang)}<span class="b date">✓ {e(t['checked_short'])} {fmt_date(j['last_checked'], lang)}</span></div></div></div>{banner}{apply}
<div class="panel"><dl class="facts">{dl}</dl></div>{desc_html}{more}{simh}"""
            ld = []
            jp = job_posting_ld(j, c)
            if jp and not is_gone:
                ld.append(jp)
            loc_txt = f" ({j['location']})" if j.get("location") else ""
            title = (f"{j['title']} – {c['name']} | Việc làm remote" if lang == "vi" else f"{j['title']} – {c['name']} | Remote job")
            desc = (f"{j['title']} tại {c['name']}{loc_txt}. {t['remote_' + j['remote']]}, khu vực {t['region_' + j['region']]}. Kiểm tra lần cuối {fmt_date(j['last_checked'], lang)}."
                    if lang == "vi" else f"{j['title']} at {c['name']}{loc_txt}. {t['remote_' + j['remote']]}, region: {t['region_' + j['region']]}. Last checked {j['last_checked']}.")
            write(lang, path, page(lang, path, title, desc[:300], body, crumbs=[(t["nav_jobs"], "/viec-lam/"), (c["name"], f"/cong-ty/{c['slug']}/"), (j["title"], path)],
                                   noindex=is_gone, jsonld=ld, og_type="article", aside=side), j["last_checked"], index=not is_gone)

        # ---------------- role pages
        chips = "".join(f'<li><a class="chip" href="{url_for(lang, "/viec-lam-remote/" + r["slug"] + "/")}">{e(r[lang])} <span class="n">{len(r["jobs"])}</span></a></li>' for r in roles)
        write(lang, "/viec-lam-remote/", page(lang, "/viec-lam-remote/", t["roles_title"], t["roles_desc"],
                                              f'<div class="pagehead"><h1>{e(t["roles_title"])}</h1><p class="lead">{e(t["roles_desc"])}</p></div><ul class="chips">{chips}</ul>',
                                              crumbs=[(t["nav_roles"], "/viec-lam-remote/")], aside=side), jobs_updated)
        for r in roles:
            base = f"/viec-lam-remote/{r['slug']}/"
            rtotal = max(1, -(-len(r["jobs"]) // per))
            for n in range(1, rtotal + 1):
                path = base if n == 1 else f"{base}trang/{n}/"
                chunk = r["jobs"][(n - 1) * per: n * per]
                ptxt = "" if n == 1 else f" – {t['page']} {n}"
                if lang == "vi":
                    h1 = f"Việc làm {r['vi']} remote ở Việt Nam{ptxt}"
                    desc = f"{len(r['jobs'])} việc làm {r['vi']} remote đang mở từ công ty remote-first tuyển ở Việt Nam, ưu tiên tin ghi rõ Việt Nam/APAC. {len(r['companies'])} công ty thường tuyển {r['vi']}."
                else:
                    h1 = f"Remote {r['en']} jobs for Vietnam{ptxt}"
                    desc = f"{len(r['jobs'])} open remote {r['en']} jobs from remote-first companies hiring in Vietnam, Vietnam/APAC first. {len(r['companies'])} companies that hire {r['en']}."
                cos = "".join(f'<li><a class="chip" href="{url_for(lang, "/cong-ty/" + c["slug"] + "/")}">{e(c["name"])}</a></li>' for c in r["companies"][:40]) if n == 1 else ""
                others = "".join(f'<li><a class="chip" href="{url_for(lang, "/viec-lam-remote/" + x["slug"] + "/")}">{e(x[lang])}</a></li>' for x in roles if x is not r)
                jl = f'<ul class="list">{with_native([job_row(j, co_by[j["company_slug"]], lang) for j in chunk], lang, ads)}</ul>' if chunk else empty_state(lang)
                body = f"""<div class="pagehead"><h1>{e(h1)}</h1><p class="lead">{e(desc)}</p></div>
{support_page.nudge(lang)}
{jl}{pager(lang, base, n, rtotal)}
{('<section><h2>' + e(t['nav_companies']) + '</h2><ul class="chips">' + cos + '</ul></section>') if cos else ''}
<section><h2>{e(t['nav_roles'])}</h2><ul class="chips">{others}</ul></section>"""
                write(lang, path, page(lang, path, h1 + (" | RemoteJob VN" if n == 1 else ""), desc, body,
                                       crumbs=[(t["nav_roles"], "/viec-lam-remote/"), (r[lang], base)] + ([(f"{t['page']} {n}", path)] if n > 1 else []), aside=side),
                      max([j["last_checked"] for j in chunk] or [TODAY]))

        # ---------------- tools (affiliate) page
        cats = ""
        for cat in affiliates["categories"]:
            items = "".join(
                f'<li class="card tool-card"><span class="label aff">{e(t["affiliate"])}</span> '
                f'<a class="t" href="{e(it["url"])}" rel="sponsored nofollow noopener">{e(it["name"])}</a><p class="muted small" style="margin:6px 0 0">{e(it[lang])}</p></li>'
                for it in cat["items"])
            intro = (cat.get("intro") or {}).get(lang)
            intro_html = f'<p class="muted">{e(intro)}</p>' if intro else ""
            cats += f'<section id="{e(cat["id"])}"><h2>{e(cat[lang])}</h2>{intro_html}<ul class="list grid2">{items}</ul></section>'
        toc = "".join(f'<li><a class="chip" href="#{e(cat["id"])}">{e(cat[lang])}</a></li>' for cat in affiliates["categories"])
        body = (f'<div class="pagehead"><h1>{e(t["tools_h1"])}</h1><p class="lead">{e(t["tools_desc"])}</p></div>'
                f'<p class="disclosure" id="disclosure"><span class="label aff">{e(t["affiliate"])}</span><span>{e(t["aff_disclosure"])}</span></p>'
                f'<ul class="chips" style="margin-top:16px">{toc}</ul>{cats}')
        write(lang, "/cong-cu/", page(lang, "/cong-cu/", t["tools_title"], t["tools_desc"], body, crumbs=[(t["nav_tools"], "/cong-cu/")]), TODAY)

        # ---------------- advertise + about + post a job
        post_url = url_for(lang, "/dang-tin/")
        issue_url = e(CFG["REPO_URL"] + "/issues/new?template=post-a-job.yml")
        if status_doc.get("last_link_check"):
            link_note = t["status_link"].format(
                date=fmt_date(status_doc.get("last_link_check"), lang),
                checked=status_doc.get("last_link_checked") or 0,
                alive=status_doc.get("last_link_alive") or 0,
                removed=status_doc.get("last_link_removed") or 0,
                blocked=status_doc.get("last_link_blocked") or 0,
                errors=status_doc.get("last_link_errors") or 0,
            )
        else:
            link_note = t["status_link_none"]
        if lang == "vi":
            adbody = f"""<h1>Quảng cáo &amp; tin tài trợ</h1>
<p>RemoteJob VN miễn phí cho người tìm việc. Chi phí vận hành có thể được bù bằng các hình thức không làm phiền:</p>
<ul><li><b>Vị trí quảng cáo cố định</b>: một ô ở cột phải trên máy tính, và tối đa một thẻ "Quảng cáo" sau mỗi 12 dòng trong danh sách. Không có quảng cáo khi vừa mở trang hoặc khi vào từ kết quả tìm kiếm. Không đặt quảng cáo ở đầu trang công ty.</li>
<li><b>Khi bấm xem tin gốc</b>: hộp thoại gắn nhãn "Quảng cáo / Advertisement" chỉ hiện sau khi bạn bấm liên kết ứng tuyển ra ngoài, tối đa một lần mỗi 3 lượt bấm và mỗi 10 phút. Có nút đóng, nút tiếp tục, và tự mở tin sau khoảng 5 giây. Hộp thoại này chỉ dùng nội dung của trang (quảng cáo nội bộ), không bao giờ là đơn vị Google AdSense. Tắt bằng <code>outbound_interstitial</code> trong site.config.json.</li>
<li><b>Tin tuyển dụng tài trợ</b>: tối đa 3 tin, gắn nhãn "Tài trợ", hiển thị riêng ở đầu trang việc làm, có ngày hết hạn. Chỉ nhận việc remote mở cho người ở Việt Nam, không nhận cờ bạc/cá cược. <a href="{post_url}">Đăng tin tuyển dụng</a>.</li>
<li><b>Liên kết affiliate</b> trên trang Công cụ, luôn gắn nhãn "Affiliate".</li></ul>
<p>{"Script Google AdSense được tải để xác minh tài khoản và cho Auto ads dạng vignette. Ô dành sẵn vẫn là quảng cáo nội bộ cho đến khi có mã vị trí. Cookie quảng cáo và cách từ chối nằm trong <a href=\"" + legal_href(lang, "privacy") + "\">chính sách bảo mật</a>." if adsense.client_id(CFG) else "Chưa tải mạng quảng cáo bên thứ ba. Liên hệ qua GitHub issue của dự án."}</p>"""
            abbody = f"""<h1>Giới thiệu</h1><p>RemoteJob VN là danh bạ cộng đồng các công ty remote-first có tuyển người ở Việt Nam. Dữ liệu là thông tin công khai, mỗi công ty có link nguồn và ngày kiểm tra.</p>
<h2 id="privacy">Quyền riêng tư</h2><p>{"Cloudflare Web Analytics không dùng cookie. Google AdSense có thể dùng cookie quảng cáo khi được bật." if adsense.client_id(CFG) else "Không cookie, không theo dõi cá nhân."} Chi tiết ở <a href="{legal_href(lang, "privacy")}">chính sách bảo mật</a>. Ngôn ngữ chọn bằng đường dẫn (/en/). Trình duyệt có thể lưu lựa chọn giao diện, số lần bấm xem tin và việc bạn đã ẩn thẻ ủng hộ ngay trên máy bạn; dữ liệu đó không được gửi đi.</p>
<h2>Tiêu chí</h2><ul><li>Công ty cho làm remote (hoặc remote-friendly, có ghi rõ) và tuyển người ở Việt Nam.</li><li>Không đưa công ty cờ bạc, cá cược, casino, iGaming.</li><li>Chỉ thông tin công khai, có nguồn.</li></ul>
<h2 id="contribute">Đóng góp</h2><p>Thêm hoặc sửa công ty bằng pull request vào <code>data/companies.json</code>. Xem <a href="{e(CFG['REPO_URL'])}/blob/main/CONTRIBUTING.md" rel="noopener">CONTRIBUTING.md</a>.</p>
<h2>Tin tuyển dụng</h2><p>Tin việc được lấy mỗi ngày từ API tuyển dụng công khai (Greenhouse, Lever, Ashby, Workable, Recruitee, và các feed JSON/XML công khai khác khi công ty dùng). Nguồn chưa có API được kiểm tra link mỗi tuần. Tin không còn sống bị gỡ khỏi danh sách và sitemap, trang noindex được giữ 30 ngày.</p>
<h2 id="status">{e(t["status_h"])}</h2><p>{e(FRESH[lang])}</p><p>{e(link_note)}</p>
<h2 id="license">Giấy phép</h2><p>Dữ liệu: CC BY 4.0. Mã nguồn: MIT.</p>"""
        else:
            adbody = f"""<h1>Advertising &amp; sponsored jobs</h1>
<p>RemoteJob VN is free for job seekers. Running costs may be covered in non-intrusive ways:</p>
<ul><li><b>Fixed ad slots</b>: one box in the right column on desktop, and at most one "Ad" card every 12 rows in lists. Nothing appears on page load or when landing from search. No ad at the top of a company page.</li>
<li><b>Outbound apply click</b>: a dialog labeled "Quảng cáo / Advertisement" opens only after you click through to the original posting, at most once every 3 clicks and once every 10 minutes. It has a close button, a continue button, and opens the job after about 5 seconds. The dialog is house content only and never an AdSense unit. Turn it off with <code>outbound_interstitial</code> in site.config.json.</li>
<li><b>Sponsored jobs</b>: at most 3, labeled "Sponsored", shown separately at the top of the jobs page, with an end date. Remote roles open to people in Vietnam only; no gambling/betting. <a href="{post_url}">Post a job</a>.</li>
<li><b>Affiliate links</b> on the Tools page, always labeled "Affiliate".</li></ul>
<p>{"The Google AdSense script loads for account verification and Auto ads vignettes. Reserved slots stay house ads until slot IDs are set. Advertising cookies and opt-out links are in the <a href=\"" + legal_href(lang, "privacy") + "\">privacy policy</a>." if adsense.client_id(CFG) else "No third-party ad network is loaded. Contact us via a GitHub issue."}</p>"""
            abbody = f"""<h1>About</h1><p>RemoteJob VN is a community directory of remote-first companies that hire people in Vietnam. Data is public information; each company has source links and a last-checked date.</p>
<h2 id="privacy">Privacy</h2><p>{"Cloudflare Web Analytics is cookieless. Google AdSense may use advertising cookies when it is enabled." if adsense.client_id(CFG) else "No cookies and no personal tracking."} Details are in the <a href="{legal_href(lang, "privacy")}">privacy policy</a>. Language is chosen by URL (/en/). The browser may store the theme choice, how often an apply link was clicked (to cap the ad), and whether you dismissed the support note on this device; that data is not sent anywhere.</p>
<h2>Criteria</h2><ul><li>The company allows remote work (or remote-friendly, stated clearly) and hires people in Vietnam.</li><li>No gambling, betting, casino or iGaming companies.</li><li>Public, sourced information only.</li></ul>
<h2 id="contribute">Contributing</h2><p>Add or edit a company with a pull request to <code>data/companies.json</code>. See <a href="{e(CFG['REPO_URL'])}/blob/main/CONTRIBUTING.md" rel="noopener">CONTRIBUTING.md</a>.</p>
<h2>Job data</h2><p>Jobs are fetched daily from public ATS APIs (Greenhouse, Lever, Ashby, Workable, Recruitee, and other public JSON/XML feeds when a company uses one). Sources with no API are link-checked weekly. Dead postings leave the lists and the sitemap; a noindex page is kept for 30 days.</p>
<h2 id="status">{e(t["status_h"])}</h2><p>{e(FRESH[lang])}</p><p>{e(link_note)}</p>
<h2 id="license">License</h2><p>Data: CC BY 4.0. Code: MIT.</p>"""
        write(lang, "/quang-cao/", page(lang, "/quang-cao/", t["ads_title"], t["ads_desc"], adbody, crumbs=[(t["ads_title"], "/quang-cao/")]), TODAY)
        write(lang, "/gioi-thieu/", page(lang, "/gioi-thieu/", t["about_title"], t["about_desc"], abbody, crumbs=[(t["nav_about"], "/gioi-thieu/")]), TODAY)
        if lang == "vi":
            postbody = f"""<h1>Đăng tin tuyển dụng</h1>
<p>Dành cho nhà tuyển dụng muốn đưa một việc remote lên đầu trang chủ và trang việc làm. Người tìm việc vẫn xem danh sách miễn phí.</p>
<h2>Tin tài trợ</h2>
<ul>
<li>Gắn nhãn <b>Tài trợ</b> và hiện riêng, không trộn vào danh sách việc thường.</li>
<li>Tối đa <b>3 tin cùng lúc</b>.</li>
<li>Chỉ nhận việc <b>remote và mở cho người ở Việt Nam</b>. Không nhận cờ bạc, cá cược, casino, iGaming.</li>
<li>Có ngày bắt đầu và ngày hết hạn. Hết hạn thì tin rời khỏi vị trí tài trợ.</li>
</ul>
<h2>Giá</h2>
<p><b>Giá: liên hệ.</b> Chưa có bảng giá công khai. Gửi yêu cầu không phải là đơn hàng đã thanh toán.</p>
<h2>Liên hệ</h2>
<p>Mở một GitHub issue. Không cần email hay số điện thoại.</p>
<p><a class="btn primary" href="{issue_url}" rel="noopener">Gửi yêu cầu đăng tin</a></p>
<p class="muted small">Issue là công khai. Không ghi số điện thoại, ghi chú riêng hay CV.</p>"""
        else:
            postbody = f"""<h1>Post a job</h1>
<p>For employers who want a remote role at the top of the home page and the jobs list. Job seekers still browse the directory for free.</p>
<h2>Sponsored listings</h2>
<ul>
<li>Labeled <b>Sponsored</b> and shown apart from the regular job list.</li>
<li>At most <b>3 listings at a time</b>.</li>
<li>Remote roles <b>open to people in Vietnam</b> only. No gambling, betting, casino or iGaming.</li>
<li>A start date and an end date. After the end date the listing leaves the sponsored slot.</li>
</ul>
<h2>Pricing</h2>
<p><b>Pricing: contact.</b> There is no public rate card. Opening a request is not a paid order.</p>
<h2>Contact</h2>
<p>Open a GitHub issue. No email or phone number is required.</p>
<p><a class="btn primary" href="{issue_url}" rel="noopener">Request a featured listing</a></p>
<p class="muted small">Issues are public. Do not include phone numbers, private notes or CVs.</p>"""
        write(lang, "/dang-tin/", page(lang, "/dang-tin/", t["post_title"], t["post_desc"], postbody,
                                        crumbs=[(t["nav_post"], "/dang-tin/")]), TODAY)
        support_alts = support_page.PATHS
        support_path = support_alts[lang]
        write(lang, support_path, page(
            lang, support_path, t["support_title"], t["support_desc"],
            support_page.body(lang, CFG["REPO_URL"]),
            crumbs=[(t["ft_support"], support_path)], alternates=support_alts), TODAY, alternates=support_alts)
        repo = CFG["REPO_URL"].rstrip("/")
        report_url = e(repo + "/issues/new?template=report-problem.yml")
        add_url = e(repo + "/issues/new?template=add-company.yml")
        for key, title_key, desc_key, renderer in (
            ("privacy", "privacy_title", "privacy_desc", lambda: legal_pages.privacy_body(lang, ads_on=bool(adsense.client_id(CFG)))),
            ("terms", "terms_title", "terms_desc", lambda: legal_pages.terms_body(lang, privacy_href=legal_href(lang, "privacy"))),
            ("contact", "contact_title", "contact_desc", lambda: legal_pages.contact_body(
                lang, repo=repo, report_url=report_url, add_url=add_url, post_url=issue_url)),
        ):
            path = LEGAL_PATHS[key][lang]
            alts = LEGAL_PATHS[key]
            write(lang, path, page(lang, path, t[title_key], t[desc_key], renderer(),
                                   crumbs=[(t[title_key], path)], alternates=alts), TODAY, alternates=alts)

    # ---------------- 404, assets, data index, sitemap, robots
    tv, te = T["vi"], T["en"]
    nf = page("vi", "/404.html", "404 – Không tìm thấy trang | Page not found", tv["nf_body"],
              f'<div class="nf"><div class="code">404</div><h1>{e(tv["nf_title"])}</h1><p class="lead" style="margin:0 auto 8px">{e(tv["nf_body"])}</p>'
              f'<p class="muted" lang="en">{e(te["nf_title"])}. {e(te["nf_body"])}</p>'
              f'<div class="cta" style="justify-content:center"><a class="btn primary" href="/viec-lam/">{e(tv["nav_jobs"])}</a><a class="btn" href="/cong-ty/">{e(tv["nav_companies"])}</a><a class="btn" href="/">{e(tv["nav_home"])}</a></div></div>',
              noindex=True, alt=False, js=True)
    with open(os.path.join(OUT, "404.html"), "w", encoding="utf-8") as fh:
        fh.write(nf)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    with open(os.path.join(OUT, "assets", f"style.{CSS_HASH}.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    with open(os.path.join(OUT, "assets", f"app.{JS_HASH}.js"), "w", encoding="utf-8") as fh:
        fh.write(_minify_js(JS))
    for name in ("vietqr-tpbank.webp", "vietqr-tpbank.png"):
        shutil.copy(os.path.join(ROOT, "site", "assets", name), os.path.join(OUT, "assets", name))
    with open(os.path.join(ROOT, "site", "_headers"), encoding="utf-8") as fh:
        headers = fh.read().replace("{THEME_BOOT_SHA}", THEME_BOOT_SHA)
    if adsense.client_id(CFG):
        script_tokens = []
        if any(adsense.slot_id(CFG, name) for name in adsense.SIZES):
            script_tokens.append("'" + adsense.push_sha() + "'")
        headers = adsense.widen_csp(headers, script_tokens)
    with open(os.path.join(OUT, "_headers"), "w", encoding="utf-8") as fh:
        fh.write(headers)
    client = adsense.client_id(CFG)
    if client:
        with open(os.path.join(OUT, "ads.txt"), "w", encoding="utf-8") as fh:
            fh.write(adsense.ads_txt(client))
    indexnow_key = str(CFG.get("indexnow_key") or "").strip()
    if re.fullmatch(r"[A-Za-z0-9-]{8,128}", indexnow_key):
        with open(os.path.join(OUT, indexnow_key + ".txt"), "w", encoding="utf-8") as fh:
            fh.write(indexnow_key)
    icons(OUT)
    with open(os.path.join(OUT, "site.webmanifest"), "w", encoding="utf-8") as fh:
        json.dump({"name": NAME, "short_name": "RemoteJob", "lang": "vi", "start_url": "/", "display": "standalone",
                   "background_color": "#f8fafc", "theme_color": "#0f766e",
                   "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                             {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
                             {"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml"}]}, fh)
    for f in ("favicon.svg", "CNAME"):
        src = os.path.join(ROOT, "site", f)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(OUT, f))
    og_image(os.path.join(OUT, "og-default.png"))
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    idx = {"cos": {c["slug"]: c["name"] for c in companies},
           "ad": ads.get("native") if ads.get("enabled") else None, "every": ads.get("native_every", 12),
           "jobs": [[j["slug"], j["title"], j["company_slug"], j["region"], j["remote"], " ".join(j["roles"]), j.get("location") or "", j["last_checked"], j.get("salary") or "", 1 if j["company_slug"] in agg_slugs else 0] for j in active]}
    with open(os.path.join(OUT, "data", "jobs-index.json"), "w", encoding="utf-8") as fh:
        json.dump(idx, fh, ensure_ascii=False, separators=(",", ":"))
    for f in ("companies.json", "jobs.json"):  # public open data downloads
        shutil.copy(os.path.join(ROOT, "data", f), os.path.join(OUT, "data", f))

    for lang in LANGS:
        urls = []
        for path, lastmod, alts in sitemap[lang]:
            altmap = alts or {"vi": path, "en": path}
            urls.append(f"<url><loc>{e(absu(lang, path))}</loc><lastmod>{lastmod}</lastmod>"
                        f'<xhtml:link rel="alternate" hreflang="vi" href="{e(absu("vi", altmap["vi"]))}"/>'
                        f'<xhtml:link rel="alternate" hreflang="en" href="{e(absu("en", altmap["en"]))}"/>'
                        f'<xhtml:link rel="alternate" hreflang="x-default" href="{e(absu("vi", altmap["vi"]))}"/></url>')
        with open(os.path.join(OUT, f"sitemap-{lang}.xml"), "w", encoding="utf-8") as fh:
            fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                     'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n")
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                 "".join(f"<sitemap><loc>{SITE}/sitemap-{l}.xml</loc><lastmod>{TODAY}</lastmod></sitemap>\n" for l in LANGS) + "</sitemapindex>\n")
    role_meta = [(slug, vi, en) for slug, vi, en, _tags, _rx, _co in ROLE_PAGES]
    with open(os.path.join(OUT, "llms.txt"), "w", encoding="utf-8") as fh:
        fh.write(llms.llms_txt(SITE, CFG["REPO_URL"], role_meta))
    full_jobs = []
    for job in listed:
        row = dict(job)
        row["company_name"] = co_by[job["company_slug"]]["name"]
        full_jobs.append(row)
    with open(os.path.join(OUT, "llms-full.txt"), "w", encoding="utf-8") as fh:
        fh.write(llms.llms_full_txt(SITE, companies, full_jobs, TODAY))
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(llms.robots_txt(SITE))
    n_pages = sum(len(v) for v in sitemap.values())
    print(f"built {OUT}: {len(companies)} companies, {len(active)} active jobs, {len(listed)} in default listings, "
          f"{len(active) - len(listed)} aggregator jobs withheld from mixed lists, {len(gone)} removed/stale job pages (noindex), "
          f"{n_pages} sitemap URLs, {sum(1 for j in active if job_posting_ld(j, co_by[j['company_slug']]))} JobPosting blocks per language")


def job_posting_ld(j, c):
    """schema.org JobPosting, only when the required facts exist; otherwise None (no JSON-LD)."""
    if company_is_aggregator(c):
        return None  # the record is a job board, not the hiring organization
    if not (j.get("title") and j.get("url") and j.get("date_posted") and c.get("name")):
        return None
    if j.get("remote") != "yes" or j.get("region") not in ("vn", "global"):
        return None  # only claim TELECOMMUTE + Vietnam eligibility when the posting names Vietnam or is worldwide
    d = {"@context": "https://schema.org", "@type": "JobPosting", "title": j["title"],
         "description": f"<p>{html.escape(j.get('description') or j['title'])}</p>",
         "datePosted": j["date_posted"][:10],
         "validThrough": (datetime.date.fromisoformat(j["last_checked"][:10]) + datetime.timedelta(days=CFG["JOB_STALE_DAYS"])).isoformat(),
         "hiringOrganization": {"@type": "Organization", "name": c["name"], "sameAs": c["website"] or c["careers_url"]},
         "jobLocationType": "TELECOMMUTE",
         "applicantLocationRequirements": {"@type": "Country", "name": "VN"},
         "url": j["url"], "directApply": False,
         "identifier": {"@type": "PropertyValue", "name": c["name"], "value": j["key"].split(":", 1)[-1]}}
    return d


def _draw_logo(size):
    """Render the SVG logo geometry with Pillow (4x supersampled)."""
    from PIL import Image, ImageDraw
    k = size * 4 / 64
    img = Image.new("RGBA", (size * 4, size * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size * 4 - 1, size * 4 - 1), int(14 * k), fill="#0f766e")
    w = int(5 * k)
    # arch: quadratic-ish curve from (14,40) up to (32,22) down to (50,40)
    pts = []
    for i in range(41):
        x = 14 + 36 * i / 40
        y = 40 - 18 * (1 - ((x - 32) / 18) ** 2) ** 0.5 * 0.9
        pts.append((x * k, y * k))
    d.line(pts, fill="#5eead4", width=w, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill="#5eead4")
    d.ellipse((26 * k, 16 * k, 38 * k, 28 * k), fill="#ffffff")
    d.line((18 * k, 46 * k, 46 * k, 46 * k), fill="#ffffff", width=w)
    for x in (18, 46):
        d.ellipse((x * k - w / 2, 46 * k - w / 2, x * k + w / 2, 46 * k + w / 2), fill="#ffffff")
    return img.resize((size, size), Image.LANCZOS)


def icons(out):
    """PNG favicons + apple-touch-icon, cached in site/icons/ so builds without Pillow still work."""
    cache = os.path.join(ROOT, "site", "icons")
    names = {"favicon-32.png": 32, "icon-192.png": 192, "icon-512.png": 512, "apple-touch-icon.png": 180}
    if not all(os.path.exists(os.path.join(cache, n)) for n in names):
        try:
            os.makedirs(cache, exist_ok=True)
            for n, sz in names.items():
                img = _draw_logo(sz)
                if n == "apple-touch-icon.png":  # iOS wants an opaque square
                    from PIL import Image
                    bg = Image.new("RGB", (sz, sz), "#0f766e")
                    bg.paste(img, (0, 0), img)
                    img = bg
                img.save(os.path.join(cache, n), optimize=True)
        except ImportError:
            return
    for n in names:
        shutil.copy(os.path.join(cache, n), os.path.join(out, n))


def og_image(fp):
    """Branded 1200x630 Open Graph image, cached at site/og-default.png."""
    src = os.path.join(ROOT, "site", "og-default.png")
    if not os.path.exists(src):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            return
        img = Image.new("RGB", (1200, 630), "#0b1120")
        d = ImageDraw.Draw(img)
        for i in range(630):  # subtle vertical gradient
            c = int(17 + 10 * i / 630)
            d.line((0, i, 1200, i), fill=(11, c, 32 + int(8 * i / 630)))
        d.ellipse((760, -220, 1400, 420), fill="#0f3d3a")
        d.ellipse((900, 300, 1350, 750), fill="#11312f")
        fonts = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]
        fb = next((f for f in fonts if os.path.exists(f)), None)
        fr = fb.replace("-Bold", "") if fb and os.path.exists(fb.replace("-Bold", "")) else fb
        F = lambda f, n: ImageFont.truetype(f, n) if f else ImageFont.load_default()
        img.paste(_draw_logo(120), (80, 80), _draw_logo(120))
        d.text((228, 100), "RemoteJob", font=F(fb, 64), fill="#ffffff")
        wv = d.textlength("RemoteJob ", font=F(fb, 64))
        d.text((228 + wv, 100), "VN", font=F(fb, 64), fill="#5eead4")
        d.text((80, 270), "Việc làm remote", font=F(fb, 76), fill="#ffffff")
        d.text((80, 360), "cho người ở Việt Nam", font=F(fb, 76), fill="#5eead4")
        d.text((80, 470), "Remote-first companies & jobs hiring in Vietnam", font=F(fr, 34), fill="#cbd5e1")
        d.rounded_rectangle((80, 535, 80 + d.textlength(SITE.replace("https://", ""), font=F(fr, 28)) + 40, 585), 25, fill="#134e4a")
        d.text((100, 543), SITE.replace("https://", ""), font=F(fr, 28), fill="#ccfbf1")
        img.save(src, optimize=True)
    shutil.copy(src, fp)


def _minify_js(js):
    """Very conservative: drop full-line // comments and leading indentation."""
    out = []
    for line in js.splitlines():
        st = line.strip()
        if not st or st.startswith("//"):
            continue
        out.append(st)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    main()
