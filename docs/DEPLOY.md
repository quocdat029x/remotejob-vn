# Deploying RemoteJob VN

The site is a folder of static files built by `python3 scripts/build.py` into `dist/`.
The canonical domain is configured in one place: `SITE_URL` in `site.config.json`
(currently `https://remotejob.nguyenquocdat.dev`). Change it there and rebuild; canonical URLs, hreflang,
sitemaps, robots.txt, Open Graph tags, JSON-LD and `dist/CNAME` all follow.

> Nothing in this repository deploys automatically. The steps below are for the maintainer.

## Option A (recommended): Cloudflare Pages

1. Cloudflare dashboard → **Workers & Pages → Create → Pages → Connect to Git** → pick
   `quocdat029x/remotejob-vn`.
2. Build settings:
   - Framework preset: **None**
   - Build command: `python3 scripts/build.py`
   - Build output directory: `dist`
   - Environment variable: `PYTHON_VERSION` = `3.12`
3. Save and deploy. You get `https://<project>.pages.dev` (for example `remotejob-vn.pages.dev`).
4. Custom domain: in the Pages project → **Custom domains → Set up a custom domain** → `remotejob.nguyenquocdat.dev`.
   Because the `nguyenquocdat.dev` zone is already on Cloudflare DNS, Cloudflare creates the record for you:

   | Type | Name | Target | Proxy |
   | --- | --- | --- | --- |
   | CNAME | `remotejob` | `<project>.pages.dev` | Proxied (orange cloud) |

   If you create it by hand, use exactly that record. SSL is issued automatically.
5. `site/_headers` is copied to `dist/_headers`; Cloudflare Pages applies it (CSP, `nosniff`, cache headers).
   The CSP allows only same-origin scripts plus the SHA-256 hash of the tiny inline theme script, which the build
   fills in automatically.
6. `dist/404.html` is used automatically for unknown paths.

The daily `refresh.yml` workflow commits updated `data/`; each commit triggers a Cloudflare Pages rebuild.

## Option B: GitHub Pages

1. Repository **Settings → Pages → Source: GitHub Actions**.
2. Run `.github/workflows/pages.yml` manually (it is `workflow_dispatch` only by default).
3. Custom domain: Settings → Pages → Custom domain `remotejob.nguyenquocdat.dev`. DNS (on Cloudflare):
   `CNAME remotejob → quocdat029x.github.io` (DNS only / grey cloud while GitHub issues the certificate).
4. GitHub Pages ignores `_headers`, so the CSP and cache headers do not apply there; use a
   `<meta http-equiv="Content-Security-Policy">` or Cloudflare Transform Rules if needed.

## After the first deploy

- Check `https://remotejob.nguyenquocdat.dev/robots.txt` and `/sitemap.xml`.
- Follow the Search Console steps in `docs/SEO.md`.
