# SEO

## Principles

- **Every page is pre-rendered static HTML** (`scripts/build.py` → `dist/`). JavaScript is progressive enhancement only.
- **One canonical domain** from `site.config.json` → `SITE_URL` (`https://remotejob.nguyenquocdat.dev`).
- **Vietnamese first**: Vietnamese pages live at the root, English pages under `/en/`. Each page has
  `<link rel="canonical">` and `hreflang` alternates for `vi`, `en` and `x-default` (→ Vietnamese).
- **ASCII slugs** (diacritics stripped): `/cong-ty/<slug>/`, `/viec-lam/<company>-<job-slug>/`, `/viec-lam-remote/<role>/`.

## URL map

| Page | Vietnamese | English |
| --- | --- | --- |
| Home | `/` | `/en/` |
| Companies | `/cong-ty/` | `/en/cong-ty/` |
| Company | `/cong-ty/covergo/` | `/en/cong-ty/covergo/` |
| Jobs | `/viec-lam/`, `/viec-lam/trang/2/` | `/en/viec-lam/` |
| Job | `/viec-lam/covergo-senior-full-stack-engineer-net-vue-react-fully-remote/` | `/en/viec-lam/…` |
| Role pages | `/viec-lam-remote/devops/`, `/sre/`, `/platform/`, `/ai-llm/`, `/mlops/`, `/dev/`, `/data/`, `/security/`, `/blockchain/` plus finer roles such as `/backend/`, `/frontend/`, `/qa/`, `/product/` when that role has at least 3 open jobs | `/en/viec-lam-remote/…` |
| Skill, hours, level, salary | `/viec-lam-remote/python/`, `/kubernetes/`, `/gio-eu-apac/`, `/gio-my/`, `/senior/`, `/luong-cong-khai/` — same three-job minimum, skipped when the data is thinner | `/en/viec-lam-remote/…` |
| Feeds | `/feed.xml` (RSS), `/atom.xml`, `/feed.json` | `/en/feed.xml`, `/en/atom.xml`, `/en/feed.json` |
| Post a job | `/dang-tin/` | `/en/dang-tin/` |
| Tools | `/cong-cu/` | `/en/cong-cu/` |
| Privacy | `/chinh-sach-bao-mat/` | `/en/privacy/` |
| Terms | `/dieu-khoan/` | `/en/terms/` |
| Contact | `/lien-he/` | `/en/contact/` |
| Support | `/ung-ho/` | `/en/support/` |

## Metadata

- Titles and meta descriptions are written per page type, Vietnamese first (e.g. "Việc làm DevOps remote tại Việt Nam").
- Open Graph + Twitter `summary_large_image` on every page, default image `/og-default.png` (1200×630, branded).
- `theme-color`, web manifest, SVG + PNG favicons, apple-touch-icon.

## Structured data (JSON-LD)

| Type | Where | Rule |
| --- | --- | --- |
| `WebSite` | home | always |
| `ItemList` | company directory | always |
| `BreadcrumbList` | every page except home | always, matches the visible breadcrumbs |
| `Organization` | company pages | always (`name`, `url`, `sameAs` = careers page) |
| `JobPosting` | job pages | **only** when title, hiringOrganization, url **and** datePosted are present, the job is still `open`, remote, and names Vietnam or is open worldwide (APAC-only postings are skipped because they may not include Vietnam). Uses `jobLocationType: TELECOMMUTE` and `applicantLocationRequirements: {Country: Vietnam}`. `validThrough` is last checked + 30 days when `last_checked` exists, and is omitted otherwise. A published salary string is copied into the description; a structured `baseSalary` is not invented. Removed or stale jobs do not emit JobPosting. |
| `FAQPage` | category hubs with at least 3 open jobs | questions are the page's own counts (jobs, companies, region, salary). |

