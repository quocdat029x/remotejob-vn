# Deploying RemoteJob VN

The site is a folder of static files built by `python3 scripts/build.py` into `dist/`.
The canonical domain is configured in one place: `SITE_URL` in `site.config.json`
(currently `https://remotejob.nguyenquocdat.dev`). Change it there and rebuild; canonical URLs, hreflang,
sitemaps, robots.txt, Open Graph tags, JSON-LD and `dist/CNAME` all follow.

> The site is hosted on Cloudflare Pages. GitHub Actions does not deploy it. The daily
> `refresh.yml` workflow commits `data/` to the repository default branch, and Pages rebuilds from that push.
> Scheduled workflows run from the GitHub default branch. This repository should use `main`.
> If GitHub still shows `master` (the original empty commit), set **Settings → General → Default branch**
> to `main`, and set the Pages production branch to `main` as well.

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

The daily `refresh.yml` workflow commits updated `data/` to the default branch with the built-in
`GITHUB_TOKEN` (`contents: write` only). It does not use any other secret. Each such commit triggers
a Cloudflare Pages rebuild. The refresh calls public ATS APIs at about one request per second and
does not sign in.

There is no GitHub Pages workflow. Hosting is Cloudflare Pages, which is what applies `dist/_headers`.

## After the first deploy

- Check `https://remotejob.nguyenquocdat.dev/robots.txt` and `/sitemap.xml`.
- Follow the Search Console steps in `docs/SEO.md`.
