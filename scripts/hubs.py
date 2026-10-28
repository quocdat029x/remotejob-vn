"""Programmatic landing pages and feeds. Facts come only from the jobs passed in.

A hub is published when it has at least MIN_OPEN_JOBS direct-employer listings
that are not explicitly onsite. Curated role pages from ROLE_PAGES are always
emitted so existing URLs stay stable; below the threshold they are noindex.
Nothing here invents jobs, salaries, dates, or companies.
"""
import datetime
import html
import re
from collections import Counter
from email.utils import format_datetime
from xml.sax.saxutils import escape as xml_escape

MIN_OPEN_JOBS = 3
FEED_LIMIT = 50
KIND_ORDER = ("role", "tech", "timezone", "seniority", "salary")

UI = {
    "vi": {
        "faq": "Câu hỏi thường gặp",
        "related": "Danh mục liên quan",
        "companies_open": "Công ty đang có tin trong nhóm này",
        "companies_profile": "Công ty ghi là thường tuyển vai trò này",
        "on_job": "Danh mục",
        "on_company": "Danh mục đang có tin",
        "popular": "Danh mục phổ biến",
        "all": "Mọi danh mục",
        "feed_title": "Việc làm remote mới",
        "feed_desc": "Tin remote mới nhất từ nhà tuyển dụng trực tiếp trên RemoteJob VN.",
        "kinds": {
            "role": "Vai trò",
            "tech": "Kỹ năng",
            "timezone": "Múi giờ",
            "seniority": "Cấp độ",
            "salary": "Lương công khai",
        },
    },
    "en": {
        "faq": "Questions",
        "related": "Related categories",
        "companies_open": "Companies with open jobs in this group",
        "companies_profile": "Companies that list this role",
        "on_job": "Categories",
        "on_company": "Categories with open jobs",
        "popular": "Popular categories",
        "all": "All categories",
        "feed_title": "Newest remote jobs",
        "feed_desc": "Newest listings from direct employers on RemoteJob VN.",
        "kinds": {
            "role": "Roles",
            "tech": "Skills",
            "timezone": "Time zones",
            "seniority": "Seniority",
            "salary": "Public salary",
        },
    },
}

# Extra role pages. Tags are the role tags already stored on a job. Title
# patterns are tighter than the importer where a tag mixes two jobs (product
# and design, sales and marketing).
EXTRA_ROLES = [
    ("backend", "Backend", "Backend", {"backend"}, r"\bbackend\b|back-end|back end"),
    ("frontend", "Frontend", "Frontend", {"frontend"}, r"\bfrontend\b|front-end|front end"),
    ("fullstack", "Fullstack", "Full stack", {"fullstack"}, r"full[- ]?stack"),
    ("mobile", "Mobile", "Mobile", {"mobile"}, r"\bmobile\b|\bios\b|\bandroid\b|\bflutter\b|react native"),
    ("qa", "QA", "QA", set(), r"\bqa\b|quality assurance|\bsdet\b|quality engineer|test engineer"),
    ("product", "Product", "Product", set(), r"product manager|product owner|\bproduct lead\b"),
    ("design", "Design", "Design", set(), r"\bdesigner\b|\bux\b|ui/ux|product design"),
    ("marketing", "Marketing", "Marketing", set(), r"\bmarketing\b|\bseo\b|growth marketing"),
    ("sales", "Sales", "Sales", set(), r"\bsales\b|account executive|business development|\bbdr\b|\bsdr\b"),
    ("support", "Support", "Support", set(), r"\bsupport\b|customer success|customer service"),
]

