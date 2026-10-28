#!/usr/bin/env python3
"""Validate data/*.json for pull requests. Stdlib only (uses `jsonschema` too if installed).

Checks: JSON Schema (schema/company.schema.json, schema/sponsored.schema.json), unique slugs,
listing policy (no gambling/iGaming, maintainer blocklist), no private-looking fields/values,
jobs.json references known companies. Exit code 1 on any error.
"""
import json, os, re, sys, datetime
sys.path.insert(0, os.path.dirname(__file__))
import policy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors, warnings = [], []
TYPES = {"string": str, "boolean": bool, "integer": int, "array": list, "object": dict, "null": type(None)}
PRIVATE_KEYS = re.compile(r"^(fit|fit_score|applied|seen|notes?|cv|resume|phone|email|owner|private.*)$", re.I)
PRIVATE_VALUES = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|(\+?84|0)\d{9,10}\b|đã nộp|da nop", re.I)


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def check(value, schema, path):
    """Minimal JSON Schema subset: type, enum, required, properties, additionalProperties,
    pattern, minLength, maxLength, items, minItems, maxItems, uniqueItems, minimum, maximum."""
    t = schema.get("type")
    if t:
        ts = t if isinstance(t, list) else [t]
        if not any(isinstance(value, TYPES[x]) and not (x == "integer" and isinstance(value, bool)) for x in ts):
            errors.append(f"{path}: expected {t}, got {type(value).__name__}"); return
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", 10**9):
            errors.append(f"{path}: length {len(value)} out of range")
    if isinstance(value, int) and not isinstance(value, bool):
        if value < schema.get("minimum", -10**18) or value > schema.get("maximum", 10**18):
            errors.append(f"{path}: {value} out of range")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", 10**9):
            errors.append(f"{path}: {len(value)} items out of range")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            errors.append(f"{path}: duplicate items")
        for i, v in enumerate(value):
            if "items" in schema:
                check(v, schema["items"], f"{path}[{i}]")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                errors.append(f"{path}: missing required field '{k}'")
        props = schema.get("properties", {})
        for k, v in value.items():
            if k in props:
                check(v, props[k], f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: field '{k}' is not allowed (public schema only)")


def scan_private(obj, path):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if PRIVATE_KEYS.match(k) and not k.startswith("_"):
                errors.append(f"{path}.{k}: private-looking field name")
            scan_private(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            scan_private(v, f"{path}[{i}]")
    elif isinstance(obj, str) and PRIVATE_VALUES.search(obj) and not obj.startswith("http"):
        errors.append(f"{path}: looks like an email/phone/private note: {obj[:60]!r}")


def main():
    companies = load("data/companies.json")
    schema = load("schema/company.schema.json")
    try:
        import jsonschema  # optional, stricter
        v = jsonschema.Draft202012Validator(schema)
        for i, c in enumerate(companies):
            for e in v.iter_errors(c):
                errors.append(f"companies[{i}] ({c.get('slug')}): {e.message}")
    except ImportError:
        for i, c in enumerate(companies):
            check(c, schema, f"companies[{i}]({c.get('slug')})")
    slugs = [c.get("slug") for c in companies]
    dup = {s for s in slugs if slugs.count(s) > 1}
    if dup:
        errors.append(f"duplicate slugs: {sorted(dup)}")
    names = [re.sub(r'\W', '', (c.get('name') or '').lower()) for c in companies]
    if len(set(names)) != len(names):
        warnings.append("two companies normalise to the same name; check for duplicates")
    today = datetime.date.today().isoformat()
    for c in companies:
        why = policy.exclusion_reason(c)
        if why:
            errors.append(f"{c.get('slug')}: not allowed on this list ({why})")
        if c.get("last_checked", "") > today:
            errors.append(f"{c.get('slug')}: last_checked is in the future")
    scan_private(companies, "companies")

    known = set(slugs)
    if os.path.exists(os.path.join(ROOT, "data/jobs.json")):
        jobs = load("data/jobs.json")
        keys = set()
        for j in jobs:
            if j.get("company_slug") not in known:
                errors.append(f"job {j.get('key')}: unknown company_slug {j.get('company_slug')}")
            if j.get("key") in keys:
                errors.append(f"job {j.get('key')}: duplicate key")
            keys.add(j.get("key"))
            if not str(j.get("url", "")).startswith("http"):
                errors.append(f"job {j.get('key')}: bad url")
    if os.path.exists(os.path.join(ROOT, "data/sources.json")):
        for s in load("data/sources.json"):
            if s.get("slug") not in known:
                errors.append(f"source {s.get('slug')}: unknown company")
    sp = load("data/sponsored.json")
    check(sp, load("schema/sponsored.schema.json"), "sponsored")
    for it in sp.get("items", []):
        if it.get("starts", "") > it.get("expires", ""):
            errors.append(f"sponsored {it.get('id')}: starts after expires")

    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(companies)} companies checked: {len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
