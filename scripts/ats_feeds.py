"""Parsers for public, unauthenticated ATS feeds.

Each parser takes the response body (and the source record) and returns the same
raw job dicts refresh_jobs.py already understands: key, title, location, url,
salary, desc, date_posted. Network access stays in the caller.
"""
import email.utils
import html
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET


def rss_date(value):
    if not isinstance(value, str) or not value.strip():
        return None
    if re.match(r"\d{4}-\d{2}-\d{2}", value):
        return value[:10]
    try:
        return email.utils.parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError, IndexError):
        return None


def _text(node):
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def _local(tag):
    return tag.rsplit("}", 1)[-1] if tag else ""


def _children(node, name):
    return [c for c in list(node) if _local(c.tag) == name]


def _child_text(node, name):
    for c in _children(node, name):
        if (c.text or "").strip():
            return c.text.strip()
        # Personio stores the description on a nested <value>.
        for inner in list(c):
            if (inner.text or "").strip():
                return inner.text.strip()
    return ""


def parse_smartrecruiters(payload, slug, token):
    data = json.loads(payload)
    out = []
    for j in data.get("content") or []:
        loc = j.get("location") or {}
        place = loc.get("fullLocation") or ", ".join(
            p for p in (loc.get("city"), loc.get("region"), loc.get("country")) if p)
        flag = loc.get("remote")
        if flag is True:
            place = f"{place} | remote=true"
        elif flag is False:
            place = f"{place} | remote=false"
        jid = str(j.get("id") or "")
        if not jid:
            continue
        ident = ((j.get("company") or {}).get("identifier")) or token
        out.append(dict(
            key=f"{slug}:{jid}", title=j.get("name"), location=place,
            url=f"https://jobs.smartrecruiters.com/{ident}/{jid}",
            salary=None, desc="", date_posted=rss_date(j.get("releasedDate")),
        ))
    return out, int(data.get("totalFound") or len(out))


def parse_personio(payload, slug, token, tld="de"):
    root = ET.fromstring(payload)
    out = []
    for pos in root.iter():
        if _local(pos.tag) != "position":
            continue
        jid = _child_text(pos, "id")
        if not jid:
            continue
        parts = []
        for block in pos.iter():
            if _local(block.tag) == "jobDescription":
                parts.append(_child_text(block, "value") or _text(block))
        office = _child_text(pos, "office")
        schedule = _child_text(pos, "schedule")
        location = " | ".join(p for p in (office, schedule) if p)
        out.append(dict(
            key=f"{slug}:{jid}", title=_child_text(pos, "name"), location=location,
            url=f"https://{token}.jobs.personio.{tld}/job/{jid}",
            salary=None, desc="\n".join(parts), date_posted=rss_date(_child_text(pos, "createdAt")),
        ))
    return out


def _feed_items(payload):
    root = ET.fromstring(payload)
    items = []
    for node in root.iter():
        if _local(node.tag) not in ("item", "entry"):
            continue
        title = link = desc = published = ""
        for c in list(node):
            name = _local(c.tag)
            if name == "title":
                title = _text(c)
            elif name == "link":
                link = (c.get("href") or _text(c) or "").strip()
            elif name in ("description", "summary", "content"):
                if not desc:
                    desc = _text(c)
            elif name in ("pubDate", "published", "updated", "date"):
                if not published:
                    published = _text(c)
        if link:
            items.append((title, link, desc, published))
    return items


def parse_teamtailor(payload, slug):
    out = []
    for title, link, desc, published in _feed_items(payload):
        m = re.search(r"/jobs/(\d+)", link)
        if not m:
            continue
        out.append(dict(
            key=f"{slug}:{m.group(1)}", title=title, location=None, url=link.split("?")[0],
            salary=None, desc=desc, date_posted=rss_date(published),
        ))
    return out


