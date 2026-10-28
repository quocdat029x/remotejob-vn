"""Parsers for public, unauthenticated ATS feeds.

Each parser takes the response body (and the source record) and returns the same
raw job dicts refresh_jobs.py already understands: key, title, location, url,
salary, desc, date_posted. Network access stays in the caller.
"""
import email.utils
import json
import re
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


def fetch_jobs(src, get, pause):
    """Return a list of raw jobs, or None when this module does not handle the ATS.

    `get(url)` performs one HTTP GET. `pause()` waits before an extra page.
    The first request is not paused here; the caller already spaces sources out.
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
    return None
