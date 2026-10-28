# Deploying RemoteJob VN

The site is a folder of static files built by `python3 scripts/build.py` into `dist/`.
The canonical domain is configured in one place: `SITE_URL` in `site.config.json`
(currently `https://remotejob.nguyenquocdat.dev`). Change it there and rebuild; canonical URLs, hreflang,
sitemaps, robots.txt, Open Graph tags, JSON-LD and `dist/CNAME` all follow.

> The site is hosted on Cloudflare Pages. GitHub Actions does not deploy it. The daily
> `refresh.yml` workflow commits `data/` to `main`, and Pages rebuilds from that push.
> Scheduled workflows run from the GitHub default branch, which is `main`.
> `refresh.yml` and `linkcheck.yml` still check out `ref: main` and push `HEAD:main`
> explicitly, so a data commit is not redirected if the default branch is ever changed.
> The Pages production branch is `main`.

## Cloudflare Pages

The Pages build image includes Python 3. This project uses the standard library only, so the build
does not pip-install anything. `.python-version` pins **3.12** for local pyenv and for tools that read
that file. Pages itself selects the interpreter from the `PYTHON_VERSION` environment variable; set it
in the project so it matches `.python-version`.

1. Cloudflare dashboard → **Workers & Pages → Create → Pages → Connect to Git** → pick
   `quocdat029x/remotejob-vn`. Production branch: **`main`**.
2. Build settings:
   - Framework preset: **None**
   - Build command: `python3 scripts/build.py`
   - Build output directory: `dist`
   - Environment variable: `PYTHON_VERSION` = `3.12` (same value as `.python-version`)
3. Save and deploy. You get `https://<project>.pages.dev` (for example `remotejob-vn.pages.dev`).
4. Custom domain: in the Pages project → **Custom domains → Set up a custom domain** → `remotejob.nguyenquocdat.dev`.
   Because the `nguyenquocdat.dev` zone is already on Cloudflare DNS, Cloudflare creates the record for you:

   | Type | Name | Target | Proxy |
   | --- | --- | --- | --- |
   | CNAME | `remotejob` | `<project>.pages.dev` | Proxied (orange cloud) |

   If you create it by hand, use exactly that record. SSL is issued automatically.
5. `site/_headers` is copied to `dist/_headers`; Cloudflare Pages applies it (CSP, `nosniff`, cache headers).
   The CSP allows same-origin scripts, the SHA-256 hash of the tiny inline theme script (filled in by the build),
   and the Cloudflare Web Analytics beacon only: `script-src https://static.cloudflareinsights.com` and
   `connect-src https://cloudflareinsights.com`. Do not widen those hosts.
6. Analytics: in the Pages project settings, enable **Cloudflare Web Analytics** so Pages injects the beacon.
   Do not commit a beacon snippet, a token, or any other analytics. It is cookieless and aggregate-only.
   There is no personal tracking and no cookie.
7. `dist/404.html` is used automatically for unknown paths.

The daily `refresh.yml` workflow checks out `main` and commits updated `data/` to `main` with the
built-in `GITHUB_TOKEN` (`contents: write`, and `issues: write` for the health issue below). It does
not use any other secret. Each such commit triggers a Cloudflare Pages rebuild. The refresh calls
public ATS APIs at about one request per second and does not sign in.

`linkcheck.yml` runs weekly (Mondays) and does the same checkout and push for job URLs that still
have no public feed: HEAD, then GET only when HEAD is not enough, one request per second. A 404, 410,
or redirect to a generic careers page marks the job removed. Network errors leave it untouched.

If the refresh workflow fails, or more than 30% of the API sources attempted in that run fail, the
workflow opens or updates a single GitHub issue titled "Data refresh health" with the label
`data-health`. A later refresh that succeeds and stays under that threshold closes the issue.
The weekly link-check workflow opens the same issue if the workflow itself fails.

After a data commit, `scripts/indexnow.py` submits new, changed, and removed job URLs to
`https://api.indexnow.org/indexnow` (one batch, no retries). The public IndexNow key is
`indexnow_key` in `site.config.json` and is written to `dist/<key>.txt`. A last-checked bump
alone is not submitted. An IndexNow outage does not fail the refresh.

When `adsense_client` is set, the build widens the CSP copied into `dist/_headers` with the Google
ad hosts documented in `docs/MONETIZATION.md`. `site/_headers` stays the cookieless baseline so an
empty publisher id does not change the policy. `/llms.txt` and `/llms-full.txt` are served as
`text/plain; charset=utf-8`.

There is no GitHub Pages workflow. Hosting is Cloudflare Pages, which is what applies `dist/_headers`.

## After the first deploy

- Check `https://remotejob.nguyenquocdat.dev/robots.txt` and `/sitemap.xml`.
- Follow the Search Console steps in `docs/SEO.md`.