def parse_jazzhr(payload, slug):
    """JazzHR public RSS. Same item shape as other RSS feeds; the id is in the URL."""
    out = []
    for title, link, desc, published in _feed_items(payload):
        m = re.search(r"/apply/([^/]+)/([^/?#]+)", link)
        if not m:
            continue
        out.append(dict(
            key=f"{slug}:{m.group(1)}", title=title, location=None, url=link.split("?")[0],
            salary=None, desc=desc, date_posted=rss_date(published),
        ))
    return out


def _bamboo_place(j):
    loc = j.get("location") if isinstance(j.get("location"), dict) else {}
    ats = j.get("atsLocation") if isinstance(j.get("atsLocation"), dict) else {}
    city = loc.get("city") or ats.get("city")
    region = loc.get("state") or ats.get("state") or ats.get("country") or loc.get("country")
    place = ", ".join(p for p in (city, region) if p)
    label = j.get("locationType") or j.get("employmentStatusLabel")
    if isinstance(label, str) and label and label not in place:
        place = " | ".join(p for p in (place, label) if p)
    if j.get("isRemote") is True:
        place = f"{place} | remote=true"
    return place or None


def parse_bamboohr(payload, slug, token):
    data = json.loads(payload)
    rows = data.get("result")
    if rows is None and isinstance(data, list):
        rows = data
    out = []
    for j in rows or []:
        jid = str(j.get("id") or "")
        if not jid:
            continue
        out.append(dict(
            key=f"{slug}:{jid}", title=j.get("jobOpeningName") or j.get("title"),
            location=_bamboo_place(j),
            url=f"https://{token}.bamboohr.com/careers/{jid}",
            salary=None, desc="", date_posted=None,
        ))
    return out