# Skill words taken from the title only. "Go to market" is not the Go language.
TECHS = [
    ("python", "Python", "Python", r"\bpython\b"),
    ("go", "Go", "Go", r"\bgolang\b|\bgo\b(?![- ]+to[- ]+market)"),
    ("java", "Java", "Java", r"\bjava\b(?!script)"),
    ("react", "React", "React", r"\breact(?:\.js)?\b"),
    ("node", "Node.js", "Node.js", r"\bnode(?:\.js)?\b"),
    ("aws", "AWS", "AWS", r"\baws\b"),
    ("kubernetes", "Kubernetes", "Kubernetes", r"\bkubernetes\b|\bk8s\b"),
    ("typescript", "TypeScript", "TypeScript", r"\btypescript\b"),
    ("rust", "Rust", "Rust", r"\brust\b"),
    ("vue", "Vue", "Vue", r"\bvue(?:\.js)?\b"),
    ("postgres", "PostgreSQL", "PostgreSQL", r"\bpostgres(?:ql)?\b"),
    ("dotnet", ".NET", ".NET", r"\.net\b|\bc#\b|\bdotnet\b"),
    ("ios", "iOS", "iOS", r"\bios\b|\bswift\b"),
    ("android", "Android", "Android", r"\bandroid\b|\bkotlin\b"),
    ("sql", "SQL", "SQL", r"\bsql\b"),
    ("linux", "Linux", "Linux", r"\blinux\b"),
]

# A level is recorded only when the title says so. Untagged titles are not "mid".
SENIORITY = [
    ("junior", "Junior", "Junior", r"\b(?:junior|jr\.?|intern(?:ship)?|entry[- ]level|new grad|graduate)\b"),
    ("mid", "Mid", "Mid-level", r"\b(?:mid[- ]level|intermediate)\b"),
    ("senior", "Senior", "Senior", r"\b(?:senior|sr\.?)\b"),
    ("lead", "Lead", "Lead", r"\b(?:lead|principal|staff)\b|\bhead of\b"),
]

TIMEZONES = [
    ("gio-eu-apac", "Giờ EU / APAC", "EU / APAC hours", "eu-apac"),
    ("gio-my", "Giờ Mỹ", "US hours", "us"),
]

SALARY_SLUG = "luong-cong-khai"

REMOTE_WORD = {
    "vi": {"yes": "Remote", "hybrid": "Hybrid", "no": "Onsite", "unknown": "Chưa rõ remote"},
    "en": {"yes": "Remote", "hybrid": "Hybrid", "no": "Onsite", "unknown": "Remote not stated"},
}

_EXTRA_RX = [(row[0], re.compile(row[4], re.I)) for row in EXTRA_ROLES]
_TECH_RX = [(row[0], re.compile(row[3], re.I)) for row in TECHS]
_SENIOR_RX = [(row[0], re.compile(row[3], re.I)) for row in SENIORITY]


def _esc(text):
    return html.escape(text or "", quote=True)


def _x(text):
    return xml_escape(text or "", {'"': "&quot;", "'": "&apos;"})


def fmt_day(value, lang):
    raw = (value or "")[:10]
    if len(raw) < 10 or raw[4] != "-" or raw[7] != "-":
        return ""
    y, m, d = raw.split("-")
    if not (y.isdigit() and m.isdigit() and d.isdigit()):
        return ""
    return f"{d}/{m}/{y}" if lang == "vi" else raw


def _direct_jobs(jobs, companies):
    out = []
    for job in jobs:
        company = companies.get(job.get("company_slug"))
        if not company or company.get("kind") == "aggregator":
            continue
        if job.get("remote") == "no":
            continue
        out.append(job)
    return out


def _finish(spec, jobs, companies):
    """Attach counts that are fully determined by `jobs`."""
    counts = Counter(job["company_slug"] for job in jobs)
    ranked = []
    for slug, n in counts.most_common():
        company = companies.get(slug)
        if not company:
            continue
        ranked.append({"slug": slug, "name": company.get("name") or slug, "jobs": n})
    ranked.sort(key=lambda row: (-row["jobs"], row["name"].lower()))
    dates = [(job.get("last_checked") or "")[:10] for job in jobs if job.get("last_checked")]
    salaries = []
    for job in jobs:
        text = (job.get("salary") or "").strip()
        if text and text not in salaries:
            salaries.append(text)
    hub = dict(spec)
    hub["jobs"] = list(jobs)
    hub["keys"] = {job["key"] for job in jobs if job.get("key")}
    hub["companies"] = ranked
    hub["top_companies"] = ranked[:3]
    hub["updated"] = max(dates) if dates else ""
    hub["regions"] = Counter(job.get("region") or "other" for job in jobs)
    hub["remote_counts"] = Counter(job.get("remote") or "unknown" for job in jobs)
    hub["salary_count"] = sum(1 for job in jobs if (job.get("salary") or "").strip())
    hub["salary_samples"] = salaries[:3]
    hub["indexable"] = len(jobs) >= MIN_OPEN_JOBS
    hub.setdefault("profile_companies", [])
    hub.setdefault("origin", "generated")
    return hub