Seed jobs have no posting date, so they get `JobPosting` only after `refresh_jobs.py` reads `datePosted`
from the ATS API. `python3 scripts/check_jsonld.py` validates all blocks; the Rich Results Test
(https://search.google.com/test/rich-results) should be used on a few live job pages after deploy.

## Expired jobs

- A job missing from its ATS feed is marked `status: removed` with `removed_on`.
- Removed or stale (not seen for `JOB_STALE_DAYS` = 30 days) jobs disappear from lists and sitemaps.
- Their page stays for `REMOVED_PAGE_KEEP_DAYS` = 30 days with `noindex,follow`, a "no longer available" banner,
  no JobPosting and links to similar jobs; after that the page is deleted (404).

## Sitemaps and robots

- `/sitemap.xml` is a sitemap index → `/sitemap-vi.xml` and `/sitemap-en.xml`; each URL has `lastmod`
  (company/job `last_checked`) and `xhtml:link` hreflang alternates. Privacy, terms, and contact
  are included, as are `/ung-ho/` and `/en/support/`. Removed jobs stay `noindex` and out of the sitemap.
- `/robots.txt` allows `/`, keeps `Disallow: /data/jobs-index.json`, names Mediapartners-Google,
  AdsBot-Google, GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, PerplexityBot, Google-Extended,
  Applebot-Extended, and Bingbot with the same allow/disallow, lists the sitemap index and both
  language sitemaps, and comments the absolute URL of `/llms.txt`.
- `/llms.txt` (llmstxt.org) and `/llms-full.txt` are generated at build time and served as
  `text/plain; charset=utf-8`. The full file lists public company facts and current
  direct-employer jobs only.

## IndexNow

`indexnow_key` in `site.config.json` is written to `dist/<key>.txt` (the key is public by design).
After a successful data commit on `main`, `scripts/indexnow.py` POSTs new, changed, and removed
job URLs (Vietnamese and English) to `https://api.indexnow.org/indexnow`. Nothing is sent when
the only change is `last_checked`. There is no retry.

## Internal linking

Company ↔ jobs ↔ category hubs: each job links to its company, similar jobs, and the role, skill, timezone, seniority, and salary hubs it actually matches. Each company links to its jobs, role pages for its `hires_roles`, and hubs that contain its open jobs. Hub pages link to related hubs. The home page links to popular categories. Hubs are omitted (or, for the original role URLs, `noindex`) when fewer than 3 direct-employer jobs are open. Onsite postings are not counted on these pages.

`/feed.xml` and `/en/feed.xml` are RSS 2.0 of the newest direct-employer jobs. Atom and JSON Feed sit beside them (`/atom.xml`, `/feed.json`, and the `/en/` copies). HTML pages advertise them with `<link rel="alternate">`.

## Core Web Vitals

- No render-blocking JS (`defer`), one small cacheable stylesheet, system fonts, no web fonts.
- Ad slots and cards reserve their size (no layout shift).
- The only analytics is Cloudflare Web Analytics, cookieless and aggregate-only, turned on in the Pages project so the beacon is injected there and not committed here. No personal tracking, no cookies, no other analytics. `site/_headers` allows `script-src https://static.cloudflareinsights.com` and `connect-src https://cloudflareinsights.com` and nothing broader.
- The apply-click interstitial is not in the HTML and is not shown on load or on a landing from search,
  so it does not sit on the LCP element and does not add CLS. See `docs/MONETIZATION.md`.
- Lighthouse 13 (local, 2026-10-28): home and a job page score Performance 100, Accessibility 100, Best Practices 100, SEO 100 on mobile, and Performance 96 with the other categories at 100 on desktop. CLS is 0. The Cloudflare beacon is not in the local build, so these runs do not include it.

## Google Search Console setup

1. Open https://search.google.com/search-console and **Add property** → **Domain** → `nguyenquocdat.dev`
   (covers all subdomains) — or **URL prefix** → `https://remotejob.nguyenquocdat.dev/`.
2. Verify:
   - Domain property: add the shown `TXT` record (`google-site-verification=…`) at the zone apex in Cloudflare DNS.
   - URL-prefix property: alternatively add the HTML file Google gives you to `site/` and make the build copy it, or use DNS.
3. **Sitemaps** → submit `https://remotejob.nguyenquocdat.dev/sitemap.xml`.
4. **URL Inspection** → inspect the home page, one company page and one job page → **Request indexing**.
5. After a few days check **Pages** (indexing), **Enhancements → Job postings** and **Breadcrumbs** for errors,
   and **International targeting/hreflang** issues if reported.
6. Optional: Bing Webmaster Tools → import from Search Console.
