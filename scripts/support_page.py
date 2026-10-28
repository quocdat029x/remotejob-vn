"""Donate / support page. Vietnamese path /ung-ho/, English path /en/support/.

Payment details are the ones the site owner asked to publish: a self-hosted VietQR,
a self-hosted Binance Pay QR, and a plain Buy Me a Coffee link. No third-party
widget, no phone, no email.

Binance Pay lives in site.config.json under donate.binance:

    {
      "username": "hiddencat",
      "qr_image": "/assets/binance-pay.png",
      "pay_id": null,
      "usdt_addresses": [{"network": "TRC20", "address": "T..."}]
    }

pay_id is shown with a copy button only when it is a non-empty string.
usdt_addresses is rendered only when it contains at least one address, and each
row is labeled with its network (USDT (TRC20), USDT (BEP20), …) so a later
deposit address cannot be copied without the chain name.
"""
import html
import json
import os
import re

from site_text import T

# Language-relative paths. url_for() adds the /en prefix for English.
PATHS = {"vi": "/ung-ho/", "en": "/support/"}
BMC_URL = "https://buymeacoffee.com/quocdat0292"
ACCOUNT_NAME = "NGUYEN QUOC DAT"
ACCOUNT_DISPLAY = "8888 6897 979"
ACCOUNT_COPY = "88886897979"
BANK = "TPBank"
# Square crop of the VietQR symbol only (version 12, 65 modules) plus a quiet
# zone of about 4 modules. The framed TPBank/Napas poster was 887×1150.
QR_W, QR_H = 683, 683
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

e = html.escape
_ASSET_PNG = re.compile(r"/assets/[A-Za-z0-9._/-]+\.png")
_USERNAME = re.compile(r"[A-Za-z0-9_.-]{2,32}")
_PAY_ID = re.compile(r"[A-Za-z0-9]{4,64}")
_NETWORK = re.compile(r"[A-Za-z0-9-]{2,16}")
_ADDRESS = re.compile(r"[A-Za-z0-9]{16,128}")


def url_for(lang, path):
    """Same rule as the site generator: English pages live under /en."""
    return path if lang == "vi" else "/en" + path


