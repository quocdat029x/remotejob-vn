"""Shared rules that decide whether a scraped link is a real, specific job posting.

Used by scripts/import_seed.py (one-off seed import) and scripts/refresh_jobs.py.
Stdlib only. Every rule is documented in docs/JOB_FILTER_RULES.md.
"""
import datetime
import re
import urllib.parse as up

# Public JSON/XML applicant-tracking feeds. HTML-only sources are not in this set;
# their open jobs are link-checked instead of re-fetched. See docs/JOB_FILTER_RULES.md.
API_ATS = {
    "greenhouse", "lever", "ashby", "workable", "recruitee",
    "smartrecruiters", "personio", "teamtailor", "bamboohr", "breezy",
    "jazzhr", "pinpoint", "rippling",
}

# 1) ATS APIs: URL must point at a single posting.
API_URL_RX = {
    "greenhouse": re.compile(r"(/jobs/\d+|gh_jid=\d+)"),
    "lever": re.compile(r"jobs\.lever\.co/[^/]+/[0-9a-f-]{36}"),
    "ashby": re.compile(r"jobs\.ashbyhq\.com/[^/]+/[0-9a-f-]{36}"),
    "workable": re.compile(r"/j/[A-Z0-9]{6,}"),
    "recruitee": re.compile(r"/o/[^/?#]+"),
    "smartrecruiters": re.compile(r"jobs\.smartrecruiters\.com/[^/]+/\d+"),
    "personio": re.compile(r"jobs\.personio\.(de|com)/job/\d+"),
    "teamtailor": re.compile(r"/jobs/\d+"),
    "bamboohr": re.compile(r"bamboohr\.com/(?:careers|jobs)/\d+"),
    "breezy": re.compile(r"breezy\.hr/p/[^/?#]+"),
    "jazzhr": re.compile(r"applytojob\.com/apply/[^/]+/[^/?#]+"),
    "pinpoint": re.compile(r"/postings/[^/?#]+"),
    "rippling": re.compile(r"ats\.rippling\.com/[^/]+/jobs/[^/?#]+"),
}

# 2) HTML sources: per-host allowlist of "single posting" URL shapes.
HTML_URL_RX = [
    re.compile(r"^https://itviec\.com/it-jobs/[a-z0-9.+-]+-\d+$"),          # ITviec posting ends in -<id>
    re.compile(r"^https://(www\.)?linkedin\.com/jobs/view/\d+"),
    re.compile(r"^https://himalayas\.app/companies/[^/]+/jobs/[^/]+$"),
    re.compile(r"^https://nkktech\.com/(vi/|en/)?careers/[a-z0-9-]+$"),
    re.compile(r"^https://memo\.d\.foundation/careers/open-positions/[a-z0-9-]+$"),
    re.compile(r"^https://cloudx\.com\.vn/tuyen-dung/[a-z0-9-]+-aid\d+$"),
    re.compile(r"^https://www\.ikonnectvn\.com/jobs/[a-z0-9-]+-jo\d+$"),
    re.compile(r"^https://fly\.io/jobs/[a-z0-9-]+$"),
    re.compile(r"^https://[a-z0-9-]+\.applytojob\.com/apply/[A-Za-z0-9]+/[^/]+$"),
]

# 3) Generic deny rules (applied to every source).
DENY_URL_RX = re.compile(
    r"(\.xml|\.rss|/feed|/blog/|/signup|/sign-up|/login|/privacy|policy|career-advice|career-planning|"
    r"job-description-generator|/jobseeker|/organisations/|context\.item)", re.I)
NAV_TITLES = {
    "learn more", "read more", "apply", "apply now", "join us", "see open positions", "sign up", "submit application",
    "xem & ứng tuyển", "xem chi tiết", "ứng tuyển", "rss feed", "career advice", "view all jobs", "open positions",
}
_YEAR_RX = re.compile(r"\b(20\d{2})\b")


def title_has_stale_year(title, today=None):
    """True when the title names a calendar year from 2010 through last year.

    The window follows the date the filter runs (or `today` in tests). A title
    that says "DevOps - 07/2023" is an old listing; the current calendar year
    and later years are kept. Years before 2010 are ignored.
    """
    today = today or datetime.date.today()
    for match in _YEAR_RX.finditer(title or ""):
        year = int(match.group(1))
        if 2010 <= year < today.year:
            return True
    return False


def slug_to_title(url):
    last = urllib_path_last(url)
    last = re.sub(r"-(aid|jo)?\d+$", "", last)
    return re.sub(r"\s+", " ", last.replace("-", " ")).strip().title()


def urllib_path_last(url):
    return [p for p in up.urlparse(url).path.split("/") if p][-1] if up.urlparse(url).path.strip("/") else ""


