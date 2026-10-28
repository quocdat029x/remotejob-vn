#!/usr/bin/env python3
"""Weekly check of job URLs that no public ATS feed can refresh.

Polite on purpose: one request per second, HEAD first, GET only when HEAD is
missing or a 404/410 needs confirming, 25s timeout, no retries, identifying
User-Agent. A job is marked removed (existing removed/removed_on fields) when
the URL returns 404/410 or redirects to a generic careers/listing page.
Network errors, 401/403/429 and other 4xx/5xx leave the job untouched.

A confirmed live posting updates last_checked, so it does not go stale only
because the careers site has no API.

Usage:
  python3 scripts/linkcheck_jobs.py --dry-run --limit 3
  python3 scripts/linkcheck_jobs.py --delay 1.0
"""
import argparse, datetime, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import data_health
import jobfilter as jf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))
UA = {"User-Agent": f"RemoteJobVN-JobRefresh/1.0 (+{CFG['REPO_URL']})", "Accept": "text/html,application/xhtml+xml,*/*;q=0.5"}
LISTING_TAILS = {
    "careers", "career", "jobs", "job", "openings", "opening", "join", "join-us",
    "tuyen-dung", "opportunities", "positions", "vacancies", "work-with-us",
    "careers.html", "jobs.html", "tuyen-dung.html",
}


def _norm(url):
    parts = urllib.parse.urlsplit(url or "")
    host = (parts.hostname or "").lower().removeprefix("www.")
    path = urllib.parse.unquote(parts.path or "").rstrip("/").lower()
    return host, path


def is_generic_listing(final, original, careers_url, website):
    """True when `final` is a different URL and is a careers index, homepage, or board root.

    The same path (trailing slash and query ignored) is not a redirect away from the posting.
    """
    fh, fp = _norm(final)
    oh, op = _norm(original)
    if not fh or (fh, fp) == (oh, op):
        return False
    for ref in (careers_url, website):
        rh, rp = _norm(ref)
        if rh and (fh, fp) == (rh, rp):
            return True
    if fh.endswith("itviec.com") and "/it-jobs/" not in fp:
        return True
    if fh.endswith("linkedin.com") and "/jobs/view/" not in fp:
        return True
    if fh.endswith("himalayas.app") and not re.search(r"/jobs/[^/]+", fp):
        return True
    parts = [p for p in fp.split("/") if p]
    if not parts:
        return True
    if parts[-1] in LISTING_TAILS and len(parts) <= 3:
        return True
    return False


def classify(status, final, original, careers_url, website, error=None):
    """Return removed, alive, blocked, or error. error and blocked do not change the job."""
    if error or status is None:
        return "error"
    if status in (404, 410):
        return "removed"
    if status in (401, 403, 429):
        return "blocked"
    if status >= 400:
        return "error"
    if is_generic_listing(final, original, careers_url, website):
        return "removed"
    if 200 <= status < 400:
        return "alive"
    return "error"


def request(url, method):
    req = urllib.request.Request(url, headers=dict(UA), method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            if method == "GET":
                response.read(2048)
            return {"status": getattr(response, "status", 200), "final": response.geturl(), "error": None}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "final": getattr(exc, "url", None) or url, "error": None}
    except Exception as exc:  # noqa: BLE001 - one attempt, then the job is left as it was
        return {"status": None, "final": url, "error": f"{type(exc).__name__}: {exc}"[:180]}


def probe(url, delay):
    """HEAD, then at most one GET. Returns the response that decides the job."""
    head = request(url, "HEAD")
    if head["error"] or head["status"] not in (400, 404, 405, 410, 501):
        return head
    time.sleep(delay)
    got = request(url, "GET")
    if got["error"] or got["status"] is None:
        # A HEAD 404 that we could not confirm is not evidence the posting is gone.
        return {"status": None, "final": head["final"], "error": got["error"] or "GET failed"}
    return got


