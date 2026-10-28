# Design system

Source: `site/assets/style.css` (minified and fingerprinted to `dist/assets/style.<hash>.css` by the build).

- **Tokens** (CSS custom properties): colors (`--bg`, `--surface`, `--text`, `--text-2`, `--text-3`, `--brand`,
  `--accent`, `--ok`, `--warn`, `--sponsor`, `--aff` + `-soft` variants), spacing scale `--s1…--s8`,
  radii `--r-sm/md/lg/pill`, shadows `--shadow-1/2`, type scale `--fs-xs…--fs-3xl`, system font stack.
- **Contrast**: all text/background pairs meet WCAG AA (≥ 4.5:1) in light and dark themes.
- **Themes**: light and dark via `prefers-color-scheme`; the header toggle stores a choice in `localStorage` and a
  tiny inline script in `<head>` applies it before first paint (no flash). Its SHA-256 hash is added to the CSP.
- **Brand**: SVG logo + "RemoteJob VN" wordmark, `favicon.svg`, `favicon-32.png`, `icon-192/512.png`,
  `apple-touch-icon.png`, `site.webmanifest`, 1200×630 `og-default.png` (generated with Pillow, cached in `site/`).
- **Components**: hero with search, chips, badges (region, remote mode, salary, last checked), an accent
  "Ủng hộ" / "Support" nav button, a dismissible in-flow support note, company cards with
  initials avatars (no hotlinked logos), job cards, detail header, fact panel, sticky filter bar, pager with gaps,
  "show more" (JS) on top of real pagination (no JS), empty states, 404, footer with About / Contribute /
  Affiliate disclosure / data license / GitHub.
- **Labeled commercial slots**: `.slot` (Ad), `.featured` + `.label.sp` (Sponsored), `.tool-card` + `.label.aff` (Affiliate).
  The outbound-click interstitial (`.ix`) is created in the DOM only after an apply click, so it is outside the first paint.
- **Accessibility**: skip link, visible focus rings, keyboard-only navigation, `aria-current`, labeled forms,
  `prefers-reduced-motion`, 44 px touch targets.
- **Responsive**: tested at 360/390, 768 and 1280 px; print stylesheet hides navigation, filters and ads and prints link URLs.
- **Budgets**: CSS < 30 KB, JS < 20 KB, no frameworks, no web fonts. Those budgets cover files this repo ships. Cloudflare Web Analytics is not one of them: Pages injects that cookieless beacon, and the CSP allows only its script and connect hosts.
