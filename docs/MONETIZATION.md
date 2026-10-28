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
- No popups, interstitials, sticky overlays, autoplay or ad scripts. Space is reserved to avoid layout shift.
- To sell a slot, replace the text/URL in `data/ads.json` (static house ad). If an ad network is ever added,
  update the CSP in `site/_headers` and the privacy text on `/gioi-thieu/` first.
- `enabled: false` removes all slots.

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