def _role_jobs(jobs, tagset, regex):
    rx = re.compile(regex, re.I) if isinstance(regex, str) else regex
    tags = set(tagset or ())
    matched = []
    for job in jobs:
        title = job.get("title") or ""
        if tags and (set(job.get("roles") or ()) & tags):
            matched.append(job)
        elif rx.search(title):
            matched.append(job)
    return matched


def timezone_slugs(job, tz_tags):
    """EU/APAC vs US hours from the company timezone tags and the job region.

    An unknown timezone note is not treated as either, unless the posting's
    own region is Vietnam or APAC.
    """
    tags = set(tz_tags or ())
    found = []
    if tags & {"vn", "apac", "eu"} or job.get("region") in ("vn", "apac"):
        found.append("gio-eu-apac")
    if "us" in tags:
        found.append("gio-my")
    return found


def collect(jobs, companies, role_pages):
    """Return hub dicts. `companies` is keyed by slug and may carry `_tz`."""
    direct = _direct_jobs(jobs, companies)
    reserved = {row[0] for row in role_pages}
    hubs = []
    seen_sets = []

    def add(hub, force=False):
        signature = frozenset(hub["keys"])
        if not force and signature in seen_sets:
            return None
        if not force and not hub["indexable"]:
            return None
        seen_sets.append(signature)
        hubs.append(hub)
        return hub

    for slug, vi, en, tagset, regex, co_roles in role_pages:
        matched = _role_jobs(direct, tagset, regex)
        profile = []
        wanted = set(co_roles or ())
        for company in companies.values():
            if company.get("kind") == "aggregator":
                continue
            if wanted and (set(company.get("hires_roles") or ()) & wanted):
                profile.append({"slug": company["slug"], "name": company.get("name") or company["slug"]})
        profile.sort(key=lambda row: row["name"].lower())
        hub = _finish(
            {"kind": "role", "slug": slug, "path": f"/viec-lam-remote/{slug}/", "vi": vi, "en": en,
             "origin": "curated", "profile_companies": profile},
            matched, companies)
        add(hub, force=True)

    for slug, vi, en, tagset, regex in EXTRA_ROLES:
        if slug in reserved:
            continue
        matched = _role_jobs(direct, tagset, regex)
        hub = _finish(
            {"kind": "role", "slug": slug, "path": f"/viec-lam-remote/{slug}/", "vi": vi, "en": en},
            matched, companies)
        add(hub)

    for slug, vi, en, regex in TECHS:
        if slug in reserved or any(h["slug"] == slug for h in hubs):
            continue
        rx = re.compile(regex, re.I)
        matched = [job for job in direct if rx.search(job.get("title") or "")]
        hub = _finish(
            {"kind": "tech", "slug": slug, "path": f"/viec-lam-remote/{slug}/", "vi": vi, "en": en},
            matched, companies)
        add(hub)

    for slug, vi, en, regex in SENIORITY:
        rx = re.compile(regex, re.I)
        matched = [job for job in direct if rx.search(job.get("title") or "")]
        hub = _finish(
            {"kind": "seniority", "slug": slug, "path": f"/viec-lam-remote/{slug}/", "vi": vi, "en": en},
            matched, companies)
        add(hub)

    grouped = {"gio-eu-apac": [], "gio-my": []}
    for job in direct:
        company = companies.get(job["company_slug"]) or {}
        for slug in timezone_slugs(job, company.get("_tz")):
            grouped[slug].append(job)
    for slug, vi, en, _key in TIMEZONES:
        hub = _finish(
            {"kind": "timezone", "slug": slug, "path": f"/viec-lam-remote/{slug}/", "vi": vi, "en": en},
            grouped[slug], companies)
        add(hub)

    paid = [job for job in direct if (job.get("salary") or "").strip()]
    hub = _finish(
        {"kind": "salary", "slug": SALARY_SLUG, "path": f"/viec-lam-remote/{SALARY_SLUG}/",
         "vi": "Lương công khai", "en": "Public salary"},
        paid, companies)
    add(hub)
    return hubs


