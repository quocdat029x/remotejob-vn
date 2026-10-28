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
| Role pages | `/viec-lam-remote/devops/`, `/sre/`, `/platform/`, `/ai-llm/`, `/mlops/`, `/dev/`, `/data/`, `/security/`, `/blockchain/` | `/en/viec-lam-remote/…` |

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
| `JobPosting` | job pages | **only** when title, hiringOrganization, url **and** datePosted are present, the job is remote and names Vietnam or is open worldwide (APAC-only postings are skipped because they may not include Vietnam). Uses `jobLocationType: TELECOMMUTE` and `applicantLocationRequirements: {Country: VN}`; `validThrough` = last checked + 30 days. Otherwise omitted. |

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
  (company/job `last_checked`) and `xhtml:link` hreflang alternates.
- `/robots.txt` allows everything and points to the sitemap index.

## Internal linking

Company ↔ jobs ↔ role pages: each job links to its company and similar jobs, each company links to its jobs,
role pages for its `hires_roles` and 6 related companies, and role pages link to each other and to companies hiring that role.

## Core Web Vitals

- No render-blocking JS (`defer`), one small cacheable stylesheet, system fonts, no web fonts.
- Ad slots and cards reserve their size (no layout shift). No third-party requests at all.
- The apply-click interstitial is not in the HTML and is not shown on load or on a landing from search,
  so it does not sit on the LCP element and does not add CLS. See `docs/MONETIZATION.md`.
- Lighthouse 13 (local, 2026-10-28): home and a job page score Performance 99–100, Accessibility 100, Best Practices 100, SEO 100 on mobile and desktop.

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