def _breezy_rows(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("positions", "jobs", "result"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def parse_breezy(payload, slug, token):
    out = []
    for j in _breezy_rows(json.loads(payload)):
        jid = str(j.get("id") or "")
        if not jid:
            continue
        loc = j.get("location") or {}
        if isinstance(loc, dict):
            country = loc.get("country")
            country = country.get("name") if isinstance(country, dict) else country
            place = loc.get("name") or ""
            if country and country not in place:
                place = ", ".join(p for p in (place, country) if p)
            if loc.get("is_remote") is True:
                place = f"{place} | remote=true"
        else:
            place = str(loc)
        url = j.get("url") or f"https://{token}.breezy.hr/p/{j.get('friendly_id') or jid}"
        out.append(dict(
            key=f"{slug}:{jid}", title=j.get("name") or j.get("title"), location=place,
            url=url, salary=None, desc=j.get("description") or "",
            date_posted=rss_date(j.get("published_date") or j.get("publishedDate")),
        ))
    return out


def _pinpoint_rows(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "postings", "jobs"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def parse_pinpoint(payload, slug):
    out = []
    for j in _pinpoint_rows(json.loads(payload)):
        jid = str(j.get("id") or "")
        url = j.get("url") or j.get("application_url") or ""
        if not jid or "/postings/" not in url:
            continue
        loc = j.get("location") or {}
        place = loc.get("name") if isinstance(loc, dict) else (loc or None)
        out.append(dict(
            key=f"{slug}:{jid}", title=j.get("title") or j.get("name"), location=place,
            url=url.split("?")[0], salary=None, desc=j.get("description") or "",
            date_posted=rss_date(j.get("published_at") or j.get("publishedAt")),
        ))
    return out


def parse_rippling(payload, slug, token):
    """Rippling public board JSON. The list is either a bare array or under items/jobs."""
    data = json.loads(payload)
    rows = data if isinstance(data, list) else []
    if isinstance(data, dict):
        for key in ("items", "jobs", "jobPosts", "results"):
            if isinstance(data.get(key), list):
                rows = data[key]
                break
    out = []
    for j in rows:
        jid = str(j.get("id") or j.get("uuid") or "")
        url = j.get("url") or j.get("jobUrl") or j.get("absoluteUrl") or ""
        if not url and jid:
            url = f"https://ats.rippling.com/{token}/jobs/{jid}"
        if not jid or "/jobs/" not in url:
            continue
        loc = j.get("locations") or j.get("location") or j.get("workLocation")
        if isinstance(loc, list):
            loc = ", ".join(str(x.get("name") or x.get("city") or x) if isinstance(x, dict) else str(x) for x in loc)
        elif isinstance(loc, dict):
            loc = loc.get("name") or loc.get("label") or loc.get("city") or loc.get("country")
        workplace = str(j.get("workplaceType") or j.get("locationType") or "")
        place = " | ".join(p for p in (loc, workplace) if p) or None
        out.append(dict(
            key=f"{slug}:{jid}", title=j.get("name") or j.get("title"), location=place,
            url=url.split("?")[0], salary=None, desc=j.get("description") or "",
            date_posted=rss_date(j.get("publishedAt") or j.get("createdAt") or j.get("postedDate")),
        ))
    return out


def smartrecruiters_jobs(src, get, pause):
    token = src["token"]
    base = src["endpoint"]
    offset = 0
    kept = []
    while offset < 500:
        sep = "&" if "?" in base else "?"
        batch, total = parse_smartrecruiters(get(f"{base}{sep}limit=100&offset={offset}"), src["slug"], token)
        kept.extend(batch)
        offset += len(batch)
        if not batch or offset >= total:
            break
        pause()
    return kept


def _personio_tld(endpoint):
    return "com" if ".personio.com" in (endpoint or "") else "de"


def _plain(value):
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# Dover's workplace_type can say HYBRID while the posting itself allows remote
# ("In-office or Remote", "a remote, distributed, and async-friendly work environment").
# "distributed systems" is not a remote-work statement.
_REMOTE_ALLOWED_RX = re.compile(
    r"(?:"
    r"in[-\s]?office\s+or\s+remote"
    r"|remote\s+or\s+in[-\s]?office"
    r"|remote\s+work"
    r"|work(?:ing)?\s+remotely"
    r"|fully\s+remote"
    r"|100%\s*remote"
    r"|remote[-\s]friendly"
    r"|a\s+remote,\s+(?:distributed|flexible|async)"
    r")",
    re.I,
)
_DOVER_DETAIL = "https://app.dover.com/api/v1/inbound/application-portal-job/{}"


def description_allows_remote(description):
    """True when the posting text says remote work is allowed."""
    return _REMOTE_ALLOWED_RX.search(_plain(description)) is not None


def dover_job_url(client, job_id):
    """Public posting URL used by the Dover careers page.

    On jobs.dover.com the route is /:clientName/:jobId. The same posting on
    app.dover.com is /apply/:clientName/:jobId. The careers page links to the
    jobs host, without the referrer query string.
    """
    segment = urllib.parse.quote(str(client).strip(), safe="")
    return f"https://jobs.dover.com/{segment}/{job_id}"


def _dover_salary(comp):
    """Salary text only when Dover marks the range as shared. Bounds alone are not public."""
    if not isinstance(comp, dict) or comp.get("open_to_sharing_comp") is not True:
        return None
    lo, hi = comp.get("lower_bound"), comp.get("upper_bound")
    if lo is None and hi is None:
        return None

    def amount(value):
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    if lo is not None and hi is not None:
        span = f"{amount(lo)}-{amount(hi)}"
    elif lo is not None:
        span = f"{amount(lo)}+"
    else:
        span = f"up to {amount(hi)}"
    return " ".join(p for p in (span, comp.get("currency_code") or "", comp.get("salary_range_type") or "") if p)


def _dover_places(locations):
    places = []
    for loc in locations or []:
        if not isinstance(loc, dict):
            continue
        name = loc.get("name")
        option = loc.get("location_option")
        if not name and isinstance(option, dict):
            name = option.get("display_name")
        if isinstance(name, str):
            name = name.strip()
        if name and name not in places:
            places.append(name)
    return places


def parse_dover_detail(detail, slug, client, job_id=None):
    """One Dover application-portal job. Remote eligibility follows the description too."""
    jid = str(job_id or detail.get("id") or "").strip()
    workplace = str(detail.get("workplace_type") or "").strip().upper()
    description = detail.get("user_provided_description") or ""
    if workplace == "REMOTE" or description_allows_remote(description):
        flag = "remote=true"
    elif workplace == "HYBRID":
        flag = "hybrid"
    elif workplace in {"ONSITE", "ON_SITE", "IN_OFFICE"}:
        flag = "onsite"
    else:
        flag = ""
    places = ", ".join(_dover_places(detail.get("locations")))
    location = " | ".join(p for p in (places, flag) if p) or None
    return dict(
        key=f"{slug}:{jid}", title=detail.get("title"), location=location,
        url=dover_job_url(client, jid), salary=_dover_salary(detail.get("compensation")),
        desc=description, date_posted=rss_date(detail.get("created")),
    )


def fetch_dover(src, get, pause):
    """List a Dover careers page, then one public detail request per published job.

    The list call is the first request (the caller already waited). Each detail
    request waits via pause(), including the first, so the source stays at about
    one request per second.
    """
    slug = src["slug"]
    client = (src.get("token") or "").strip()
    endpoint = src["endpoint"]
    page = endpoint
    out = []
    seen = set()
    pages = 0
    while page and pages < 20 and len(seen) < 500:
        if pages:
            pause()
        pages += 1
        data = json.loads(get(page))
        if not isinstance(data, dict):
            break
        for row in data.get("results") or []:
            if not isinstance(row, dict):
                continue
            if row.get("is_published") is False or row.get("is_sample") is True:
                continue
            jid = str(row.get("id") or "").strip()
            if not jid or jid in seen:
                continue
            seen.add(jid)
            pause()
            detail_url = _DOVER_DETAIL.format(urllib.parse.quote(jid, safe=""))
            detail = json.loads(get(detail_url))
            if not isinstance(detail, dict):
                continue
            if detail.get("active") is False or detail.get("is_private") is True:
                continue
            name = client or str(detail.get("client_name") or "").strip()
            if not name:
                continue
            out.append(parse_dover_detail(detail, slug, name, jid))
        nxt = data.get("next")
        if not isinstance(nxt, str) or not nxt:
            break
        page = nxt if nxt.startswith("http") else urllib.parse.urljoin(endpoint, nxt)
    return out


# --- Workday career sites (myworkdayjobs.com CXS JSON endpoints) ---

_WORKDAY_ID_RX = re.compile(r"_(R\d+)$")


def workday_site_root(endpoint):
    """Human careers-site root for a CXS listing endpoint.

    https://hitachi.wd1.myworkdayjobs.com/wday/cxs/hitachi/hitachi/jobs
    -> https://hitachi.wd1.myworkdayjobs.com/hitachi
    """
    m = re.match(r"(https?://[^/]+)/wday/cxs/[^/]+/([^/]+)", endpoint or "")
    return f"{m.group(1)}/{m.group(2)}" if m else None


def workday_row_id(row):
    """Requisition id (R0149848) from a listing row: bulletFields first, path tail second."""
    bullets = row.get("bulletFields") or []
    if bullets and isinstance(bullets[0], str) and re.fullmatch(r"R\d+", bullets[0].strip()):
        return bullets[0].strip()
    tail = (row.get("externalPath") or "").rsplit("/", 1)[-1]
    m = _WORKDAY_ID_RX.search(tail)
    return m.group(1) if m else None


def parse_workday_posting(info, slug, url, job_id):
    """One Workday jobPostingInfo record. remoteType ("Onsite"/"Hybrid"/"Remote")
    becomes the same location flag the other feeds use."""
    places = []
    if isinstance(info.get("location"), str) and info["location"]:
        places.append(info["location"])
    for loc in info.get("additionalLocations") or []:
        if isinstance(loc, dict) and isinstance(loc.get("descriptor"), str) and loc["descriptor"] not in places:
            places.append(loc["descriptor"])
    workplace = str(info.get("remoteType") or "").strip()
    location = " | ".join(p for p in (", ".join(places), workplace) if p) or None
    return dict(
        key=f"{slug}:{job_id}", title=info.get("title"), location=location,
        url=(info.get("externalUrl") or url or "").split("?")[0] or None, salary=None,
        desc=info.get("jobDescription") or "", date_posted=rss_date(info.get("startDate")),
    )


def workday_facets(src):
    """appliedFacets payload from a source's `facets` map: {"locationCountry": "<id>"}."""
    facets = src.get("facets")
    if not isinstance(facets, dict):
        return {}
    out = {}
    for key, value in facets.items():
        if isinstance(value, str) and value:
            out[key] = [value]
        elif isinstance(value, list):
            out[key] = [v for v in value if isinstance(v, str) and v]
    return out


def workday_jobs(src, get, pause):
    """List a Workday CXS feed (one POST per page), then one public detail GET per posting.

    A source may set `facets` (e.g. {"locationCountry": "<Workday country id>"}, taken
    from the careers-site URL) and/or `search` (free text) to scope a large board;
    without them the whole site is listed. The first page is the first request (the
    caller already waited); every further page and every detail request waits via pause().
    """
    slug = src["slug"]
    endpoint = src["endpoint"]
    base = endpoint.rsplit("/", 1)[0]
    site_root = workday_site_root(endpoint)
    applied = workday_facets(src)
    search = str(src.get("search") or "").strip()
    out, seen = [], set()
    offset, pages = 0, 0
    while pages < 25 and len(seen) < 500:
        payload = json.dumps({"appliedFacets": applied, "limit": 20, "offset": offset, "searchText": search})
        data = json.loads(get(endpoint, data=payload))
        rows = data.get("jobPostings") or [] if isinstance(data, dict) else []
        pages += 1
        for row in rows:
            if not isinstance(row, dict):
                continue
            jid = workday_row_id(row)
            path = row.get("externalPath")
            if not jid or jid in seen or not isinstance(path, str) or not path.startswith("/"):
                continue
            seen.add(jid)
            pause()  # one request per second: the listing page already used the slot
            detail = json.loads(get(base + path))
            info = detail.get("jobPostingInfo") if isinstance(detail, dict) else None
            if not isinstance(info, dict):
                continue
            fallback = site_root + path if site_root else None
            out.append(parse_workday_posting(info, slug, fallback, jid))
        if not rows or not data.get("total") or offset + len(rows) >= int(data["total"]):
            break
        offset += len(rows)
        pause()
    return out


def fetch_jobs(src, get, pause):
    """Return a list of raw jobs, or None when this module does not handle the ATS.

    `get(url)` performs one HTTP GET; Workday also passes `data=<json string>` for
    its POST listing. `pause()` waits before an extra page. The first request is
    not paused here; the caller already spaces sources out.
    """
    ats = src.get("ats")
    slug = src["slug"]
    token = src.get("token") or ""
    if ats == "smartrecruiters":
        return smartrecruiters_jobs(src, get, pause)
    if ats == "personio":
        return parse_personio(get(src["endpoint"]), slug, token, _personio_tld(src.get("endpoint")))
    if ats == "teamtailor":
        return parse_teamtailor(get(src["endpoint"]), slug)
    if ats == "jazzhr":
        return parse_jazzhr(get(src["endpoint"]), slug)
    if ats == "bamboohr":
        return parse_bamboohr(get(src["endpoint"], accept="application/json"), slug, token)
    if ats == "breezy":
        return parse_breezy(get(src["endpoint"]), slug, token)
    if ats == "pinpoint":
        return parse_pinpoint(get(src["endpoint"]), slug)
    if ats == "rippling":
        return parse_rippling(get(src["endpoint"]), slug, token)
    if ats == "dover":
        return fetch_dover(src, get, pause)
    if ats == "workday":
        return workday_jobs(src, get, pause)
    return None