def h1_for(hub, lang, page_n=1):
    name = hub[lang]
    kind = hub["kind"]
    if lang == "vi":
        if kind == "salary":
            text = "Việc làm remote có lương công khai"
        elif hub["slug"] == "gio-eu-apac":
            text = "Việc làm remote hợp giờ EU và APAC"
        elif hub["slug"] == "gio-my":
            text = "Việc làm remote theo giờ Mỹ"
        elif kind == "seniority":
            text = f"Việc làm remote cấp {name}"
        elif kind == "tech":
            text = f"Việc làm remote {name}"
        else:
            text = f"Việc làm {name} remote đang mở"
        if page_n > 1:
            text += f" – trang {page_n}"
        return text
    if kind == "salary":
        text = "Remote jobs with a public salary"
    elif hub["slug"] == "gio-eu-apac":
        text = "Remote jobs suited to EU and APAC hours"
    elif hub["slug"] == "gio-my":
        text = "Remote jobs on US hours"
    elif kind == "seniority":
        text = f"Remote {name} jobs"
    elif kind == "tech":
        text = f"Remote {name} jobs"
    else:
        text = f"Remote {name} jobs open now"
    if page_n > 1:
        text += f" – page {page_n}"
    return text


def _workplace(hub, lang):
    rem = hub.get("remote_counts") or {}
    if lang == "vi":
        parts = []
        if rem.get("yes"):
            parts.append(f"{rem['yes']} tin ghi remote")
        if rem.get("hybrid"):
            parts.append(f"{rem['hybrid']} tin hybrid")
        if rem.get("unknown"):
            parts.append(f"{rem['unknown']} tin chưa ghi rõ remote")
        return ("Hình thức trên tin: " + ", ".join(parts) + ".") if parts else ""
    parts = []
    if rem.get("yes"):
        parts.append(f"{rem['yes']} remote")
    if rem.get("hybrid"):
        parts.append(f"{rem['hybrid']} hybrid")
    if rem.get("unknown"):
        parts.append(f"{rem['unknown']} not stated")
    return ("Workplace on the posting: " + ", ".join(parts) + ".") if parts else ""


def topic_phrase(hub, lang):
    """Natural phrase for counts, so a salary hub does not read as a job title."""
    name = hub[lang]
    if lang == "vi":
        if hub["kind"] == "salary":
            return "có lương công khai"
        if hub["slug"] == "gio-eu-apac":
            return "hợp giờ EU và APAC"
        if hub["slug"] == "gio-my":
            return "theo giờ Mỹ"
        if hub["kind"] == "seniority":
            return f"cấp {name}"
        return name
    if hub["kind"] == "salary":
        return "with a public salary"
    if hub["slug"] == "gio-eu-apac":
        return "suited to EU and APAC hours"
    if hub["slug"] == "gio-my":
        return "on US hours"
    if hub["kind"] == "seniority":
        return f"at {name} level"
    return name


def intro_for(hub, lang, page_n=1):
    n = len(hub["jobs"])
    companies = len(hub["companies"])
    phrase = topic_phrase(hub, lang)
    date = fmt_day(hub.get("updated"), lang)
    tops = hub.get("top_companies") or []
    if lang == "vi":
        text = f"Có {n} việc {phrase} đang mở, từ {companies} công ty tuyển trực tiếp."
        if tops:
            text += " Nhiều tin nhất: " + ", ".join(f"{row['name']} ({row['jobs']})" for row in tops) + "."
        if date:
            text += f" Lần kiểm tra mới nhất: {date}."
    else:
        if hub["kind"] == "salary":
            text = f"{n} open listings publish a salary, from {companies} direct employers."
        elif hub["kind"] == "timezone":
            text = f"{n} open listings are {phrase}, from {companies} direct employers."
        elif hub["kind"] == "seniority":
            text = f"{n} open listings are {phrase}, from {companies} direct employers."
        else:
            text = f"{n} open {phrase} listings from {companies} direct employers."
        if tops:
            text += " Most listings: " + ", ".join(f"{row['name']} ({row['jobs']})" for row in tops) + "."
        if date:
            text += f" Newest check in this group: {date}."
    workplace = _workplace(hub, lang)
    if workplace:
        text += " " + workplace
    if page_n > 1:
        text = (f"Trang {page_n}. " if lang == "vi" else f"Page {page_n}. ") + text
    return " ".join(text.split())


