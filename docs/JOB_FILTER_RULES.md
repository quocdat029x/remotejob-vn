# Job filter rules

Implemented in `scripts/jobfilter.py`, shared by `scripts/import_seed.py` and `scripts/refresh_jobs.py`.
A scraped link becomes a job only if it passes all of the rules below.

## 1. Is it a single job posting?

- **API sources** (Greenhouse, Lever, Ashby, Workable, Recruitee, SmartRecruiters, Personio, Teamtailor, BambooHR, Breezy, JazzHR, Pinpoint, Rippling): the URL must match the ATS posting pattern
  - Greenhouse `/jobs/<digits>` or `gh_jid=<digits>`
  - Lever / Ashby `/<company>/<uuid>`
  - Workable `/j/<CODE>`
  - Recruitee `/o/<slug>`
  - SmartRecruiters `jobs.smartrecruiters.com/<company>/<id>`
  - Personio `jobs.personio.de|com/job/<id>`
  - Teamtailor `/jobs/<id>`
  - BambooHR `bamboohr.com/careers/<id>`
  - Breezy `breezy.hr/p/<id>`
  - JazzHR `applytojob.com/apply/<id>/<slug>`
  - Pinpoint `/postings/<slug>`
  - Rippling `ats.rippling.com/<company>/jobs/<id>`
- **HTML sources**: per-host allowlist of posting URL shapes, for example ITviec `/it-jobs/<slug>-<id>`, LinkedIn
  `/jobs/view/<id>`, Himalayas `/companies/<c>/jobs/<slug>`, CloudX `-aid<id>`, iKonnect `-jo<id>`,
  `*.applytojob.com/apply/<id>/<slug>`. Category, search and listing pages are dropped.
- **Deny list** for every source: feeds (`.xml`, `.rss`, `/feed`), `/blog/`, sign-up/login, privacy/policy pages,
  career-advice pages, job-seeker/organisation landing pages.
- **Navigation titles** ("Apply now", "Learn more", "Xem chi tiết", …) are never used as titles; the title is rebuilt
  from the URL slug instead.

## 2. Clean-up

- Titles: strip "Remote Apply", hashtags and internal codes such as `JO123`.
- Stale: a title that contains a calendar year from 2010 through the year before the current year
  (e.g. "DevOps - 07/2023") is an old listing. `title_has_stale_year` in `scripts/jobfilter.py` compares
  the year with today's date, so the window moves every 1 January with no code edit. The current calendar
  year and later years are kept; years before 2010 are ignored. The check applies to HTML and API sources.
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
- Jobs whose source is still not an API are link-checked weekly by `scripts/linkcheck_jobs.py`
  (HEAD, then one GET if HEAD is 400/404/405/410/501). HTTP 404/410, or a redirect to the company
  careers page, the company homepage, or another generic listing path, sets `status: removed` and
  `removed_on`. A live posting updates `last_checked`. Timeouts, connection errors, 401/403/429,
  and other 5xx responses leave the job untouched. TopCV and ITviec are not scraped; an existing
  public ITviec posting URL can still be link-checked.

## 6. Aggregators do not crowd out direct employers

Some sources are job boards, not the employer. Huzzle is one: a hiring platform whose public Workable
board contributed about 526 of ~3200 jobs and dominated mixed lists.

Flag the company, not the individual jobs, with optional `"kind": "aggregator"` in `data/companies.json`
(omitted means `employer`; allowed values are `employer` and `aggregator`). Example: Huzzle.

Aggregator jobs stay in `data/jobs.json`, on `/cong-ty/<slug>/`, and as their own job pages (still linked
from that company page). They are left out of:

- the home page (latest Vietnam/APAC jobs, the open-job count, and the Vietnam/APAC count),
- `/viec-lam/` and its pagination,
- role landing pages and the "companies hiring this role" chips,
- "similar jobs" on a job page.

The jobs index used by client-side filters still contains them, with a trailing `1` flag. They appear
only when the company filter is that aggregator, so choosing Huzzle still lists its roles. They are not
capped inside the company page: the whole board is available there, and mixed pages stay employer-only.
A cap would still place a job board on every page of results; exclusion keeps direct employers as the
default browse.

Aggregator postings do not get JobPosting JSON-LD, because the company record is not the hiring
organization. The company card and profile show a "Nền tảng tổng hợp / Job aggregator" badge.

The rule runs at build time (`jobs_for_default_listings` in `scripts/build.py`). Adding another board
is a one-line `"kind": "aggregator"` on that company. Do not use this flag for a direct employer that
simply has many openings.