def _load_donate():
    with open(os.path.join(ROOT, "site.config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    donate = cfg.get("donate")
    return donate if isinstance(donate, dict) else {}


def _binance(donate):
    """Normalized Binance Pay block, or None when the QR cannot be shown locally."""
    raw = (donate or {}).get("binance")
    if not isinstance(raw, dict):
        return None
    username = str(raw.get("username") or "").strip()
    qr = str(raw.get("qr_image") or "").strip()
    if not _USERNAME.fullmatch(username) or not _ASSET_PNG.fullmatch(qr) or ".." in qr:
        return None
    pay_id = raw.get("pay_id")
    pay_id = pay_id.strip() if isinstance(pay_id, str) else ""
    if pay_id and not _PAY_ID.fullmatch(pay_id):
        pay_id = ""
    addresses = []
    for item in raw.get("usdt_addresses") or []:
        if not isinstance(item, dict):
            continue
        network = str(item.get("network") or "").strip()
        address = str(item.get("address") or "").strip()
        if not _NETWORK.fullmatch(network) or not _ADDRESS.fullmatch(address):
            continue
        addresses.append({"network": network.upper(), "address": address})
    return {"username": username, "qr_image": qr, "pay_id": pay_id, "usdt_addresses": addresses}


def _png_size(url_path):
    name = os.path.basename(url_path)
    with open(os.path.join(ROOT, "site", "assets", name), "rb") as fh:
        header = fh.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"not a png: {name}")
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def _webp_url(png_url):
    if not png_url.endswith(".png"):
        return ""
    name = os.path.basename(png_url)[:-4] + ".webp"
    if os.path.isfile(os.path.join(ROOT, "site", "assets", name)):
        return "/assets/" + name
    return ""


def _copy_button(value, label, copied):
    return (
        f'<button type="button" class="btn copy-acct" data-copy="{e(value)}" '
        f'data-copied="{e(copied)}" aria-live="polite">{e(label)}</button>'
    )


def _fill(template, **values):
    out = template
    for key, value in values.items():
        out = out.replace("{" + key + "}", value)
    return out


def _qr_card(lang):
    t = T[lang]
    # The Vietnamese page leads with the QR, so that image can be the LCP element.
    # English leads with Buy Me a Coffee; the QR sits lower, especially on a phone.
    loading = ' loading="lazy"' if lang == "en" else ' fetchpriority="high"'
    return f"""<section class="card qr-card" id="vietqr" aria-labelledby="vietqr-h">
<h2 id="vietqr-h">{e(t["support_qr_h"])}</h2>
<p class="donate-intro">{e(t["support_qr_p"])}</p>
<div class="qr-frame"><picture>
<source srcset="/assets/vietqr-tpbank.webp" type="image/webp">
<img src="/assets/vietqr-tpbank.png" width="{QR_W}" height="{QR_H}" alt="{e(t["support_qr_alt"])}" decoding="async"{loading}>
</picture>
<p class="qr-badge">{e(t["support_qr_badge"])}</p></div>
<dl class="acct-facts">
<div><dt>{e(t["support_name_l"])}</dt><dd>{ACCOUNT_NAME}</dd></div>
<div><dt>{e(t["support_number_l"])}</dt><dd class="acct-row"><span class="acct">{ACCOUNT_DISPLAY}</span> {_copy_button(ACCOUNT_COPY, t["support_copy"], t["support_copied"])}</dd></div>
<div><dt>{e(t["support_bank_l"])}</dt><dd>{BANK}</dd></div>
</dl>
<p class="qr-mobile-note muted">{e(t["support_mobile"])}</p>
</section>"""


def _binance_card(lang, block):
    t = T[lang]
    username = block["username"]
    width, height = _png_size(block["qr_image"])
    webp = _webp_url(block["qr_image"])
    source = f'<source srcset="{e(webp)}" type="image/webp">' if webp else ""
    alt = _fill(t["support_binance_alt"], username=username)
    rows = (
        f'<div><dt>{e(t["support_binance_user_l"])}</dt>'
        f'<dd class="acct-row"><span class="acct">{e(username)}</span> '
        f'{_copy_button(username, t["support_copy"], t["support_copied"])}</dd></div>'
    )
    if block["pay_id"]:
        rows += (
            f'<div><dt>{e(t["support_binance_payid_l"])}</dt>'
            f'<dd class="acct-row"><span class="acct">{e(block["pay_id"])}</span> '
            f'{_copy_button(block["pay_id"], t["support_copy"], t["support_copied"])}</dd></div>'
        )
    usdt = ""
    if block["usdt_addresses"]:
        addr_rows = []
        for item in block["usdt_addresses"]:
            label = _fill(t["support_usdt_l"], network=item["network"])
            addr_rows.append(
                f'<div><dt>{e(label)}</dt>'
                f'<dd class="acct-row"><span class="acct usdt-addr">{e(item["address"])}</span> '
                f'{_copy_button(item["address"], t["support_copy"], t["support_copied"])}</dd></div>'
            )
        usdt = (
            f'\n<div class="usdt-block"><h3>{e(t["support_usdt_h"])}</h3>'
            f'<p class="muted">{e(t["support_usdt_p"])}</p>'
            f'<dl class="acct-facts">{"".join(addr_rows)}</dl></div>'
        )
    instruction = _fill(t["support_binance_p"], username=username)
    return f"""<section class="card qr-card binance-card" id="binance" aria-labelledby="binance-h">
<h2 id="binance-h">{e(t["support_binance_h"])}</h2>
<p class="donate-intro">{e(instruction)}</p>
<div class="qr-frame"><picture>
{source}
<img src="{e(block["qr_image"])}" width="{width}" height="{height}" alt="{e(alt)}" decoding="async" loading="lazy">
</picture></div>
<dl class="acct-facts">
{rows}
</dl>
<p class="binance-free">{e(t["support_binance_free"])}</p>{usdt}
</section>"""


def _bmc_card(lang):
    t = T[lang]
    return f"""<section class="card bmc-card" id="international" aria-labelledby="bmc-h">
<h2 id="bmc-h">{e(t["support_bmc_h"])}</h2>
<p class="donate-intro">{e(t["support_bmc_p"])}</p>
<ul class="bmc-points">
<li>{e(t["support_bmc_li1"])}</li>
<li>{e(t["support_bmc_li2"])}</li>
</ul>
<p class="bmc-action"><a class="btn bmc-btn" href="{BMC_URL}" rel="noopener" target="_blank"><span aria-hidden="true">☕</span> {e(t["support_bmc_btn"])}</a></p>
</section>"""


def _cards(lang, donate):
    """Card order follows the audience. Binance sits between the local and card options."""
    cards = [_qr_card(lang), _bmc_card(lang)]
    block = _binance(donate)
    if block:
        # Vietnamese: VietQR, Binance Pay, Buy Me a Coffee.
        # English: Buy Me a Coffee, Binance Pay, VietQR.
        cards.insert(1, _binance_card(lang, block))
    if lang != "vi":
        cards.reverse()
    return "".join(cards)


def body(lang, repo, donate=None):
    """Full main-column HTML. Card order follows the audience of that language."""
    t = T[lang]
    donate = _load_donate() if donate is None else donate
    home = url_for(lang, "/")
    contrib = e(repo.rstrip("/")) + "/blob/main/CONTRIBUTING.md"
    return f"""<div class="pagehead"><h1>{e(t["support_h1"])}</h1><p class="lead">{e(t["support_lead"])}</p></div>
<div class="donate-grid">{_cards(lang, donate)}</div>
<section class="other-help"><h2>{e(t["support_other_h"])}</h2>
<ul>
<li>{e(t["support_share"])} <a href="{home}">RemoteJob VN</a></li>
<li><a href="{contrib}" rel="noopener">{e(t["support_pr"])}</a></li>
</ul></section>"""


# Sidebar thumbnail. The file is square; 160×160 keeps the rail compact.
THUMB_W, THUMB_H = 160, 160


def sidebar_card(lang, donate=None):
    """Compact donate card for the sidebar column. English leads with Buy Me a Coffee.

    Binance Pay is a text link to the donate page anchor, not a third QR, so the
    sticky rail stays about the same height.
    """
    t = T[lang]
    href = url_for(lang, PATHS[lang])
    qr = f"""<div class="side-qr"><picture>
<source srcset="/assets/vietqr-tpbank.webp" type="image/webp">
<img src="/assets/vietqr-tpbank.png" width="{THUMB_W}" height="{THUMB_H}" alt="{e(t["support_qr_alt"])}" decoding="async" loading="lazy">
</picture></div>"""
    acct = (
        f'<div class="side-acct"><span class="acct">{ACCOUNT_DISPLAY}</span> '
        f'{_copy_button(ACCOUNT_COPY, t["support_copy"], t["support_copied"])}</div>'
    )
    bmc = (
        f'<a class="btn bmc-btn" href="{BMC_URL}" rel="noopener" target="_blank">'
        f'<span aria-hidden="true">☕</span> {e(t["support_bmc_btn"])}</a>'
    )
    parts = (qr, acct, bmc) if lang == "vi" else (bmc, qr, acct)
    donate = _load_donate() if donate is None else donate
    binance_link = ""
    if _binance(donate):
        binance_link = f'<a class="side-binance" href="{href}#binance">{e(t["support_side_binance"])}</a>'
    more = (
        f'<div class="side-actions">{binance_link}'
        f'<a class="side-more" href="{href}">{e(t["support_more"])}</a></div>'
    )
    return (
        f'<section class="side-support" aria-labelledby="side-support-h">'
        f'<h2 id="side-support-h">{e(t["support_side_h"])}</h2>'
        f'<p>{e(t["support_side_p"])}</p>'
        f'<div class="side-support-body">{"".join(parts)}</div>'
        f'{more}</section>'
    )


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