def _method_faq(hub, lang):
    n = len(hub["jobs"])
    name = hub[lang]
    kind = hub["kind"]
    if lang == "vi":
        if kind == "tech":
            return (f"Từ khoá {name} được lấy từ đâu?",
                    f"Từ tiêu đề tin, đúng từ đã khai cho trang {name}. Không suy ra từ công nghệ gần nghĩa. Trang này có {n} tin.")
        if kind == "seniority":
            return ("Cấp độ được xác định thế nào?",
                    f"Chỉ khi tiêu đề ghi junior, mid, senior, lead, principal, staff hoặc head of. Tiêu đề không ghi cấp không nằm ở trang cấp độ. Trang {name} có {n} tin.")
        if hub["slug"] == "gio-eu-apac":
            return ("Vì sao tin nằm ở trang giờ EU / APAC?",
                    f"Công ty có ghi chú múi giờ Việt Nam, APAC hoặc EU, hoặc tin có khu vực Việt Nam/APAC. Ghi chú chưa rõ không được tính, trừ khi khu vực tin là Việt Nam hoặc APAC. Trang này có {n} tin.")
        if hub["slug"] == "gio-my":
            return ("Vì sao tin nằm ở trang giờ Mỹ?",
                    f"Công ty có ghi chú múi giờ Mỹ. Không suy ra giờ Mỹ từ địa điểm trong tiêu đề. Trang này có {n} tin.")
        if kind == "role":
            return (f"Tin được chọn vào trang {name} bằng cách nào?",
                    f"Khớp thẻ vai trò hoặc cụm trong tiêu đề của trang {name}. Tin ghi onsite không được tính. Trang này có {n} tin.")
        return None
    if kind == "tech":
        return (f"Where does the {name} keyword come from?",
                f"From the job title, using the {name} pattern for this page. A similar technology is not assumed. This page has {n} listings.")
    if kind == "seniority":
        return ("How is seniority decided?",
                f"Only when the title says junior, mid, senior, lead, principal, staff, or head of. Titles with no level word are not placed on a seniority page. The {name} page has {n} listings.")
    if hub["slug"] == "gio-eu-apac":
        return ("Why is a job on the EU / APAC hours page?",
                f"The company timezone note says Vietnam, APAC, or EU hours, or the posting region is Vietnam or APAC. An unknown note is not counted unless the region is Vietnam or APAC. This page has {n} listings.")
    if hub["slug"] == "gio-my":
        return ("Why is a job on the US hours page?",
                f"The company timezone note says US hours. US hours are not inferred from a place name in the title. This page has {n} listings.")
    if kind == "role":
        return (f"How does a job land on the {name} page?",
                f"It matches this page's role tag or title phrase. Postings marked onsite are left out. This page has {n} listings.")
    return None


