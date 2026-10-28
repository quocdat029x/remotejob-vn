#!/usr/bin/env python3
"""One-off seed import: copy ONLY public fields from a private research folder into data/.

Usage: python3 scripts/import_seed.py <source_dir>
Reads <source_dir>/companies.json, watchlist.json, watch-state/jobs_current.json. Nothing else.
Writes data/companies.json, data/sources.json, data/jobs.json, data/excluded.json, docs/import_report.md.
"""
import json, os, re, sys, datetime, collections
sys.path.insert(0, os.path.dirname(__file__))
import jobfilter as jf
import policy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_FIELDS = ["slug", "name", "website", "careers_url", "group", "hq", "remote_policy", "vn_hiring_mode",
                 "hires_roles", "timezone_note", "salary_public", "source_urls", "verified", "last_checked", "kind"]
SOURCE_FIELDS = ["slug", "ats", "token", "endpoint", "method"]
JOB_FIELDS_IN = ["key", "company_slug", "company", "title", "location", "url", "salary", "desc"]  # desc -> short excerpt only
GAMBLING_RX = policy.GAMBLING_RX


def main(src):
    companies = json.load(open(os.path.join(src, "companies.json"), encoding="utf-8"))
    watch = json.load(open(os.path.join(src, "watchlist.json"), encoding="utf-8"))
    jobs = json.load(open(os.path.join(src, "watch-state", "jobs_current.json"), encoding="utf-8"))
    jobs_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(src, "watch-state", "jobs_current.json")))
    jobs_checked = jobs_mtime.strftime("%Y-%m-%d")
    errors_path = os.path.join(src, "watch-state", "last_errors.txt")
    failed = set()
    if os.path.exists(errors_path):
        failed = {ln.split()[0] for ln in open(errors_path, encoding="utf-8") if ln.strip()}

    kept, excluded = [], []
    for c in companies:
        why = policy.exclusion_reason(c)
        if why:
            excluded.append({"slug": c["slug"], "name": c["name"], "reason": why}); continue
        row = {k: c.get(k) for k in PUBLIC_FIELDS if k != "kind"}
        if c.get("kind") in ("employer", "aggregator"):
            row["kind"] = c["kind"]
        kept.append(row)
    keep_slugs = {c["slug"] for c in kept}

    # A company whose OWN job titles are mostly gambling products is also excluded (none at import time).
    by_co = collections.defaultdict(list)
    for j in jobs:
        by_co[j["company_slug"]].append(j)
    for slug, js in by_co.items():
        hits = sum(1 for j in js if GAMBLING_RX.search(j.get("title") or ""))
        if slug in keep_slugs and js and hits / len(js) > 0.3:
            keep_slugs.discard(slug)
            excluded.append({"slug": slug, "name": js[0]["company"], "reason": "gambling-related job titles"})
    kept = [c for c in kept if c["slug"] in keep_slugs]

    sources = []
    for w in watch:
        if w["slug"] in keep_slugs:
            s = {k: w.get(k) for k in SOURCE_FIELDS}
            s["last_checked"] = jobs_checked
            s["status"] = "error" if w["slug"] in failed else "ok"
            sources.append(s)
    ats_of = {s["slug"]: s["ats"] for s in sources}

    stats = collections.Counter(); per_co_raw = collections.Counter(); per_co_kept = collections.Counter()
    seen_url, seen_title = set(), set(); out = []
    for j in jobs:
        slug = j["company_slug"]; per_co_raw[slug] += 1
        if slug not in keep_slugs:
            stats["excluded-company"] += 1; continue
        ats = ats_of.get(slug, "custom")
        ok, why = jf.is_job(ats, j.get("url"), j.get("title"))
        if not ok:
            stats[why] += 1; continue
        url = j["url"].split("#")[0]
        if url in seen_url:
            stats["duplicate-url"] += 1; continue
        title = jf.clean_title(j.get("title"), url)
        tkey = (slug, title.lower(), (j.get("location") or "").lower())
        if tkey in seen_title:
            stats["duplicate-title+location (repost)"] += 1; continue
        seen_url.add(url); seen_title.add(tkey)
        out.append({
            "key": j["key"], "company_slug": slug, "title": title, "location": jf.tidy_location(j.get("location")),
            "url": url, "salary": j.get("salary") or None, "ats": ats,
            "roles": jf.job_roles(title), "region": jf.job_region(title, j.get("location")),
            "remote": jf.job_remote(title, j.get("location")),
            "description": jf.excerpt(j.get("desc")), "date_posted": None,
            "status": "open", "first_seen": jobs_checked, "last_checked": jobs_checked,
        })
        per_co_kept[slug] += 1; stats["kept"] += 1

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    def dump(name, obj):
        with open(os.path.join(ROOT, "data", name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1); fh.write("\n")
    kept.sort(key=lambda c: (c["group"], c["name"].lower()))
    out.sort(key=lambda j: (j["company_slug"], j["title"].lower()))
    dump("companies.json", kept); dump("sources.json", sources); dump("jobs.json", out); dump("excluded.json", excluded)

    names = {c["slug"]: c["name"] for c in kept}
    lines = ["# Import report", "", f"Jobs snapshot date: {jobs_checked}", "",
             f"Companies in seed: {len(companies)}; kept: {len(kept)}; excluded: {len(excluded)}", ""]
    lines += [f"- excluded `{e['slug']}` ({e['name']}): {e['reason']}" for e in excluded] or ["- (no company in the seed matched an exclusion rule)"]
    lines += ["", f"Raw job links: {len(jobs)}; kept: {len(out)}", "", "## Drop reasons", ""]
    lines += [f"- {k}: {v}" for k, v in stats.most_common() if k != "kept"]
    lines += ["", "## Jobs per company (kept / raw)", "", "| company | source | kept | raw |", "|---|---|---:|---:|"]
    for slug in sorted(keep_slugs, key=lambda s: (-per_co_kept[s], s)):
        lines.append(f"| {names[slug]} | {ats_of.get(slug, '-')}{' (fetch error)' if slug in failed else ''} | {per_co_kept[slug]} | {per_co_raw[slug]} |")
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    open(os.path.join(ROOT, "docs", "import_report.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"companies kept={len(kept)} excluded={len(excluded)} jobs kept={len(out)}/{len(jobs)}")
    print(dict(stats))


if __name__ == "__main__":
    main(sys.argv[1])
