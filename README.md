# RemoteJob VN

A free, open-source, community-maintained directory of **remote-first companies that hire people in Vietnam**,
plus their currently open remote jobs. The site is Vietnamese-first with an English version under `/en/`.

- Live site (planned): https://remotejob.nguyenquocdat.dev
- Repository: https://github.com/quocdat029x/remotejob-vn
- Data: CC BY 4.0 (`LICENSE-DATA.md`) · Code: MIT (`LICENSE`)
- Cookieless, aggregate-only Cloudflare Web Analytics (enabled in the Cloudflare Pages project, not committed here). No personal tracking, no cookies, no other analytics, no sign-in.

## How it works

```
data/companies.json   curated public facts per company (validated by schema/company.schema.json)
data/sources.json     where each company's jobs come from (ATS + token/endpoint) and fetch status
data/jobs.json        open jobs, refreshed daily from public ATS APIs
data/sponsored.json   paid "Featured job" slots (empty by default, schema/sponsored.schema.json)
data/affiliates.json  tools page slots (payments, learning, home office, VPS, coworking); replace url later
data/ads.json         house ad slots plus the outbound-click interstitial creative (no ad scripts)
site.config.json      SITE_URL (canonical domain), site name, staleness windows, page size, repo URL
scripts/build.py      static site generator -> dist/ (pre-rendered HTML for every page, vi + en)
scripts/refresh_jobs.py  polite job refresher (1 request/second, public endpoints only)
scripts/validate.py   schema + policy + privacy checks (runs on every PR)
scripts/check_jsonld.py  structural JSON-LD check of dist/
site/                 CSS, JS (progressive enhancement), favicon, _headers, CNAME
```

Every page is plain pre-rendered HTML. JavaScript adds instant filtering, "show more", the theme toggle and the
apply-click interstitial. Without JS, pagination and all links still work.

## Quick start

Requirements: Python 3.10+ (stdlib only). Pillow is optional and only needed to regenerate the OG image and PNG icons.

```bash
git clone https://github.com/quocdat029x/remotejob-vn.git
cd remotejob-vn
python3 scripts/validate.py          # check data
python3 scripts/build.py            # build dist/
python3 -m http.server 8765 --directory dist
# open http://127.0.0.1:8765/
```

Refresh jobs from public ATS APIs (Greenhouse, Lever, Ashby, Workable, Recruitee):

```bash
python3 scripts/refresh_jobs.py --dry-run --only gradion,akuity   # try a few sources without writing
python3 scripts/refresh_jobs.py                                    # all API sources, ~1 request/second
python3 scripts/linkcheck_jobs.py --dry-run --limit 3             # HTML-only URL check, no writes
```

Other tools:

```bash
python3 scripts/check_jsonld.py      # validate JSON-LD in dist/
python3 scripts/test_jobfilter.py && python3 scripts/test_listing.py && python3 scripts/test_content.py && python3 scripts/test_freshness.py && python3 scripts/test_support.py && python3 scripts/test_hubs.py && node scripts/test_interstitial.mjs
node scripts/test_interstitial_bfcache.mjs   # apply-dialog Back button; needs google-chrome
./scripts/screenshots.sh             # light/dark screenshots at 1280 and 390 px (needs google-chrome + local server)
```

## Pages

| Path | Content |
| --- | --- |
| `/` | Home: search, role shortcuts, jobs that mention Vietnam/APAC, Vietnamese companies |
| `/cong-ty/` | Company directory with filters (role, hiring mode, group, timezone) |
| `/cong-ty/<slug>/` | Company profile, open jobs, related companies |
| `/viec-lam/` (+ `/trang/N/`) | All open jobs, paginated; filters by role/company/region/remote with JS |
| `/viec-lam/<company>-<job>/` | Job page with apply link and JobPosting JSON-LD when data allows |
| `/viec-lam-remote/<slug>/` | Category hubs with at least 3 open direct-employer jobs: roles, title skills (Python, Go, …), EU/APAC vs US hours, seniority, and public salary (`/luong-cong-khai/`) |
| `/feed.xml`, `/atom.xml`, `/feed.json` | Newest jobs (RSS, Atom, JSON Feed). English copies under `/en/` |
| `/cong-cu/` | Tools for remote workers (affiliate slots, clearly labeled; URLs are placeholders) |
| `/dang-tin/` | Post a sponsored job (pricing: contact, via a GitHub issue) |
| `/quang-cao/`, `/gioi-thieu/` | Advertising info, about/privacy/license |
| `/ung-ho/` | Support the project: VietQR (TPBank) and Buy Me a Coffee |
| `/chinh-sach-bao-mat/`, `/dieu-khoan/`, `/lien-he/` | Privacy, terms, contact (GitHub issues only) |
| `/en/privacy/`, `/en/terms/`, `/en/contact/` | English privacy, terms, and contact |
| `/en/support/` | English support page (Buy Me a Coffee, then VietQR) |
| `/llms.txt`, `/llms-full.txt` | llmstxt.org summary and a compact public listing |
| `/en/...` | English versions of the HTML pages above |

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) – add or fix a company
- [docs/DEPLOY.md](docs/DEPLOY.md) – Cloudflare Pages (`python3 scripts/build.py`, output `dist`)
- [docs/SEO.md](docs/SEO.md) – SEO design and Google Search Console setup
- [docs/JOB_FILTER_RULES.md](docs/JOB_FILTER_RULES.md) – which job links are kept and why
- [docs/MONETIZATION.md](docs/MONETIZATION.md) – ad slots, affiliate page, sponsored jobs
- [docs/DESIGN.md](docs/DESIGN.md) – design system, budgets, accessibility

## Content policy

- Public facts only. No personal data about anyone (no emails, phone numbers, CVs, notes or ratings).
- No gambling, betting, casino or iGaming companies. `scripts/policy.py` enforces a keyword rule and a blocklist.
- Jobs not seen for 30 days are hidden; removed jobs keep a `noindex` page for 30 days, then are deleted.

## Workflows

- `.github/workflows/validate.yml` – runs on every pull request: unit tests, validate data, build, check JSON-LD.
- `.github/workflows/refresh.yml` – daily: refresh jobs from public APIs (~1 request/second), validate, commit `data/` to the default branch with `GITHUB_TOKEN` only. Cloudflare Pages rebuilds from that push.

Python 3.12 is pinned in `.python-version`. Set `PYTHON_VERSION=3.12` on Cloudflare Pages (see `docs/DEPLOY.md`).
Companies with `"kind": "aggregator"` (Huzzle) stay in the directory but are left out of the default job lists.
