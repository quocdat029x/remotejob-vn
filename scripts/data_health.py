#!/usr/bin/env python3
"""Refresh health: a public status file, and one GitHub issue when a run is unhealthy.

The issue uses the workflow's GITHUB_TOKEN (issues: write). No other secret.
A later healthy refresh closes that issue. Threshold: more than 30% of the API
sources attempted in the run failed. A crashed workflow is also unhealthy; the
workflow passes that in --reason.

Usage:
  python3 scripts/data_health.py --github-output
  python3 scripts/data_health.py --open-issue
  python3 scripts/data_health.py --close-issue
"""
import argparse, json, os, sys, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THRESHOLD = 0.30
TITLE = "Data refresh health"
LABEL = "data-health"
LABEL_COLOR = "b60205"


def merge_status(root, updates):
    path = os.path.join(root, "data", "status.json")
    current = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            current = json.load(fh)
    current.update(updates)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(current, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return current


def load_status(root=ROOT):
    path = os.path.join(root, "data", "status.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def is_unhealthy(attempted, failed, threshold=THRESHOLD):
    """True when this run tried at least one API source and more than `threshold` failed."""
    attempted = int(attempted or 0)
    failed = int(failed or 0)
    if attempted <= 0:
        return False
    return (failed / attempted) > threshold


def summary_text(status, workflow_result="success", reason=""):
    attempted = status.get("last_api_attempted")
    failed = status.get("last_api_failed")
    ratio = "n/a"
    if isinstance(attempted, int) and attempted > 0 and isinstance(failed, int):
        ratio = f"{failed}/{attempted} ({failed / attempted:.0%}; threshold {THRESHOLD:.0%})"
    lines = [
        "Automated data-health report for RemoteJob VN. Public counts only.",
        "",
        f"Workflow result: {workflow_result}",
        f"API source failures this run: {ratio}",
        f"Last API refresh date: {status.get('last_api_refresh') or 'n/a'}",
        f"Last HTML link check: {status.get('last_link_check') or 'not run'}",
    ]
    if status.get("last_link_check"):
        lines.append(
            "Link check: "
            f"checked {status.get('last_link_checked')} · alive {status.get('last_link_alive')} · "
            f"removed {status.get('last_link_removed')} · blocked {status.get('last_link_blocked')} · "
            f"errors {status.get('last_link_errors')}"
        )
    if reason:
        lines += ["", reason.strip()]
    lines += [
        "",
        "This issue is opened with the workflow GITHUB_TOKEN when the refresh workflow fails, "
        "or when more than 30% of API sources fail in a run. A later healthy refresh closes it.",
        "Network errors on individual HTML job links do not by themselves open this issue.",
    ]
    return "\n".join(lines)


def _github(method, path, body=None):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        raise RuntimeError("GITHUB_TOKEN and GITHUB_REPOSITORY are required")
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "RemoteJobVN-DataHealth",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        return exc.code, raw


def _repo_path(suffix):
    return f"/repos/{os.environ['GITHUB_REPOSITORY']}{suffix}"


def ensure_label():
    code, _payload = _github("POST", _repo_path("/labels"), {
        "name": LABEL, "color": LABEL_COLOR,
        "description": "Automated alert when the public job refresh is unhealthy",
    })
    if code in (201, 422):
        return
    raise RuntimeError(f"could not ensure label {LABEL}: HTTP {code}")


def open_issues():
    code, payload = _github("GET", _repo_path(f"/issues?state=open&labels={LABEL}&per_page=20"))
    if code != 200 or not isinstance(payload, list):
        raise RuntimeError(f"could not list {LABEL} issues: HTTP {code}")
    return [item for item in payload if item.get("title") == TITLE]


def comment(number, body):
    code, _payload = _github("POST", _repo_path(f"/issues/{number}/comments"), {"body": body})
    if code not in (200, 201):
        raise RuntimeError(f"could not comment on issue {number}: HTTP {code}")


def open_or_update(body):
    ensure_label()
    existing = open_issues()
    if existing:
        number = existing[0]["number"]
        comment(number, body)
        print(f"updated issue #{number}")
        return
    code, payload = _github("POST", _repo_path("/issues"), {"title": TITLE, "body": body, "labels": [LABEL]})
    if code != 201:
        raise RuntimeError(f"could not open issue: HTTP {code} {payload!s:.200}")
    print(f"opened issue #{payload.get('number')}")


def close_open(body):
    existing = open_issues()
    if not existing:
        print("no open data-health issue")
        return
    for item in existing:
        number = item["number"]
        comment(number, body)
        code, _payload = _github("PATCH", _repo_path(f"/issues/{number}"), {"state": "closed", "state_reason": "completed"})
        if code != 200:
            raise RuntimeError(f"could not close issue {number}: HTTP {code}")
        print(f"closed issue #{number}")


def write_github_output(status):
    attempted = int(status.get("last_api_attempted") or 0)
    failed = int(status.get("last_api_failed") or 0)
    unhealthy = is_unhealthy(attempted, failed)
    text = summary_text(status)
    print(text)
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        print(f"unhealthy={str(unhealthy).lower()}")
        return
    delim = "RJVN_HEALTH"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"unhealthy={'true' if unhealthy else 'false'}\n")
        fh.write(f"summary<<{delim}\n{text}\n{delim}\n")


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--github-output", action="store_true")
    mode.add_argument("--open-issue", action="store_true")
    mode.add_argument("--close-issue", action="store_true")
    ap.add_argument("--reason", default="")
    ap.add_argument("--workflow-result", default=os.environ.get("WORKFLOW_RESULT", "success"))
    args = ap.parse_args()
    status = load_status()
    if args.github_output:
        write_github_output(status)
        return
    body = summary_text(status, args.workflow_result, args.reason or os.environ.get("HEALTH_SUMMARY", ""))
    if args.open_issue:
        open_or_update(body)
    else:
        close_open("The latest job refresh was healthy, so this alert is closed.\n\n" + body)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        sys.exit(1)
