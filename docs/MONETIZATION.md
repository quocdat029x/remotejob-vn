# Monetization

The site is free for job seekers. Revenue options are wired in as **placeholders** that never load third-party
code, never track users and never block content. Everything is data-driven and can be turned off.

## Ad slots (`data/ads.json`)

```json
{"enabled": true, "native_every": 12, "sidebar": {"vi": "...", "en": "...", "url": "/quang-cao/"}, "native": {...}}
```

- **Desktop sidebar** (≥1100 px): one 300×250 reserved box on home, company directory, jobs and role pages.
  Hidden on mobile.
- **Native card**: at most one card every 10–15 rows (`native_every`, clamped to 10–15) in company and job lists,
  styled like a list card but labeled "Quảng cáo / Ad". Hidden while the user is filtering.
- **Company pages**: no ad at the top; one labeled slot at the very bottom only.
- No ad on page load, no sticky overlay, no autoplay, no ad-network script. List slots reserve their size
  so they do not shift layout.
- To sell a slot, replace the text/URL in `data/ads.json` (static house ad). If an ad network is ever added,
  update the CSP in `site/_headers` and the privacy text on `/gioi-thieu/` first.
- `enabled: false` removes the sidebar, native and company-page slots. It does not by itself turn off the
  outbound-click interstitial; that has its own flag (below).

## Outbound-click interstitial

Shown only after a visitor clicks an outbound apply link (`data-out="job"` on the job page, the
"Xem tin gốc & ứng tuyển" / "View original & apply" button). It is not injected on page load and not
shown when someone lands from search.

- **Progressive enhancement.** The control is a normal `<a href="…">` to the employer. With JavaScript
  off, or for a crawler, the browser follows that href. Modified clicks (new tab) are not intercepted.
- **Frequency cap**, stored on the device in `localStorage` (falls back to `sessionStorage` if
  `localStorage` throws). Keys `rjvn-out-n` (outbound click count) and `rjvn-out-at` (last time the
  dialog was shown). The dialog opens on every 3rd plain click, and never more than once per 10 minutes.
  Nothing is sent to a server.
- **Creative** comes from `data/ads.json` → `interstitial` (house/sponsored placeholder by default:
  title, body, internal CTA, 5 second countdown). The visible label is `Quảng cáo / Advertisement`.
- **Controls.** A visible close button, a "Continue to job" / "Tiếp tục tới tin tuyển dụng" button, and
  an automatic continue after `seconds` (default 5, clamped to 3–15). Escape does the same as close:
  dismisses the dialog and continues to the job. Focus is trapped (`role="dialog"`, `aria-modal`).
- **Bots.** The script does not open the dialog when `navigator.webdriver` is true or the user agent
  looks like a crawler (Googlebot, Bingbot, HeadlessChrome, and similar).
- **Layout.** The dialog node is created on click. It is not in the HTML, so it does not affect LCP or CLS.
- **Off switch.** `"outbound_interstitial": false` in `site.config.json` omits the config tag. The apply
  link is unchanged.

### Later: Google AdSense vignette instead of this dialog

This repository does not load AdSense or any other ad-network script. To swap the custom interstitial
for an AdSense Auto ads vignette later:

1. Set `"outbound_interstitial": false` in `site.config.json` so the custom dialog is not emitted.
   Leave the apply control as a normal `<a href>`. `data-out="job"` can stay; with the flag off, the
   script does not intercept it.
2. In a separate change, add the AdSense loader only after editing `site/_headers` (`script-src`,
   `frame-src`, `img-src`, `connect-src`) and the privacy copy on `/gioi-thieu/` (third-party script
   and cookies). Do not claim "no third-party scripts" in the same release.
3. In the AdSense UI, enable Auto ads and the vignette format. Vignettes are Google's interstitial and
   are triggered by AdSense between page views, not by `site/assets/app.js`.
4. Do not run the custom dialog and an AdSense vignette together.
5. There is no publisher id and no `adsbygoogle` snippet in this repo. Adding one is a deliberate
   follow-up, not a default.

## Affiliate page `/cong-cu/` (`data/affiliates.json`)

Five categories: VPS/hosting, courses & certifications, home-office gear, international payment tools, coworking.
Every link:

- is rendered with a visible **"Affiliate"** label,
- has `rel="sponsored nofollow noopener"`,
- appears under an affiliate disclosure (`#disclosure`, linked from the footer).

All URLs are `https://example.com/affiliate/...` placeholders. Replace them only after joining a real program.

## Featured / sponsored jobs (`data/sponsored.json`)

```json
{"max_featured": 3, "items": []}
```

- Empty by default; see `docs/sponsored.example.json` and `schema/sponsored.schema.json`.
- Active items (`starts` ≤ today ≤ `expires`) appear at the top of the home page and job list, at most
  `max_featured` (0–3), with a distinct border and a **"Tài trợ / Sponsored"** label, links use `rel="sponsored nofollow noopener"`.
- Sponsored items do not get JobPosting JSON-LD and are not mixed into organic results.
- `/quang-cao/` explains the options to employers.
