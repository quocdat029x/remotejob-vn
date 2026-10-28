#!/usr/bin/env python3
"""Tell IndexNow about job URLs that were added, edited, or removed.

One POST to https://api.indexnow.org/indexnow, no retries. The key file is
public on purpose (site/<key>.txt, copied to the site root at build time).
Skips the call when the key is missing or no job URL changed. An endpoint
error is printed and does not fail the refresh: the data commit already succeeded.

Compared fields are title, url, status, company, location and description.
A last_checked bump alone is not submitted.

Usage:
  python3 scripts/indexnow.py                 # HEAD~1 vs HEAD (after the data commit)
  python3 scripts/indexnow.py --old HEAD --new WORKTREE
"""
import argparse, json, os, sys, urllib.error, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import build

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))
ENDPOINT = "https://api.indexnow.org/indexnow"
UA = {"User-Agent": f"RemoteJobVN-IndexNow/1.0 (+{CFG['REPO_URL']})", "Content-Type": "application/json; charset=utf-8"}


def job_signature(job):
    return (
        job.get("title"), job.get("url"), job.get("status", "open"),
        job.get("company_slug"), job.get("location"), job.get("description"),
    )


def changed_job_urls(old_jobs, new_jobs, site):
    old_paths = build.assign_job_paths(old_jobs)
    new_paths = build.assign_job_paths(new_jobs)
    old = {j["key"]: j for j in old_jobs}
    new = {j["key"]: j for j in new_jobs}
    urls = set()
    for key in set(old) | set(new):
        before, after = old.get(key), new.get(key)
        same = before and after and job_signature(before) == job_signature(after) and old_paths.get(key) == new_paths.get(key)
        if same:
            continue
        for path in (old_paths.get(key), new_paths.get(key)):
            if not path:
                continue
            urls.add(site.rstrip("/") + path)
            urls.add(site.rstrip("/") + "/en" + path)
    return sorted(urls)


def load_jobs(rev):
    if rev == "WORKTREE":
        with open(os.path.join(ROOT, "data", "jobs.json"), encoding="utf-8") as fh:
            return json.load(fh)
    import subprocess
    raw = subprocess.check_output(["git", "show", f"{rev}:data/jobs.json"], cwd=ROOT)
    return json.loads(raw.decode())


def submit(urls, site, key):
    host = urllib.parse.urlparse(site).hostname
    if not host:
        print("IndexNow skipped: SITE_URL has no host")
        return 0
    # IndexNow accepts up to 10,000 URLs per request. Pause between batches.
    import time
    for start in range(0, len(urls), 10000):
        if start:
            time.sleep(1)
        batch = urls[start:start + 10000]
        body = json.dumps({
            "host": host,
            "key": key,
            "keyLocation": f"{site.rstrip('/')}/{key}.txt",
            "urlList": batch,
        }).encode()
        req = urllib.request.Request(ENDPOINT, data=body, headers=dict(UA), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                print(f"IndexNow {response.status} urls={len(batch)}")
        except urllib.error.HTTPError as exc:
            detail = exc.read(500).decode("utf-8", "replace")
            print(f"IndexNow HTTP {exc.code} (not retrying): {detail}")
        except Exception as exc:  # noqa: BLE001 - do not fail the refresh for a search-engine outage
            print(f"IndexNow error (not retrying): {type(exc).__name__}: {exc}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", default="HEAD~1")
    ap.add_argument("--new", default="HEAD")
    args = ap.parse_args()
    key = str(CFG.get("indexnow_key") or "").strip()
    if not key:
        print("IndexNow skipped: indexnow_key is empty")
        return
    try:
        old_jobs = load_jobs(args.old)
        new_jobs = load_jobs(args.new)
    except Exception as exc:  # noqa: BLE001
        print(f"IndexNow skipped: cannot read jobs ({type(exc).__name__}: {exc})")
        return
    urls = changed_job_urls(old_jobs, new_jobs, CFG["SITE_URL"])
    if not urls:
        print("IndexNow skipped: no job URL changes")
        return
    print(f"IndexNow submitting {len(urls)} url(s)")
    submit(urls, CFG["SITE_URL"], key)


if __name__ == "__main__":
    main()
