"""Google AdSense wiring that stays off until site.config.json has a publisher id.

Nothing in this module contacts Google. The static generator calls it while
rendering dist/. An empty adsense_client leaves the HTML, ads.txt and CSP alone.
"""
import base64
import hashlib
import html
import re

# Hosts Google documents for AdSense ad code, Auto ads and the certified CMP
# (Funding Choices, loaded by Privacy & messaging). Applied only when a publisher id is set.
AD_HOSTS = {
    "script-src": [
        "https://pagead2.googlesyndication.com",
        "https://partner.googleadservices.com",
        "https://www.googletagservices.com",
        "https://adservice.google.com",
        "https://tpc.googlesyndication.com",
        "https://fundingchoicesmessages.google.com",
        "https://www.google.com",
        "https://www.gstatic.com",
        "https://googleads.g.doubleclick.net",
        "https://ep1.adtrafficquality.google",
        "https://ep2.adtrafficquality.google",
    ],
    "img-src": [
        "https://pagead2.googlesyndication.com",
        "https://googleads.g.doubleclick.net",
        "https://tpc.googlesyndication.com",
        "https://www.google.com",
        "https://www.gstatic.com",
        "https://fundingchoicesmessages.google.com",
        "https://www.googleadservices.com",
    ],
    "frame-src": [
        "https://googleads.g.doubleclick.net",
        "https://tpc.googlesyndication.com",
        "https://pagead2.googlesyndication.com",
        "https://www.google.com",
        "https://fundingchoicesmessages.google.com",
        "https://www.googletagservices.com",
        "https://adservice.google.com",
        "https://ep1.adtrafficquality.google",
        "https://ep2.adtrafficquality.google",
    ],
    "connect-src": [
        "https://pagead2.googlesyndication.com",
        "https://googleads.g.doubleclick.net",
        "https://adservice.google.com",
        "https://ep1.adtrafficquality.google",
        "https://ep2.adtrafficquality.google",
        "https://csi.gstatic.com",
        "https://fundingchoicesmessages.google.com",
        "https://www.google.com",
        "https://www.gstatic.com",
    ],
}

# Fixed slots. The ins element itself has this size, so the layout does not shift
# when the creative arrives. Sidebar matches the existing 300×250 house box.
SIZES = {"sidebar": (300, 250), "native": (320, 100), "bottom": (320, 100)}

# Runs at the end of body. Skips the desktop sidebar when it is display:none
# (under 1100px) so a hidden unit is not requested on mobile.
PUSH_JS = (
    "document.querySelectorAll('ins.adsbygoogle').forEach(function(el){"
    "var side=el.closest('.side');"
    "if(side&&getComputedStyle(side).display==='none')return;"
    "(window.adsbygoogle=window.adsbygoogle||[]).push({});"
    "});"
)

# Appended to the stylesheet only when a publisher id is set, so the house-ad
# CSS (and its hash) stays byte-for-byte the same while AdSense is unconfigured.
EXTRA_CSS = (
    ".slot.adsense{height:auto;align-items:flex-start}"
    ".slot-side.adsense{width:300px;min-height:292px}"
    ".slot-native.adsense,.slot-bottom.adsense{display:block;min-height:132px}"
)


def client_id(cfg):
    raw = str((cfg or {}).get("adsense_client") or "").strip()
    return raw if re.fullmatch(r"ca-pub-\d{10,20}", raw) else ""


def slot_id(cfg, name):
    raw = str(((cfg or {}).get("adsense_slots") or {}).get(name) or "").strip()
    return raw if re.fullmatch(r"\d{6,12}", raw) else ""


def publisher_id(client):
    """ca-pub-123 -> pub-123, the form ads.txt uses."""
    return "pub-" + client.split("pub-", 1)[1]


def ads_txt(client):
    return f"google.com, {publisher_id(client)}, DIRECT, f08c47fec0942fa0\n"


def meta_tag(client):
    return f'<meta name="google-adsense-account" content="{html.escape(client, quote=True)}">'


def loader_tag(client):
    src = html.escape(
        "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + client,
        quote=True,
    )
    return f'<script async src="{src}" crossorigin="anonymous"></script>'


def push_tag():
    return f"<script>{PUSH_JS}</script>"


def push_sha():
    digest = hashlib.sha256(PUSH_JS.encode()).digest()
    return "sha256-" + base64.b64encode(digest).decode()


def ins_html(client, slot, width, height):
    return (
        f'<ins class="adsbygoogle" style="display:inline-block;width:{width}px;height:{height}px" '
        f'data-ad-client="{html.escape(client, quote=True)}" '
        f'data-ad-slot="{html.escape(slot, quote=True)}"></ins>'
    )


def widen_csp(headers_text, extra_script_tokens):
    """Add AdSense hosts to the CSP line. Returns the original text when there is nothing to add."""
    if not extra_script_tokens and not AD_HOSTS:
        return headers_text

    def widen_policy(policy):
        parts = [p.strip() for p in policy.split(";") if p.strip()]
        seen = set()
        out = []
        for part in parts:
            name = part.split()[0]
            seen.add(name)
            hosts = list(AD_HOSTS.get(name, []))
            if name == "script-src":
                hosts = list(extra_script_tokens) + hosts
            tokens = part.split()
            for host in hosts:
                if host not in tokens:
                    tokens.append(host)
            out.append(" ".join(tokens))
        for name, hosts in AD_HOSTS.items():
            if name not in seen:
                out.append(" ".join([name] + hosts))
        return "; ".join(out)

    lines = []
    for line in headers_text.splitlines(keepends=True):
        body = line.strip()
        prefix = "Content-Security-Policy:"
        if body.startswith(prefix):
            indent = line[: len(line) - len(line.lstrip())]
            nl = "\n" if line.endswith("\n") else ""
            lines.append(indent + prefix + " " + widen_policy(body[len(prefix):].strip()) + nl)
        else:
            lines.append(line)
    return "".join(lines)
