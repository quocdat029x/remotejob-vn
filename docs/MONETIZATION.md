# Monetization

The site is free for job seekers. Optional donations (VietQR and Buy Me a Coffee on `/ung-ho/` and `/en/support/`)
are plain links and a self-hosted QR image, with no third-party widget. Revenue options are wired in as **placeholders** that never load third-party
code, never track users and never block content. Everything is data-driven and can be turned off.

## Ad slots (`data/ads.json`)

```json
{"enabled": true, "native_every": 12, "sidebar": {"vi": "...", "en": "...", "url": "/quang-cao/"}, "native": {...}}
```

- **Desktop sidebar** (≥1100 px): one 300×250 reserved box on home, company directory, company pages,
  job lists, job pages and role pages. A compact support card (VietQR thumbnail, account copy, Buy Me a Coffee)
  sits under that box. The pair is `position: sticky` when it fits the viewport, and returns to normal flow
  when it is taller than the screen so it does not cover the footer. Hidden ad on mobile.
  On a single column the support card is shown once below the content only when that page has no dismissible
  support note.
- **Native card**: at most one card every 10–15 rows (`native_every`, clamped to 10–15) in company and job lists,
  styled like a list card but labeled "Quảng cáo / Ad". Hidden while the user is filtering.
- **Company pages**: no ad above the company name; the sidebar column matches the other pages, plus one labeled
  slot at the very bottom.
- List slots reserve their size so they do not shift layout. With no AdSense slot id they stay house ads.
  The async AdSense loader is separate and only present when `adsense_client` is set (see below).
- To sell a slot, replace the text/URL in `data/ads.json` (static house ad) or paste an AdSense slot id.
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

The apply-click dialog is **house content only**. It is never an AdSense unit. AdSense policy does
not allow ads inside a pop-up we build. Do not put `adsbygoogle` markup in `site/assets/app.js`.
Leave `"outbound_interstitial": true` if you want that house dialog. Auto ads vignettes, if enabled
in the AdSense account, are Google's own between-page format and are separate from this dialog.
Do not also turn the custom dialog into an ad-network interstitial.

## Google AdSense

`site.config.json` holds `adsense_client` (a `ca-pub-` id) and optional `adsense_slots`
(`sidebar`, `native`, `bottom`, numeric slot ids). The publisher id in this repo is
`ca-pub-7257034493587502`. Slot ids are empty, so the reserved sidebar, native, and company-page
slots stay house ads.

When `adsense_client` matches `ca-pub-` plus digits, the build:

- writes `/ads.txt` as `google.com, pub-7257034493587502, DIRECT, f08c47fec0942fa0`
- adds `<meta name="google-adsense-account" content="ca-pub-...">`
- adds the async loader
  `<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-..." crossorigin="anonymous"></script>`
  on every page (verification and Auto ads; it does not block HTML parsing)
- widens `dist/_headers` for the Google ad and Funding Choices hosts (`script-src`, `img-src`,
  `frame-src`, `connect-src`)
- renders a fixed-size `<ins class="adsbygoogle">` **only** for a slot that has an id
  (sidebar 300×250, native and bottom 320×100). The desktop sidebar unit is not requested when
  the sidebar is `display: none` (under 1100px).

When the client id is empty, none of that is emitted and the CSP matches `site/_headers`.

### What you still do in the AdSense account

1. Finish site review. The publisher id is already in `site.config.json`; merging this change
   publishes `ads.txt`, the meta tag, and the loader.
2. Ads → Auto ads: turn **vignette** on. Turn **anchor** ads and other mobile overlays off.
   There is no reliable page-level switch for that in the snippet; it is an account setting.
3. Privacy & messaging: enable Google's certified CMP for the EEA and the UK. Do not add a
   cookie banner in this repository.
4. Optional, after review: create display units and paste the numeric slot ids into
   `adsense_slots`. Until then the reserved boxes stay house ads. Do not put a unit in the
   apply-click dialog.

## Affiliate page `/cong-cu/` (`data/affiliates.json`)

Sections are ordered for the audience, which includes non-engineers (sales, marketing, support and operations are a large share of the jobs):

1. Receiving international payments (Wise, Payoneer)
2. Courses, certifications and English (Coursera, Udemy, KodeKloud, English-learning apps, a CV tool)
3. Home-office gear (intended program: Shopee Affiliate via ACCESSTRADE Vietnam)
4. VPS and hosting for engineers (DigitalOcean, Vultr, Hostinger)
5. Coworking in Ho Chi Minh City, Hanoi and Da Nang

Every link:

- is rendered with a visible **"Affiliate"** label,
- has `rel="sponsored nofollow noopener"`,
- appears under an affiliate disclosure (`#disclosure`, linked from the footer).

`url` is a non-affiliate placeholder: the vendor's public homepage, or `https://example.com/affiliate/<slot>` when there is no single product page. Replace `url` only when a program is joined. Do not add a script or a tracking pixel.

## Featured / sponsored jobs (`data/sponsored.json`)

```json
{"max_featured": 3, "items": []}
```

- Empty by default; see `docs/sponsored.example.json` and `schema/sponsored.schema.json`.
- Active items (`starts` ≤ today ≤ `expires`) appear at the top of the home page and job list, at most
  `max_featured` (0–3), with a distinct border and a **"Tài trợ / Sponsored"** label, links use `rel="sponsored nofollow noopener"`.
- Sponsored items do not get JobPosting JSON-LD and are not mixed into organic results.
- `/dang-tin/` (English `/en/dang-tin/`) explains the offer to employers: labeled Sponsored, at most 3 at a time, remote roles open to people in Vietnam only. Pricing is the placeholder **Pricing: contact** / **Giá: liên hệ**. The contact path is a GitHub issue (`post-a-job.yml`), not an email address or phone number.
- `/quang-cao/` summarizes the same options and links to that page.