def clean_title(title, url):
    t = re.sub(r"\s+", " ", title or "").strip()
    t = re.sub(r"\s*(Remote\s*)?Apply( now)?$", "", t, flags=re.I).strip()     # applytojob / ikonnect suffix
    t = re.sub(r"\s*#.*$", "", t).strip()                                       # ikonnect "# HCMC # Hybrid" tags
    t = re.sub(r"^JO\d+\s+", "", t)                                              # ikonnect internal code
    if t.lower() in NAV_TITLES or len(t) < 4:
        t = slug_to_title(url)
    return t


def is_job(ats, url, title, today=None):
    """Return (ok, reason). `today` overrides the clock for the stale-year rule."""
    if not url or not url.startswith("http"):
        return False, "no-url"
    if DENY_URL_RX.search(url):
        return False, "nav-or-policy-link"
    if ats in API_URL_RX:
        if not API_URL_RX[ats].search(url):
            return False, "api-url-not-a-posting"
        if title_has_stale_year(title, today):
            return False, "stale (old year in title)"
        return True, "api"
    if not any(rx.search(url) for rx in HTML_URL_RX):
        return False, "html-url-not-a-posting (category/listing/nav)"
    if title_has_stale_year(title, today):
        return False, "stale (old year in title)"
    return True, "html"


ROLE_RULES = [
    ("sre", r"\bsre\b|site reliability|reliability eng"),
    ("devops", r"devops|dev ops|devsecops|release eng|build eng"),
    ("platform", r"platform eng|platform\b|kubernetes|k8s"),
    ("infra", r"infra|cloud eng|cloud architect|systems? eng|system admin|sysadmin|network eng|\bit\b ops|linux|storage"),
    ("security", r"secur|appsec|soc analyst|pentest"),
    ("data", r"\bdata\b|analytics|\bbi\b|database|dba|etl"),
    ("ai-ml", r"\bai\b|\bml\b|machine learning|mlops|llm|deep learning|research scien|computer vision|\bgpu\b"),
    ("backend", r"backend|back-end|back end|server|golang|\bgo\b|java\b|python|node|ruby|rails|\.net|php|rust|scala|elixir"),
    ("frontend", r"frontend|front-end|front end|react|vue|angular|\bui\b"),
    ("fullstack", r"full.?stack"),
    ("mobile", r"mobile|ios|android|flutter|react native"),
    ("blockchain", r"blockchain|solidity|smart contract|web3|protocol eng"),
    ("qa", r"\bqa\b|quality|test|sdet"),
    ("engineering", r"engineer|developer|programmer|architect|\bswe\b|tech lead|cto"),
    ("product-design", r"product manager|product owner|designer|ux|\bpm\b"),
    ("sales-marketing", r"sales|account exec|marketing|growth|seo|content|social media|partnership|business dev|\bbd\b|gtm"),
    ("support-ops", r"support|customer|success|operations|recruit|talent|\bhr\b|people|finance|account|legal|compliance|admin"),
]
_ROLE_RX = [(k, re.compile(v, re.I)) for k, v in ROLE_RULES]


def job_roles(title):
    tags = [k for k, rx in _ROLE_RX if rx.search(title or "")]
    if len(tags) > 1 and "engineering" in tags:
        tags.remove("engineering")
    return tags or ["other"]


VN_RX = re.compile(r"viet ?nam|hanoi|ha noi|ho chi minh|hcmc|\bhcm\b|saigon|da nang|can tho|tp\.hcm", re.I)
APAC_RX = re.compile(r"apac|apj|asia|singapore|malaysia|thailand|philippines|indonesia|utc\+7|gmt\+7|sea\b|southeast", re.I)
GLOBAL_RX = re.compile(r"worldwide|anywhere|global|remote job|100% remote", re.I)
REMOTE_RX = re.compile(r"remote|telecommuting=true|work from home|wfh", re.I)


def job_region(title, location):
    s = f"{title} {location or ''}"
    if VN_RX.search(s):
        return "vn"
    if APAC_RX.search(s):
        return "apac"
    if GLOBAL_RX.search(s):
        return "global"
    return "other"


def job_remote(title, location):
    s = f"{title} {location or ''}"
    if re.search(r"hybrid", title or "", re.I) and not REMOTE_RX.search(title or ""):
        return "hybrid"  # the title is more specific than an ATS-wide workplace flag
    if re.search(r"remote=false|telecommuting=false|onsite|on-site", s, re.I) and not re.search(r"remote=true|telecommuting=true", s, re.I):
        return "no" if not REMOTE_RX.search(title or "") else "yes"
    if re.search(r"hybrid", s, re.I):
        return "hybrid"
    return "yes" if REMOTE_RX.search(s) else "unknown"


def tidy_location(loc):
    if not loc:
        return None
    parts = [p.strip(" ,") for p in loc.split("|")]
    parts = [p for p in parts if p and not re.fullmatch(r"(remote|telecommuting)=(true|false|none)( \w+)?|None|", p, re.I)]
    out = " · ".join(dict.fromkeys(parts))
    return out or None


def excerpt(text, limit=600):
    """Short plain-text excerpt of a public job description (we always link to the original)."""
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()
    if not t:
        return None
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0]
    return cut + " …"
