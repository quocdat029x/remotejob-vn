"""Facet tokens for the jobs index.

The predicates are the category-hub rules (role tags and title patterns, skill
words, EU/APAC vs US hours, seniority words, and a non-empty public salary).
Filter values use the short slugs from the hubs, except time zones, which use
`eu-apac` and `us` in the query string. Hub paths stay `gio-eu-apac` / `gio-my`.
"""
import re

import hubs
from site_text import ROLE_PAGES, T

_TZ_URL = {"gio-eu-apac": "eu-apac", "gio-my": "us"}
_REGION = ("vn", "apac", "global", "other")
_REMOTE = ("yes", "hybrid", "unknown", "no")
_POSTED = (("7", "posted_7"), ("30", "posted_30"), ("90", "posted_90"))


def _compile_roles():
    rows = []
    for slug, vi, en, tags, regex, _co in ROLE_PAGES:
        rows.append((slug, vi, en, set(tags or ()), re.compile(regex, re.I)))
    have = {row[0] for row in rows}
    for slug, vi, en, tags, regex in hubs.EXTRA_ROLES:
        if slug in have:
            continue
        rows.append((slug, vi, en, set(tags or ()), re.compile(regex, re.I)))
    return rows


_ROLE = _compile_roles()
_TECH = [(slug, vi, en, re.compile(regex, re.I)) for slug, vi, en, regex in hubs.TECHS]
_LEVEL = [(slug, vi, en, re.compile(regex, re.I)) for slug, vi, en, regex in hubs.SENIORITY]
_TZ = [(key, vi, en) for _slug, vi, en, key in hubs.TIMEZONES]


def _hit(job, tags, rx):
    if tags and (set(job.get("roles") or ()) & tags):
        return True
    return bool(rx.search(job.get("title") or ""))


def _day(value):
    raw = (value or "")[:10]
    if len(raw) != 10 or raw[4] != "-" or raw[7] != "-":
        return ""
    year, month, day = raw.split("-")
    if year.isdigit() and month.isdigit() and day.isdigit():
        return raw
    return ""


def tokens(job, company):
    """Return facet values for one job. `company` may carry `_tz` and `group`."""
    company = company or {}
    title = job.get("title") or ""
    role = [slug for slug, _vi, _en, tags, rx in _ROLE if _hit(job, tags, rx)]
    skill = [slug for slug, _vi, _en, rx in _TECH if rx.search(title)]
    level = [slug for slug, _vi, _en, rx in _LEVEL if rx.search(title)]
    tz = []
    for slug in hubs.timezone_slugs(job, company.get("_tz")):
        url = _TZ_URL.get(slug)
        if url and url not in tz:
            tz.append(url)
    salary = "yes" if (job.get("salary") or "").strip() else ""
    return {
        "role": role,
        "skill": skill,
        "tz": tz,
        "level": level,
        "group": company.get("group") or "",
        "salary": salary,
        "posted": _day(job.get("date_posted")),
    }


def empty_seen():
    return {key: set() for key in ("role", "skill", "tz", "level", "region", "remote", "group", "salary", "posted")}


def observe(seen, job, tok):
    """Record values that should appear as options. Caller skips aggregator jobs."""
    for key in ("role", "skill", "tz", "level"):
        seen[key].update(tok[key])
    if job.get("region"):
        seen["region"].add(job["region"])
    if job.get("remote"):
        seen["remote"].add(job["remote"])
    if tok.get("group"):
        seen["group"].add(tok["group"])
    if tok.get("salary"):
        seen["salary"].add(tok["salary"])
    if tok.get("posted"):
        seen["posted"].add("1")


def _keep(rows, seen):
    return [[slug, vi, en] for slug, vi, en in rows if slug in seen]


def catalog(seen, companies):
    """Facet menu for both languages.

    Each facet is [key, vi label, en label, options].
    Each option is [value, vi label, en label].
    `companies` is (slug, name) pairs, already sorted.
    Posted buckets stay 7 / 30 / 90 days; app.js counts those same values.
    """
    vi, en = T["vi"], T["en"]
    fx = []

    def add(key, label_vi, label_en, opts):
        if opts:
            fx.append([key, label_vi, label_en, opts])

    add("role", vi["f_role"], en["f_role"], _keep([(s, a, b) for s, a, b, _t, _r in _ROLE], seen["role"]))
    add("skill", vi["f_skill"], en["f_skill"], _keep([(s, a, b) for s, a, b, _r in _TECH], seen["skill"]))
    add("tz", vi["f_tz"], en["f_tz"], _keep(_TZ, seen["tz"]))
    add("level", vi["f_level"], en["f_level"], _keep([(s, a, b) for s, a, b, _r in _LEVEL], seen["level"]))
    if companies:
        add("company", vi["f_company"], en["f_company"], [[slug, name, name] for slug, name in companies])
    add("region", vi["f_region"], en["f_region"], _keep([(k, vi["region_" + k], en["region_" + k]) for k in _REGION], seen["region"]))
    add("remote", vi["f_remote"], en["f_remote"], _keep([(k, vi["remote_" + k], en["remote_" + k]) for k in _REMOTE], seen["remote"]))
    add("group", vi["f_group"], en["f_group"], _keep([("A", vi["group_A"], en["group_A"]), ("B", vi["group_B"], en["group_B"])], seen["group"]))
    if "yes" in seen["salary"]:
        add("salary", vi["f_salary"], en["f_salary"], [["yes", vi["f_salary_yes"], en["f_salary_yes"]]])
    if seen["posted"]:
        add("posted", vi["f_posted"], en["f_posted"], [[value, vi[key], en[key]] for value, key in _POSTED])
    return fx
