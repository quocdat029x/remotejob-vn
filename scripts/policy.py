"""Listing policy shared by import, validation and refresh.

1. No gambling / betting / casino / iGaming companies, or companies whose main business serves them.
2. A small maintainer blocklist (stored as SHA-256 of normalised names, so the list itself
   does not publish who is on it).
"""
import hashlib, re, urllib.parse as up

GAMBLING_RX = re.compile(
    r"gambl|betting|sportsbook|casino|igaming|i-gaming|bookmaker|lottery|poker|slot game|"
    r"cá cược|cờ bạc|nhà cái|xổ số|tài xỉu", re.I)

# Known gambling / gambling-serving companies (public reason, plain text).
GAMBLING_BLOCKLIST = {"thegrandhotram", "playstudios", "geocomply", "sportygroup", "sporty", "coinspaid", "opinov8"}

# Maintainer policy blocklist: sha256(normalised name).
MAINTAINER_BLOCKLIST_SHA256 = {
    "c92dd1594e0371100e93c4414683ebb3a96f3934488df322ec5d956cbeed591b",
}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _candidates(company):
    words = re.findall(r"[a-z0-9]+", (company.get("name") or "").lower())
    out = {_norm(company.get("slug")), _norm(company.get("name"))}
    for i in range(len(words)):
        for j in range(i + 1, min(len(words), i + 4) + 1):
            out.add("".join(words[i:j]))
    for u in (company.get("website"), company.get("careers_url")):
        host = up.urlparse(u or "").netloc.lower().removeprefix("www.")
        if host:
            out.add(_norm(host.split(".")[0]))
    out.discard("")
    return out


def exclusion_reason(company):
    cands = _candidates(company)
    if cands & GAMBLING_BLOCKLIST:
        return "gambling/betting/casino/iGaming (blocklist)"
    if any(hashlib.sha256(c.encode()).hexdigest() in MAINTAINER_BLOCKLIST_SHA256 for c in cands):
        return "maintainer policy blocklist"
    blob = " ".join(str(company.get(k) or "") for k in ("name", "website", "careers_url", "hq", "remote_policy"))
    if GAMBLING_RX.search(blob):
        return "gambling/betting/casino/iGaming (keyword match)"
    return None
