#!/usr/bin/env python3
"""Google Indexing API publisher for JobPosting URLs.

Google explicitly allows and encourages the Indexing API for JobPosting schema:
https://developers.google.com/search/apis/indexing-api/v3/quickstart

When run after daily job refresh and build, this notifies Google to crawl
new or updated JobPosting pages immediately (within minutes) instead of
waiting days for normal search engine spider discovery.

Setup:
1. Create a Google Cloud Project & enable "Indexing API".
2. Create a Service Account, generate a JSON Key file, and save it as
   `google-service-account.json` (do not commit to git).
3. In Google Search Console, add the Service Account email as an "Owner" of the property.
4. Run:
   python3 scripts/google_indexing.py --key google-service-account.json --limit 100
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEXING_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
SCOPES = "https://www.googleapis.com/auth/indexing"


def load_config():
    cfg_path = os.path.join(ROOT, "site.config.json")
    with open(cfg_path, encoding="utf-8") as f:
        return json.load(f)


def create_signed_jwt(service_account_dict):
    """Create a signed JWT using standard Python stdlib and RSA private key."""
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
    except ImportError:
        # Fallback to PyJWT or inform user
        pass

    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": service_account_dict["client_email"],
        "scope": SCOPES,
        "aud": TOKEN_ENDPOINT,
        "exp": now + 3600,
        "iat": now,
    }

    def b64url(data):
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    token_base = f"{b64url(json.dumps(header).encode())}.{b64url(json.dumps(payload).encode())}"

    # Sign using cryptography
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    private_key = load_pem_private_key(service_account_dict["private_key"].encode(), password=None)
    signature = private_key.sign(token_base.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    return f"{token_base}.{b64url(signature)}"


def get_access_token(service_account_dict):
    jwt = create_signed_jwt(service_account_dict)
    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt,
    }).encode("utf-8")
    req = urllib.request.Request(TOKEN_ENDPOINT, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["access_token"]


def publish_url(access_token, url, action="URL_UPDATED", dry_run=False):
    """Publish a single URL notification to Google Indexing API."""
    body = {
        "url": url,
        "type": action  # URL_UPDATED or URL_DELETED
    }
    if dry_run:
        print(f"[DRY-RUN] {action}: {url}")
        return True

    req = urllib.request.Request(INDEXING_ENDPOINT, data=json.dumps(body).encode("utf-8"), method="POST")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[SUCCESS] {action}: {url}")
            return True
    except urllib.error.HTTPError as ex:
        err = ex.read().decode("utf-8")
        print(f"[ERROR {ex.code}] {url}: {err}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Submit Job URLs to Google Indexing API")
    parser.add_argument("--key", help="Path to Google Service Account JSON key", default="google-service-account.json")
    parser.add_argument("--limit", type=int, default=100, help="Max URLs to submit (quota limit is typically 200/day)")
    parser.add_argument("--action", choices=["URL_UPDATED", "URL_DELETED"], default="URL_UPDATED")
    parser.add_argument("--dry-run", action="store_true", help="Print URLs without submitting")
    args = parser.parse_args()

    cfg = load_config()
    site_url = cfg["SITE_URL"].rstrip("/")

    jobs_path = os.path.join(ROOT, "data", "jobs.json")
    with open(jobs_path, encoding="utf-8") as f:
        jobs = json.load(f)

    import hashlib
    import unicodedata
    import re

    def slugify(text, limit=70):
        t = (text or "").replace("đ", "d").replace("Đ", "D")
        t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
        t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
        if len(t) > limit:
            t = t[:limit].rsplit("-", 1)[0]
        return t or "job"

    used = set()
    job_paths = {}
    for job in sorted(jobs, key=lambda item: item["key"]):
        base = slugify(job["company_slug"] + "-" + job["title"], 80)
        slug = base if base not in used else base + "-" + hashlib.sha1(job["key"].encode()).hexdigest()[:6]
        used.add(slug)
        job_paths[job["key"]] = f"/viec-lam/{slug}/"

    # Filter for active jobs with paths
    target_urls = []
    for j in sorted(jobs, key=lambda x: x.get("last_checked", ""), reverse=True):
        if j.get("status") == "open":
            p = job_paths.get(j["key"])
            if p:
                url_vi = f"{site_url}{p}"
                url_en = f"{site_url}/en{p}"
                target_urls.extend([url_vi, url_en])
                if len(target_urls) >= args.limit:
                    break

    print(f"Found {len(target_urls)} JobPosting URLs to process (limit: {args.limit})")

    if args.dry_run:
        for u in target_urls:
            publish_url(None, u, args.action, dry_run=True)
        return

    if not os.path.exists(args.key):
        print(f"Service account key '{args.key}' not found. Run with --dry-run or provide --key.", file=sys.stderr)
        sys.exit(1)

    with open(args.key, encoding="utf-8") as f:
        sa = json.load(f)

    token = get_access_token(sa)
    success = 0
    for u in target_urls:
        if publish_url(token, u, args.action):
            success += 1
        time.sleep(0.5)

    print(f"Successfully submitted {success}/{len(target_urls)} URLs to Google Indexing API.")


if __name__ == "__main__":
    main()