def faqs_for(hub, lang):
    """Question/answer pairs whose numbers are the hub's own counts."""
    n = len(hub["jobs"])
    name = hub[lang]
    companies = len(hub["companies"])
    date = fmt_day(hub.get("updated"), lang)
    tops = hub.get("top_companies") or []
    regs = hub.get("regions") or {}
    sal_n = hub.get("salary_count") or 0
    samples = hub.get("salary_samples") or []
    out = []
    phrase = topic_phrase(hub, lang)
    if lang == "vi":
        when = f" Ngày kiểm tra mới nhất trong nhóm là {date}." if date else ""
        out.append((
            f"Hiện có bao nhiêu việc {phrase} đang mở?",
            f"Có {n} tin đang mở từ {companies} công ty tuyển trực tiếp.{when}",
        ))
        if tops:
            bits = ", ".join(f"{row['name']} ({row['jobs']} tin)" for row in tops)
            out.append((
                f"Công ty nào đang có nhiều tin {phrase} nhất?",
                f"Nhiều tin nhất: {bits}. Chỉ tính tin đang mở của nhà tuyển dụng trực tiếp.",
            ))
        labels = (("vn", "Việt Nam"), ("apac", "APAC"), ("global", "toàn cầu"), ("other", "không ghi rõ khu vực"))
        bits = [f"{regs[key]} tin ghi {label}" for key, label in labels if regs.get(key)]
        detail = ("; ".join(bits) + ". ") if bits else ""
        out.append((
            f"Các tin {phrase} có ghi tuyển ở Việt Nam không?",
            "Không phải tin nào cũng ghi Việt Nam. " + detail + "Hãy đọc tin gốc. Thư mục chỉ gồm công ty remote-first có thông tin tuyển người ở Việt Nam.",
        ))
        if hub["kind"] == "salary":
            sample = (" Ví dụ đang có trên tin: " + "; ".join(samples) + ".") if samples else ""
            out.append((
                "Lương trên trang này lấy từ đâu?",
                f"{sal_n} tin có chuỗi lương chép từ tin gốc.{sample} RemoteJob VN không ước tính lương.",
            ))
        else:
            out.append((
                f"Bao nhiêu tin {name} ghi lương công khai?",
                f"{sal_n} trong {n} tin có chuỗi lương trên tin gốc. RemoteJob VN không ước tính lương.",
            ))
    else:
        when = f" The newest check in this group is {date}." if date else ""
        if hub["kind"] == "salary":
            count_q = "How many open listings publish a salary?"
        elif hub["kind"] in ("timezone", "seniority"):
            count_q = f"How many open listings are {phrase}?"
        else:
            count_q = f"How many open {phrase} listings are there?"
        out.append((
            count_q,
            f"{n} open listings from {companies} direct employers.{when}",
        ))
        if tops:
            bits = ", ".join(f"{row['name']} ({row['jobs']})" for row in tops)
            out.append((
                "Which companies have the most listings with a public salary?" if hub["kind"] == "salary"
                else f"Which companies have the most listings {phrase}?" if hub["kind"] in ("timezone", "seniority")
                else f"Which companies have the most {phrase} listings?",
                f"Most listings: {bits}. Only open jobs from direct employers are counted.",
            ))
        labels = (("vn", "Vietnam"), ("apac", "APAC"), ("global", "worldwide"), ("other", "no region stated"))
        bits = [f"{regs[key]} say {label}" for key, label in labels if regs.get(key)]
        detail = ("; ".join(bits) + ". ") if bits else ""
        out.append((
            f"Do these listings say they hire in Vietnam?",
            "Not every posting names Vietnam. " + detail + "Read the original posting. The directory only includes remote-first companies with public information about hiring in Vietnam.",
        ))
        if hub["kind"] == "salary":
            sample = (" Examples copied from postings: " + "; ".join(samples) + ".") if samples else ""
            out.append((
                "Where do the salary figures come from?",
                f"{sal_n} listings include a salary string copied from the original posting.{sample} RemoteJob VN does not estimate pay.",
            ))
        else:
            out.append((
                f"How many of these listings publish a salary?",
                f"{sal_n} of {n} listings include a salary string from the original posting. RemoteJob VN does not estimate pay.",
            ))
    method = _method_faq(hub, lang)
    if method:
        out.append(method)
    return out


def page_copy(hub, lang, page_n=1):
    h1 = h1_for(hub, lang, page_n)
    intro = intro_for(hub, lang, page_n)
    description = intro if len(intro) <= 300 else intro[:300].rsplit(" ", 1)[0]
    return {
        "h1": h1,
        "title": h1 + " | RemoteJob VN",
        "description": description,
        "intro": intro,
        "faq": faqs_for(hub, lang) if page_n == 1 else [],
        "og_title": (hub["en"] or hub["slug"]).upper(),
    }


def faq_jsonld(pairs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": answer}}
            for question, answer in pairs
        ],
    }


def related(hub, catalog, limit=8):
    """Same-kind hubs first, then other hubs that share at least one job."""
    others = [item for item in catalog if item["path"] != hub["path"] and item.get("indexable")]
    same = sorted((item for item in others if item["kind"] == hub["kind"]), key=lambda item: (-len(item["jobs"]), item["slug"]))
    keys = hub["keys"]
    cross = [item for item in others if item["kind"] != hub["kind"] and (keys & item["keys"])]
    cross.sort(key=lambda item: (-len(keys & item["keys"]), item["slug"]))
    out = []
    seen = set()
    for item in list(same) + cross[:4]:
        if item["path"] in seen:
            continue
        out.append(item)
        seen.add(item["path"])
        if len(out) >= limit:
            break
    return out


