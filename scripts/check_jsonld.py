#!/usr/bin/env python3
"""Structural check of every JSON-LD block in dist/ (parses, required fields per schema.org type, Google JobPosting rules)."""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "dist")
RX = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
REQUIRED = {
    "WebSite": ["name", "url"],
    "Organization": ["name", "url"],
    "BreadcrumbList": ["itemListElement"],
    "ItemList": ["itemListElement"],
    "JobPosting": ["title", "description", "datePosted", "hiringOrganization", "jobLocationType", "applicantLocationRequirements", "url"],
    "FAQPage": ["mainEntity"],
}
counts, errors = {}, []
for fp in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
    html = open(fp, encoding="utf-8").read()
    noindex = 'name="robots" content="noindex' in html
    for raw in RX.findall(html):
        try:
            d = json.loads(raw)
        except ValueError as ex:
            errors.append(f"{fp}: invalid JSON ({ex})")
            continue
        t = d.get("@type")
        counts[t] = counts.get(t, 0) + 1
        if d.get("@context") != "https://schema.org":
            errors.append(f"{fp}: {t} missing @context")
        for k in REQUIRED.get(t, []):
            if not d.get(k):
                errors.append(f"{fp}: {t} missing {k}")
        if t == "JobPosting":
            if noindex:
                errors.append(f"{fp}: JobPosting on a noindex page")
            if d.get("jobLocationType") != "TELECOMMUTE":
                errors.append(f"{fp}: jobLocationType must be TELECOMMUTE")
            if not re.match(r"\d{4}-\d{2}-\d{2}", d.get("datePosted", "")):
                errors.append(f"{fp}: bad datePosted")
            org = d.get("hiringOrganization") or {}
            if org.get("@type") != "Organization" or not org.get("name"):
                errors.append(f"{fp}: hiringOrganization must be an Organization with a name")
            alr = d.get("applicantLocationRequirements") or {}
            if alr.get("@type") != "Country" or not alr.get("name"):
                errors.append(f"{fp}: applicantLocationRequirements must be a Country")
            if d.get("validThrough") and not re.match(r"^\d{4}-\d{2}-\d{2}", d["validThrough"]):
                errors.append(f"{fp}: bad validThrough")
        if t == "FAQPage":
            ents = d.get("mainEntity")
            if not isinstance(ents, list) or not ents:
                errors.append(f"{fp}: FAQPage needs mainEntity")
            else:
                for q in ents:
                    ans = q.get("acceptedAnswer") or {}
                    if q.get("@type") != "Question" or not str(q.get("name") or "").strip():
                        errors.append(f"{fp}: FAQ question missing name")
                    if ans.get("@type") != "Answer" or not str(ans.get("text") or "").strip():
                        errors.append(f"{fp}: FAQ answer missing text")
        if t == "BreadcrumbList":
            for i, it in enumerate(d["itemListElement"], 1):
                if it.get("position") != i or not it.get("item", "").startswith("http"):
                    errors.append(f"{fp}: breadcrumb item {i} invalid")
print("JSON-LD blocks:", json.dumps(counts, sort_keys=True))
for e in errors[:50]:
    print("ERROR", e)
print(f"{len(errors)} error(s)")
sys.exit(1 if errors else 0)
