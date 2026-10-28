"""Donate / support page. Vietnamese path /ung-ho/, English path /en/support/.

Payment details are the ones the site owner asked to publish: a self-hosted VietQR
and a plain Buy Me a Coffee link. No third-party widget, no phone, no email.
"""
import html

from site_text import T

# Language-relative paths. url_for() adds the /en prefix for English.
PATHS = {"vi": "/ung-ho/", "en": "/support/"}
BMC_URL = "https://buymeacoffee.com/quocdat0292"
ACCOUNT_NAME = "NGUYEN QUOC DAT"
ACCOUNT_DISPLAY = "8888 6897 979"
ACCOUNT_COPY = "88886897979"
BANK = "TPBank"
QR_W, QR_H = 887, 1150

e = html.escape


def url_for(lang, path):
    """Same rule as the site generator: English pages live under /en."""
    return path if lang == "vi" else "/en" + path


def _qr_card(lang):
    t = T[lang]
    # The Vietnamese page leads with the QR, so that image can be the LCP element.
    # English leads with Buy Me a Coffee; the QR sits lower, especially on a phone.
    loading = ' loading="lazy"' if lang == "en" else ' fetchpriority="high"'
    return f"""<section class="card qr-card" id="vietqr" aria-labelledby="vietqr-h">
<h2 id="vietqr-h">{e(t["support_qr_h"])}</h2>
<p>{e(t["support_qr_p"])}</p>
<div class="qr-frame"><picture>
<source srcset="/assets/vietqr-tpbank.webp" type="image/webp">
<img src="/assets/vietqr-tpbank.png" width="{QR_W}" height="{QR_H}" alt="{e(t["support_qr_alt"])}" decoding="async"{loading}>
</picture></div>
<dl class="acct-facts">
<div><dt>{e(t["support_name_l"])}</dt><dd>{ACCOUNT_NAME}</dd></div>
<div><dt>{e(t["support_number_l"])}</dt><dd class="acct-row"><span class="acct">{ACCOUNT_DISPLAY}</span> <button type="button" class="btn copy-acct" data-copy="{ACCOUNT_COPY}" data-copied="{e(t["support_copied"])}" aria-live="polite">{e(t["support_copy"])}</button></dd></div>
<div><dt>{e(t["support_bank_l"])}</dt><dd>{BANK}</dd></div>
</dl>
<p class="qr-mobile-note muted">{e(t["support_mobile"])}</p>
</section>"""


def _bmc_card(lang):
    t = T[lang]
    return f"""<section class="card bmc-card" id="international" aria-labelledby="bmc-h">
<h2 id="bmc-h">{e(t["support_bmc_h"])}</h2>
<p>{e(t["support_bmc_p"])}</p>
<p><a class="btn bmc-btn" href="{BMC_URL}" rel="noopener" target="_blank"><span aria-hidden="true">☕</span> {e(t["support_bmc_btn"])}</a></p>
</section>"""


def body(lang, repo):
    """Full main-column HTML. Card order follows the audience of that language."""
    t = T[lang]
    cards = (_qr_card(lang), _bmc_card(lang)) if lang == "vi" else (_bmc_card(lang), _qr_card(lang))
    home = url_for(lang, "/")
    contrib = e(repo.rstrip("/")) + "/blob/main/CONTRIBUTING.md"
    return f"""<div class="pagehead"><h1>{e(t["support_h1"])}</h1><p class="lead">{e(t["support_lead"])}</p></div>
<div class="donate-grid">{cards[0]}{cards[1]}</div>
<section class="other-help"><h2>{e(t["support_other_h"])}</h2>
<ul>
<li>{e(t["support_share"])} <a href="{home}">RemoteJob VN</a></li>
<li><a href="{contrib}" rel="noopener">{e(t["support_pr"])}</a></li>
</ul></section>"""


def nudge(lang):
    """Small in-flow note. Hidden before paint when localStorage says it was dismissed."""
    t = T[lang]
    href = url_for(lang, PATHS[lang])
    return (
        f'<aside class="support-nudge" data-support-nudge>'
        f'<p>{e(t["support_nudge"])} <a href="{href}">{e(t["nav_support"])}</a></p>'
        f'<button type="button" class="dismiss" data-support-dismiss aria-label="{e(t["support_dismiss"])}">×</button>'
        f'</aside>'
    )
