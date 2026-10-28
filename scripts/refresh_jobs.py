#!/usr/bin/env python3
"""Refresh data/jobs.json from public ATS APIs, politely.

Adapted from the original careers monitor (fetch.py):
- Only public, unauthenticated JSON endpoints (Greenhouse, Lever, Ashby, Workable, Recruitee) by default.
  HTML careers pages are skipped unless --include-html is given (link scraping is noisy; see docs/JOB_FILTER_RULES.md).
- At most ~1 request per second (--delay), one request per source, no retries, 25 s timeout,
  identifying User-Agent.
- Every link goes through the same filter rules as the seed import (scripts/jobfilter.py).
- Jobs no longer returned by a source that fetched successfully are marked status="removed"
  with removed_on=<today>; the site drops them from lists/sitemap and serves a noindex page for
  REMOVED_PAGE_KEEP_DAYS, after which they are purged here.
- Jobs from a source that failed are left untouched (their last_checked ages; after JOB_STALE_DAYS
  the site hides them).
- Updates last_checked on jobs, on data/sources.json entries, and on the company record
  (company.last_checked = last date any public source for the company was checked successfully).

Usage:
  python3 scripts/refresh_jobs.py                   # all API sources, writes data/
  python3 scripts/refresh_jobs.py --only a,b --dry-run   # fetch a few sources, print a summary, write nothing
"""
import argparse, datetime, hashlib, html as H, json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import jobfilter as jf
import policy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))
UA = {"User-Agent": f"RemoteJobVN-JobRefresh/1.0 (+{CFG['REPO_URL']})", "Accept": "application/json,text/html;q=0.8,*/*;q=0.5"}
API_ATS = {"greenhouse", "lever", "ashby", "workable", "recruitee"}
JOBRX = re.compile(r"/(jobs?|careers?|positions?|openings?|vacanc|tuyen-dung|it-jobs|o/|apply)", re.I)


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def strip(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", H.unescape(s or ""))).strip()


def ms_to_date(ms):
    try:
        return datetime.datetime.fromtimestamp(int(ms) / 1000, datetime.timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        return None


def iso_date(s):
    return s[:10] if isinstance(s, str) and re.match(r"\d{4}-\d{2}-\d{2}", s) else None


def fetch_source(src):
    """Return a list of raw job dicts: key, title, location, url, salary, desc, date_posted."""
    slug, ats, ep = src["slug"], src["ats"], src["endpoint"]
    out = []
    if ats == "greenhouse":
        u = ep if "content=" in ep else ep + ("&" if "?" in ep else "?") + "content=true"
        for j in json.loads(get(u)).get("jobs", []):
            out.append(dict(key=f"{slug}:{j['id']}", title=j.get("title"), location=(j.get("location") or {}).get("name"),
                            url=j.get("absolute_url"), salary=None, desc=strip(j.get("content", "")),
                            date_posted=iso_date(j.get("first_published") or j.get("updated_at"))))
    elif ats == "lever":
        for j in json.loads(get(ep)):
            cat = j.get("categories", {})
            sal = j.get("salaryRange")
            sal = f"{sal.get('min')}-{sal.get('max')} {sal.get('currency')}/{sal.get('interval')}" if sal else None
            out.append(dict(key=f"{slug}:{j['id']}", title=j.get("text"),
                            location=f"{cat.get('location')} | {j.get('workplaceType')} | {','.join(cat.get('allLocations') or [])}",
                            url=j.get("hostedUrl"), salary=sal, desc=j.get("descriptionPlain") or "", date_posted=ms_to_date(j.get("createdAt"))))
    elif ats == "ashby":
        u = ep + ("&" if "?" in ep else "?") + "includeCompensation=true"
        for j in json.loads(get(u)).get("jobs", []):
            comp = (j.get("compensation") or {}).get("compensationTierSummary")
            locs = [j.get("location")] + [s.get("location") for s in j.get("secondaryLocations") or []]
            out.append(dict(key=f"{slug}:{j['id']}", title=j.get("title"),
                            location=f"{' / '.join(filter(None, locs))} | remote={j.get('isRemote')} {j.get('workplaceType')}",
                            url=j.get("jobUrl"), salary=comp, desc=j.get("descriptionPlain") or "", date_posted=iso_date(j.get("publishedAt"))))
    elif ats == "workable":
        for j in json.loads(get(ep)).get("jobs", []):
            jid = j.get("shortcode") or j.get("id") or hashlib.md5(j.get("url", "").encode()).hexdigest()[:12]
            loc = ", ".join(filter(None, [j.get("city"), j.get("country")])) + f" | telecommuting={j.get('telecommuting')}"
            out.append(dict(key=f"{slug}:{jid}", title=j.get("title"), location=loc, url=j.get("url") or j.get("shortlink"),
                            salary=None, desc=strip(j.get("description", "")), date_posted=iso_date(j.get("published_on") or j.get("created_at"))))
    elif ats == "recruitee":
        for j in json.loads(get(ep)).get("offers", []):
            out.append(dict(key=f"{slug}:{j['id']}", title=j.get("title"), location=f"{j.get('location')} | remote={j.get('remote')}",
                            url=j.get("careers_url"), salary=None, desc=strip(j.get("description", "")),
                            date_posted=iso_date(j.get("published_at") or j.get("created_at"))))
    else:  # HTML: collect job-like links (only with --include-html)
        page = get(ep)
        for m in re.finditer(r'<a\b[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', page, re.S | re.I):
            href = urllib.parse.urljoin(ep, H.unescape(m.group(1)))
            text = strip(m.group(2))
            p = urllib.parse.urlparse(href)
            if not p.scheme.startswith("http") or not JOBRX.search(p.path) or len(text) > 150:
                continue
            clean = href.split("?")[0].rstrip("/")
            out.append(dict(key=f"{slug}:{hashlib.sha1(clean.encode()).hexdigest()[:12]}", title=text, location=None,
                            url=clean, salary=None, desc="", date_posted=None))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated company slugs")
    ap.add_argument("--dry-run", action="store_true", help="fetch and report, do not write data/")
    ap.add_argument("--include-html", action="store_true", help="also scrape HTML careers pages (noisy)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests (min 1.0)")
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    a = ap.parse_args()
    delay = max(1.0, a.delay)
    today = a.today

    def path(n):
        return os.path.join(ROOT, "data", n)

    companies = json.load(open(path("companies.json"), encoding="utf-8"))
    co_by = {c["slug"]: c for c in companies}
    sources = json.load(open(path("sources.json"), encoding="utf-8"))
    jobs = json.load(open(path("jobs.json"), encoding="utf-8"))
    only = set(a.only.split(",")) if a.only else None
    todo = [s for s in sources if (not only or s["slug"] in only) and s["slug"] in co_by and not policy.exclusion_reason(co_by[s["slug"]])
            and (s["ats"] in API_ATS or a.include_html)]

    by_key = {j["key"]: j for j in jobs}
    report = []
    for i, s in enumerate(todo):
        if i:
            time.sleep(delay)
        try:
            raw = fetch_source(s)
        except Exception as ex:  # noqa: BLE001 - report and continue; no retries by design
            s["status"] = "error"
            report.append(f"ERROR {s['slug']} {s['ats']}: {type(ex).__name__} {str(ex)[:120]}")
            continue
        kept, seen_url, seen_title, drops = [], set(), set(), 0
        for r in raw:
            ok, _why = jf.is_job(s["ats"], r.get("url"), r.get("title"))
            if not ok or r["url"] in seen_url:
                drops += 1
                continue
            title = jf.clean_title(r.get("title"), r["url"])
            tk = (title.lower(), (r.get("location") or "").lower())
            if tk in seen_title:
                drops += 1
                continue
            seen_url.add(r["url"]); seen_title.add(tk)
            prev = by_key.get(r["key"], {})
            kept.append({
                "key": r["key"], "company_slug": s["slug"], "title": title, "location": jf.tidy_location(r.get("location")),
                "url": r["url"], "salary": r.get("salary") or None, "ats": s["ats"], "roles": jf.job_roles(title),
                "region": jf.job_region(title, r.get("location")), "remote": jf.job_remote(title, r.get("location")),
                "description": jf.excerpt(r.get("desc")), "date_posted": r.get("date_posted") or prev.get("date_posted"),
                "status": "open", "first_seen": prev.get("first_seen") or today, "last_checked": today,
            })
        new_keys = {k["key"] for k in kept}
        removed = 0
        for j in jobs:
            if j["company_slug"] == s["slug"] and j["key"] not in new_keys and j.get("status", "open") == "open":
                j["status"] = "removed"; j["removed_on"] = today; removed += 1
        jobs = [j for j in jobs if j["key"] not in new_keys] + kept
        by_key.update({k["key"]: k for k in kept})
        s["status"] = "ok"; s["last_checked"] = today
        co_by[s["slug"]]["last_checked"] = max(co_by[s["slug"]]["last_checked"], today)
        dated = sum(1 for k in kept if k["date_posted"])
        report.append(f"ok    {s['slug']:<18} {s['ats']:<10} raw={len(raw):<4} kept={len(kept):<4} dropped={drops:<4} removed={removed:<4} with_date={dated}")
        if a.dry_run and kept:
            ex = kept[0]
            report.append(f"      e.g. {ex['title']!r} | {ex['location']} | posted {ex['date_posted']} | {ex['url']}")

    # purge removed jobs past the keep window
    cut = (datetime.date.fromisoformat(today) - datetime.timedelta(days=CFG["REMOVED_PAGE_KEEP_DAYS"])).isoformat()
    jobs = [j for j in jobs if not (j.get("status") == "removed" and j.get("removed_on", today) < cut)]
    jobs.sort(key=lambda j: (j["company_slug"], j["title"].lower()))

    print("\n".join(report))
    print(f"{len(todo)} source(s) fetched; jobs total {len(jobs)} ({sum(1 for j in jobs if j.get('status', 'open') == 'open')} open)")
    if a.dry_run:
        print("dry run: nothing written")
        return

    def dump(n, obj):
        with open(path(n), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1); fh.write("\n")
    dump("jobs.json", jobs); dump("sources.json", sources); dump("companies.json", companies)


if __name__ == "__main__":
    main()