def source_is_api(src):
    return src.get("method") == "api" or src.get("ats") in jf.API_ATS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    ap.add_argument("--limit", type=int, default=0, help="check at most this many jobs (0 = all)")
    ap.add_argument("--only", help="comma-separated company slugs")
    args = ap.parse_args()
    delay = max(1.0, args.delay)
    today = args.today
    data = os.path.join(ROOT, "data")

    def load(name):
        with open(os.path.join(data, name), encoding="utf-8") as fh:
            return json.load(fh)

    companies = load("companies.json")
    sources = load("sources.json")
    jobs = load("jobs.json")
    co_by = {c["slug"]: c for c in companies}
    src_by = {s["slug"]: s for s in sources}
    only = set(args.only.split(",")) if args.only else None
    html_slugs = {s["slug"] for s in sources if not source_is_api(s)}
    todo = [j for j in jobs if j.get("status", "open") == "open" and j["company_slug"] in html_slugs
            and (not only or j["company_slug"] in only) and str(j.get("url", "")).startswith("http")]
    todo.sort(key=lambda j: (j["company_slug"], j["key"]))
    if args.limit:
        todo = todo[: args.limit]

    counts = {"alive": 0, "removed": 0, "error": 0, "blocked": 0}
    touched = set()
    blocked_notes = []
    for i, job in enumerate(todo):
        if i:
            time.sleep(delay)
        company = co_by.get(job["company_slug"], {})
        try:
            result = probe(job["url"], delay)
        except Exception as exc:  # noqa: BLE001
            result = {"status": None, "final": job["url"], "error": type(exc).__name__}
        kind = classify(result["status"], result["final"], job["url"], company.get("careers_url"), company.get("website"), result.get("error"))
        counts[kind] += 1
        if kind == "removed":
            job["status"] = "removed"
            job["removed_on"] = today
            touched.add(job["company_slug"])
            print(f"removed {job['company_slug']} {result['status']} {job['url']} -> {result['final']}")
        elif kind == "alive":
            job["last_checked"] = today
            touched.add(job["company_slug"])
            print(f"alive   {job['company_slug']} {result['status']} {job['url']}")
        else:
            print(f"{kind:<7} {job['company_slug']} {result['status']} {result.get('error') or ''} {job['url']}")
            if kind == "blocked":
                blocked_notes.append(f"{job['company_slug']} {result['status']} {urllib.parse.urlsplit(job['url']).hostname}")

    for slug in touched:
        src = src_by.get(slug)
        if src:
            src["last_checked"] = today
        if slug in co_by:
            co_by[slug]["last_checked"] = max(co_by[slug].get("last_checked") or today, today)

    cut = (datetime.date.fromisoformat(today) - datetime.timedelta(days=CFG["REMOVED_PAGE_KEEP_DAYS"])).isoformat()
    before = len(jobs)
    jobs = [j for j in jobs if not (j.get("status") == "removed" and j.get("removed_on", today) < cut)]
    jobs.sort(key=lambda j: (j["company_slug"], j["title"].lower()))
    print(
        f"link-check jobs={len(todo)} alive={counts['alive']} removed={counts['removed']} "
        f"blocked={counts['blocked']} errors={counts['error']} purged={before - len(jobs)}"
    )
    if blocked_notes:
        print("blocked-hosts " + ", ".join(sorted(set(blocked_notes))))
    if args.dry_run:
        print("dry run: nothing written")
        return
    updates = {
        "last_link_check": today,
        "last_link_checked": len(todo),
        "last_link_alive": counts["alive"],
        "last_link_removed": counts["removed"],
        "last_link_blocked": counts["blocked"],
        "last_link_errors": counts["error"],
    }
    data_health.merge_status(ROOT, updates)

    def dump(name, obj):
        with open(os.path.join(data, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1)
            fh.write("\n")

    dump("jobs.json", jobs)
    dump("sources.json", sources)
    dump("companies.json", companies)


if __name__ == "__main__":
    main()