def pick_diverse(hubs, limit):
    ordered = sorted(hubs, key=lambda item: (-len(item["jobs"]), item["slug"]))
    by_kind = {}
    for item in ordered:
        by_kind.setdefault(item["kind"], []).append(item)
    picked = []
    seen = set()
    for kind in KIND_ORDER:
        group = by_kind.get(kind) or []
        if not group:
            continue
        item = group[0]
        picked.append(item)
        seen.add(item["path"])
        if len(picked) >= limit:
            return picked
    for item in ordered:
        if item["path"] in seen:
            continue
        picked.append(item)
        seen.add(item["path"])
        if len(picked) >= limit:
            break
    return picked


def index_html(catalog, lang, url, h1, lead):
    ui = UI[lang]
    parts = [f'<div class="pagehead"><h1>{_esc(h1)}</h1><p class="lead">{_esc(lead)}</p></div>']
    for kind in KIND_ORDER:
        group = [item for item in catalog if item["kind"] == kind and item.get("indexable")]
        if not group:
            continue
        group.sort(key=lambda item: (-len(item["jobs"]), item[lang].lower()))
        chips = "".join(
            f'<li><a class="chip" href="{_esc(url(item["path"]))}">{_esc(item[lang])} <span class="n">{len(item["jobs"])}</span></a></li>'
            for item in group)
        parts.append(f'<section><h2>{_esc(ui["kinds"][kind])}</h2><ul class="chips">{chips}</ul></section>')
    return "\n".join(parts)


def sections_html(hub, lang, jobs_html, related_hubs, url, *, pager_html="", before_list="", page_n=1):
    """Visible hub body. `jobs_html` is the caller-rendered list (real jobs only)."""
    copy = page_copy(hub, lang, page_n)
    ui = UI[lang]
    parts = [f'<div class="pagehead"><h1>{_esc(copy["h1"])}</h1><p class="lead">{_esc(copy["intro"])}</p></div>']
    if before_list and page_n == 1:
        parts.append(before_list)
    parts.append(jobs_html)
    if pager_html:
        parts.append(pager_html)
    if page_n == 1:
        open_cos = (hub.get("companies") or [])[:40]
        if open_cos:
            chips = "".join(
                f'<li><a class="chip" href="{_esc(url("/cong-ty/" + row["slug"] + "/"))}">{_esc(row["name"])} <span class="n">{row["jobs"]}</span></a></li>'
                for row in open_cos)
            parts.append(f'<section><h2>{_esc(ui["companies_open"])}</h2><ul class="chips">{chips}</ul></section>')
        open_slugs = {row["slug"] for row in open_cos}
        profile = [row for row in (hub.get("profile_companies") or []) if row["slug"] not in open_slugs][:24]
        if profile:
            chips = "".join(
                f'<li><a class="chip" href="{_esc(url("/cong-ty/" + row["slug"] + "/"))}">{_esc(row["name"])}</a></li>'
                for row in profile)
            parts.append(f'<section><h2>{_esc(ui["companies_profile"])}</h2><ul class="chips">{chips}</ul></section>')
        if related_hubs:
            chips = "".join(
                f'<li><a class="chip" href="{_esc(url(item["path"]))}">{_esc(item[lang])} <span class="n">{len(item["jobs"])}</span></a></li>'
                for item in related_hubs)
            parts.append(f'<section><h2>{_esc(ui["related"])}</h2><ul class="chips">{chips}</ul></section>')
        if copy["faq"]:
            blocks = "".join(f"<h3>{_esc(question)}</h3><p>{_esc(answer)}</p>" for question, answer in copy["faq"])
            parts.append(f'<section class="faq" id="faq"><h2>{_esc(ui["faq"])}</h2><div class="panel">{blocks}</div></section>')
    return "\n".join(parts), copy


def chip_html(hubs, lang, url):
    return "".join(
        f'<li><a class="chip" href="{_esc(url(item["path"]))}">{_esc(item[lang])} <span class="n">{len(item["jobs"])}</span></a></li>'
        for item in hubs)


