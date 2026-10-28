# Job filter rules

Implemented in `scripts/jobfilter.py`, shared by `scripts/import_seed.py` and `scripts/refresh_jobs.py`.
A scraped link becomes a job only if it passes all of the rules below.

## 1. Is it a single job posting?

- **API sources** (Greenhouse, Lever, Ashby, Workable, Recruitee): the URL must match the ATS posting pattern
  - Greenhouse `/jobs/<digits>` or `gh_jid=<digits>`
  - Lever / Ashby `/<company>/<uuid>`
  - Workable `/j/<CODE>`
  - Recruitee `/o/<slug>`
- **HTML sources**: per-host allowlist of posting URL shapes, for example ITviec `/it-jobs/<slug>-<id>`, LinkedIn
  `/jobs/view/<id>`, Himalayas `/companies/<c>/jobs/<slug>`, CloudX `-aid<id>`, iKonnect `-jo<id>`,
  `*.applytojob.com/apply/<id>/<slug>`. Category, search and listing pages are dropped.
- **Deny list** for every source: feeds (`.xml`, `.rss`, `/feed`), `/blog/`, sign-up/login, privacy/policy pages,
  career-advice pages, job-seeker/organisation landing pages.
- **Navigation titles** ("Apply now", "Learn more", "Xem chi tiết", …) are never used as titles; the title is rebuilt
  from the URL slug instead.

## 2. Clean-up

- Titles: strip "Remote Apply", hashtags and internal codes such as `JO123`.
- Stale: titles that contain a year from 2010–2025 (e.g. "DevOps - 07/2023") are treated as old listings.
  *Update this range each January.*
- Duplicates: the same (company, title, location) is kept once (re-posts are common on some boards).
- Description: plain-text excerpt, at most 600 characters.

## 3. Tags

- `roles`: keyword rules (`ROLE_RULES`) → `sre`, `devops`, `platform`, `infra`, `security`, `data`, `ai-ml`,
  `backend`, `frontend`, `fullstack`, `mobile`, `blockchain`, `qa`, `engineering`, `product-design`,
  `sales-marketing`, `support-ops`, or `other`.
- `region`: `vn` (mentions Vietnam / Hanoi / HCMC / Da Nang …), `apac`, `global` (worldwide / anywhere), `other`.
- `remote`: `yes`, `hybrid`, `no`, `unknown`. A "Hybrid" in the title wins over an ATS-wide `remote=false` flag;
  an explicit "Remote" in the title wins over a generic on-site flag.

## 4. Lifecycle

| State | Listed | Sitemap | Page |
| --- | --- | --- | --- |
| open, checked within 30 days | yes | yes | indexable |
| not seen for 30+ days (stale) | no | no | `noindex` for 30 days, then deleted |
| missing from ATS feed (`removed`) | no | no | `noindex` + banner for 30 days, then purged from `data/jobs.json` |

## 5. Refresh politeness

- Only public, unauthenticated endpoints. No sign-in, no cookies.
- One request per second (`--delay`, minimum 1.0 s), 25 s timeout, no retries, identifying User-Agent with the repo URL.
- HTML careers pages are not scraped by default (`--include-html` to opt in); sources that fail are marked
  `status: error` in `data/sources.json` and their existing jobs are kept until they become stale.