def feed_items(jobs, companies, lang, absolute, limit=FEED_LIMIT):
    """Newest direct listings. Dates and salaries are copied, never filled in."""
    ranked = sorted(jobs, key=lambda job: (
        (job.get("date_posted") or job.get("first_seen") or job.get("last_checked") or ""),
        (job.get("last_checked") or ""),
        (job.get("title") or ""),
    ), reverse=True)
    items = []
    words = REMOTE_WORD[lang]
    for job in ranked[:limit]:
        company = companies.get(job.get("company_slug")) or {}
        name = company.get("name") or job.get("company_slug") or ""
        date = (job.get("date_posted") or job.get("first_seen") or job.get("last_checked") or "")[:10]
        bits = [name]
        if job.get("location"):
            bits.append(job["location"])
        bits.append(words.get(job.get("remote") or "unknown", words["unknown"]))
        salary = (job.get("salary") or "").strip()
        if salary:
            bits.append(salary)
        items.append({
            "title": f"{job.get('title') or ''} – {name}",
            "url": absolute(job.get("path") or "/"),
            "date": date if len(date) == 10 else "",
            "summary": " · ".join(bit for bit in bits if bit),
        })
    return items


def _rfc822(day):
    if not day:
        return ""
    year, month, dom = (int(part) for part in day.split("-"))
    return format_datetime(datetime.datetime(year, month, dom, tzinfo=datetime.timezone.utc))


def rss_xml(items, *, title, link, description, language, self_url):
    dates = [item["date"] for item in items if item.get("date")]
    updated = max(dates) if dates else ""
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        "<channel>",
        f"<title>{_x(title)}</title>",
        f"<link>{_x(link)}</link>",
        f"<description>{_x(description)}</description>",
        f"<language>{_x(language)}</language>",
        f"<atom:link xmlns:atom=\"http://www.w3.org/2005/Atom\" href=\"{_x(self_url)}\" rel=\"self\" type=\"application/rss+xml\"/>",
    ]
    if updated:
        body.append(f"<lastBuildDate>{_x(_rfc822(updated))}</lastBuildDate>")
    for item in items:
        body.append("<item>")
        body.append(f"<title>{_x(item['title'])}</title>")
        body.append(f"<link>{_x(item['url'])}</link>")
        body.append(f"<guid isPermaLink=\"true\">{_x(item['url'])}</guid>")
        if item.get("date"):
            body.append(f"<pubDate>{_x(_rfc822(item['date']))}</pubDate>")
        body.append(f"<description>{_x(item['summary'])}</description>")
        body.append("</item>")
    body.append("</channel></rss>\n")
    return "\n".join(body)


def atom_xml(items, *, title, link, description, self_url, updated):
    dates = [item["date"] for item in items if item.get("date")]
    stamp = max(dates) if dates else (updated or "")
    stamp = f"{stamp}T00:00:00Z" if stamp else "1970-01-01T00:00:00Z"
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"<title>{_x(title)}</title>",
        f"<subtitle>{_x(description)}</subtitle>",
        f'<link href="{_x(link)}" rel="alternate"/>',
        f'<link href="{_x(self_url)}" rel="self"/>',
        f"<id>{_x(self_url)}</id>",
        f"<updated>{_x(stamp)}</updated>",
        "<author><name>RemoteJob VN</name></author>",
    ]
    for item in items:
        when = f"{item['date']}T00:00:00Z" if item.get("date") else stamp
        body.append("<entry>")
        body.append(f"<title>{_x(item['title'])}</title>")
        body.append(f'<link href="{_x(item["url"])}"/>')
        body.append(f"<id>{_x(item['url'])}</id>")
        body.append(f"<updated>{_x(when)}</updated>")
        body.append(f"<summary>{_x(item['summary'])}</summary>")
        body.append("</entry>")
    body.append("</feed>\n")
    return "\n".join(body)


def json_feed(items, *, title, link, description, language, self_url):
    feed_items = []
    for item in items:
        row = {"id": item["url"], "url": item["url"], "title": item["title"], "content_text": item["summary"]}
        if item.get("date"):
            row["date_published"] = item["date"] + "T00:00:00Z"
        feed_items.append(row)
    return {
        "version": "https://jsonfeed.org/version/1.1",
        "title": title,
        "home_page_url": link,
        "feed_url": self_url,
        "description": description,
        "language": language,
        "items": feed_items,
    }
