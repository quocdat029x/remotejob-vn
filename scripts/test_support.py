#!/usr/bin/env python3
"""Support page: VietQR + Buy Me a Coffee, hreflang, and the soft ask."""
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import build
import llms
import support_page

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


class SupportPageTests(unittest.TestCase):
    def test_paths_use_translated_slugs(self):
        self.assertEqual(support_page.PATHS["vi"], "/ung-ho/")
        self.assertEqual(support_page.PATHS["en"], "/support/")

    def test_vietnamese_page_leads_with_a_scannable_vietqr(self):
        html = support_page.body("vi", repo="https://github.com/quocdat029x/remotejob-vn")
        self.assertLess(html.index("Trong nước: quét VietQR"), html.index("Quốc tế: Buy Me a Coffee"))
        self.assertIn("NGUYEN QUOC DAT", html)
        self.assertIn("8888 6897 979", html)
        self.assertIn('data-copy="88886897979"', html)
        self.assertIn("TPBank", html)
        self.assertIn("Napas 247", html)
        self.assertIn('href="https://buymeacoffee.com/quocdat0292"', html)
        self.assertIn('rel="noopener"', html)
        self.assertIn('target="_blank"', html)
        self.assertNotIn("bmc-button", html)
        self.assertNotIn("<script", html)
        self.assertIn('width="683"', html)
        self.assertIn('height="683"', html)
        self.assertIn("VietQR · Napas 247 · TPBank", html)
        self.assertIn('class="qr-badge"', html)
        self.assertIn('srcset="/assets/vietqr-tpbank.webp"', html)
        self.assertIn('src="/assets/vietqr-tpbank.png"', html)
        viet = html.split('id="vietqr"', 1)[1].split("</section>", 1)[0]
        self.assertNotIn('loading="lazy"', viet)
        self.assertIn('fetchpriority="high"', viet)
        self.assertIn("chụp màn hình", html)
        self.assertIn("pull request", html)
        self.assertIn("CONTRIBUTING.md", html)
        self.assertIsNone(EMAIL.search(html))
        self.assertNotIn("mailto:", html)

    def test_english_page_leads_with_buy_me_a_coffee(self):
        html = support_page.body("en", repo="https://github.com/quocdat029x/remotejob-vn")
        self.assertLess(html.index("Buy Me a Coffee"), html.index("VietQR"))
        self.assertIn("screenshot", html.lower())
        self.assertIn('loading="lazy"', html)
        self.assertIn('width="683"', html)
        self.assertIn('height="683"', html)
        self.assertIn("VietQR · Napas 247 · TPBank", html)
        self.assertIn("NGUYEN QUOC DAT", html)
        self.assertIn('data-copy="88886897979"', html)

    def test_llms_txt_lists_both_language_urls(self):
        text = llms.llms_txt(
            "https://remotejob.nguyenquocdat.dev",
            "https://github.com/quocdat029x/remotejob-vn",
            [("devops", "DevOps", "DevOps")],
        )
        self.assertIn("https://remotejob.nguyenquocdat.dev/ung-ho/", text)
        self.assertIn("https://remotejob.nguyenquocdat.dev/en/support/", text)

    def test_header_is_an_accent_button_with_hreflang(self):
        html = build.page(
            "vi", "/ung-ho/", "Ủng hộ", "desc", "<p>body</p>", alternates=support_page.PATHS,
        )
        self.assertIn('class="nav-support"', html)
        self.assertIn("Ủng hộ ☕", html)
        self.assertIn('href="/ung-ho/"', html)
        self.assertIn('hreflang="en" href="https://remotejob.nguyenquocdat.dev/en/support/"', html)
        self.assertIn('hreflang="en" lang="en"', html)
        self.assertIn('href="/en/support/"', html)
        self.assertRegex(html, r'<a class="nav-support" href="/ung-ho/" aria-current="page">')
        self.assertIn('href="/ung-ho/"', html[html.index("<footer"):])

    def test_english_header_points_back_at_vietnamese(self):
        html = build.page(
            "en", "/support/", "Support", "desc", "<p>body</p>", alternates=support_page.PATHS,
        )
        self.assertIn('href="/en/support/"', html)
        self.assertIn('hreflang="vi" href="https://remotejob.nguyenquocdat.dev/ung-ho/"', html)
        self.assertRegex(html, r'<a class="nav-support" href="/en/support/" aria-current="page">Support</a>')

    def test_nudge_stays_in_normal_flow(self):
        html = support_page.nudge("vi")
        self.assertIn("support-nudge", html)
        self.assertIn('href="/ung-ho/"', html)
        self.assertIn("data-support-dismiss", html)
        self.assertNotIn("position:fixed", html)
        self.assertNotIn("position:sticky", html)

    def test_sidebar_card_is_compact_and_language_ordered(self):
        vi = support_page.sidebar_card("vi")
        self.assertIn("Ủng hộ RemoteJob VN ☕", vi)
        self.assertIn("Trang miễn phí. Ủng hộ giúp trang tiếp tục hoạt động.", vi)
        self.assertLess(vi.index("side-qr"), vi.index("bmc-btn"))
        self.assertIn('loading="lazy"', vi)
        self.assertIn('width="160"', vi)
        self.assertIn('height="160"', vi)
        self.assertIn('srcset="/assets/vietqr-tpbank.webp"', vi)
        self.assertIn('src="/assets/vietqr-tpbank.png"', vi)
        self.assertIn("8888 6897 979", vi)
        self.assertIn('data-copy="88886897979"', vi)
        self.assertIn('href="https://buymeacoffee.com/quocdat0292"', vi)
        self.assertIn('rel="noopener"', vi)
        self.assertIn('target="_blank"', vi)
        self.assertIn('href="/ung-ho/"', vi)
        self.assertIn('href="/ung-ho/#binance"', vi)
        self.assertIn("Binance Pay", vi)
        self.assertNotIn("/assets/binance-pay", vi)
        self.assertIn("Xem thêm", vi)
        self.assertNotIn("<script", vi)
        self.assertNotIn("bmc-button", vi)
        self.assertIsNone(EMAIL.search(vi))
        en = support_page.sidebar_card("en")
        self.assertIn("Support RemoteJob VN ☕", en)
        self.assertIn("The site is free. Donations keep it running.", en)
        self.assertLess(en.index("bmc-btn"), en.index("side-qr"))
        self.assertIn('href="/en/support/"', en)
        self.assertIn('href="/en/support/#binance"', en)
        self.assertIn("Binance Pay", en)
        self.assertNotIn("/assets/binance-pay", en)
        self.assertIn("See more", en)
        self.assertIn('loading="lazy"', en)

    def test_sidebar_rail_places_card_under_the_house_ad(self):
        import json
        with open(os.path.join(ROOT, "data", "ads.json"), encoding="utf-8") as fh:
            ads = json.load(fh)
        vi_ad = build.ad_sidebar("vi", ads)
        self.assertIn("Quảng cáo tại đây: tiếp cận kỹ sư remote ở Việt Nam.", vi_ad)
        self.assertIn(">Quảng cáo<", vi_ad)
        self.assertNotIn("Advertise here", vi_ad)
        self.assertIn("300 × 250", vi_ad)
        en_ad = build.ad_sidebar("en", ads)
        self.assertIn("Advertise here: reach remote engineers in Vietnam.", en_ad)
        self.assertIn(">Ad<", en_ad)
        forced = build.sidebar_house_text("vi", {"vi": "Advertise here: reach remote engineers in Vietnam.", "en": "Advertise here: reach remote engineers in Vietnam."})
        self.assertEqual(forced, "Quảng cáo tại đây: tiếp cận kỹ sư remote ở Việt Nam.")
        page = build.page("vi", "/viec-lam/example/", "T", "D", "<p>body</p>", aside=vi_ad)
        self.assertIn('class="rail"', page)
        self.assertLess(page.index("slot-side"), page.index("side-support"))
        self.assertIn("Ủng hộ RemoteJob VN ☕", page)
        self.assertNotIn("support-nudge", page)
        listed = build.page("vi", "/", "T", "D", support_page.nudge("vi") + "<p>body</p>", aside=vi_ad)
        self.assertIn("support-nudge", listed)
        self.assertIn("side-support", listed)
        en_page = build.page("en", "/cong-ty/acme/", "T", "D", "<p>body</p>", aside=en_ad)
        card = en_page[en_page.index("side-support"):]
        self.assertLess(card.index("bmc-btn"), card.index("side-qr"))
        bare = build.page("vi", "/gioi-thieu/", "T", "D", "<p>body</p>")
        self.assertNotIn("side-support", bare)

    def test_sidebar_css_sticks_only_when_it_fits(self):
        css_path = os.path.join(ROOT, "site", "assets", "style.css")
        js_path = os.path.join(ROOT, "site", "assets", "app.js")
        with open(css_path, encoding="utf-8") as fh:
            css = fh.read()
        with open(js_path, encoding="utf-8") as fh:
            js = fh.read()
        flat = css.replace("\n", "")
        self.assertIn(".rail{display:flex", flat)
        self.assertIn(".rail.is-tall{position:static}", flat)
        self.assertIn(".layout.with-aside:not(:has(.support-nudge)) .side-support", css)
        self.assertIn("max-height:720px", css)
        self.assertIn(".donate-grid{display:grid;gap:var(--s4);align-items:stretch}", flat)
        self.assertIn(".qr-frame{background:#fff", flat)
        self.assertIn(".side-qr{background:#fff", flat)
        self.assertIn(".side-qr img{display:block;width:160px;height:160px", flat)
        self.assertIn("function fitRail()", js)
        self.assertIn("is-tall", js)

    def test_interstitial_has_a_soft_coffee_line(self):
        previous = build.CFG.get("outbound_interstitial")
        build.CFG["outbound_interstitial"] = True
        build.ADS = {}
        try:
            vi = build.ix_script("vi")
            en = build.ix_script("en")
        finally:
            build.ADS = {}
            if previous is None:
                build.CFG.pop("outbound_interstitial", None)
            else:
                build.CFG["outbound_interstitial"] = previous
        self.assertIn("Thấy hữu ích? Mời mình ly cà phê", vi)
        self.assertIn("/ung-ho/", vi)
        self.assertIn("/en/support/", en)
        self.assertIn("coffee", en.lower())

    def test_dismiss_is_applied_before_first_paint(self):
        self.assertIn("rjvn-support-hide", build.THEME_BOOT)
        self.assertIn("dataset.support", build.THEME_BOOT)

    def test_static_qr_assets_exist(self):
        assets = os.path.join(ROOT, "site", "assets")
        for name in ("vietqr-tpbank.webp", "vietqr-tpbank.png", "binance-pay.webp", "binance-pay.png"):
            path = os.path.join(assets, name)
            self.assertTrue(os.path.isfile(path), path)
            self.assertGreater(os.path.getsize(path), 1000)
        with open(os.path.join(assets, "binance-pay.png"), "rb") as fh:
            header = fh.read(24)
        self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
        width = int.from_bytes(header[16:20], "big")
        height = int.from_bytes(header[20:24], "big")
        self.assertEqual((width, height), (675, 675))
        with open(os.path.join(assets, "vietqr-tpbank.png"), "rb") as fh:
            viet = fh.read(24)
        self.assertEqual(viet[:8], b"\x89PNG\r\n\x1a\n")
        viet_w = int.from_bytes(viet[16:20], "big")
        viet_h = int.from_bytes(viet[20:24], "big")
        self.assertEqual((viet_w, viet_h), (683, 683))

    def test_binance_pay_card_uses_config_and_hides_empty_usdt(self):
        with open(os.path.join(ROOT, "site.config.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        block = cfg["donate"]["binance"]
        self.assertEqual(block["username"], "hiddencat")
        self.assertEqual(block["qr_image"], "/assets/binance-pay.png")
        self.assertIsNone(block["pay_id"])
        self.assertEqual(block["usdt_addresses"], [])
        repo = "https://github.com/quocdat029x/remotejob-vn"
        vi = support_page.body("vi", repo=repo)
        self.assertLess(vi.index('id="vietqr"'), vi.index('id="binance"'))
        self.assertLess(vi.index('id="binance"'), vi.index('id="international"'))
        self.assertIn("Mở app Binance → Pay → Quét mã, hoặc tìm username hiddencat", vi)
        self.assertIn("Chuyển khoản Binance Pay giữa các tài khoản Binance không mất phí.", vi)
        self.assertIn('data-copy="hiddencat"', vi)
        self.assertIn('src="/assets/binance-pay.png"', vi)
        self.assertIn('srcset="/assets/binance-pay.webp"', vi)
        self.assertIn('width="675"', vi)
        self.assertIn('height="675"', vi)
        self.assertIn('loading="lazy"', vi.split('id="binance"', 1)[1].split("</section>", 1)[0])
        self.assertNotIn("USDT", vi)
        self.assertNotIn("Binance Pay ID", vi)
        self.assertNotIn("binance.com", vi)
        self.assertNotIn("<script", vi)
        en = support_page.body("en", repo=repo)
        self.assertLess(en.index('id="international"'), en.index('id="binance"'))
        self.assertLess(en.index('id="binance"'), en.index('id="vietqr"'))
        self.assertIn("Open the Binance app → Pay → Scan the code, or search for the username hiddencat", en)
        self.assertIn("Binance Pay transfers between Binance users are free.", en)
        self.assertIn('data-copy="hiddencat"', en)
        self.assertNotIn("USDT", en)

    def test_usdt_rows_render_only_when_addresses_exist(self):
        repo = "https://github.com/quocdat029x/remotejob-vn"
        trc = "T123456789012345678901234567890123"
        bep = "0x" + ("ab" * 20)
        donate = {"binance": {
            "username": "hiddencat",
            "qr_image": "/assets/binance-pay.png",
            "pay_id": "1092837465",
            "usdt_addresses": [
                {"network": "trc20", "address": trc},
                {"network": "BEP20", "address": bep},
                {"network": "", "address": trc},
                {"network": "TRC20", "address": "short"},
            ],
        }}
        vi = support_page.body("vi", repo=repo, donate=donate)
        self.assertIn("USDT (TRC20)", vi)
        self.assertIn("USDT (BEP20)", vi)
        self.assertIn(f'data-copy="{trc}"', vi)
        self.assertIn(f'data-copy="{bep}"', vi)
        self.assertIn('data-copy="1092837465"', vi)
        self.assertIn("Chỉ gửi USDT đúng mạng ghi bên dưới.", vi)
        self.assertEqual(vi.count("USDT (TRC20)"), 1)
        en = support_page.body("en", repo=repo, donate=donate)
        self.assertIn("USDT (TRC20)", en)
        self.assertIn("Send USDT only on the network named below.", en)
        self.assertIn("Binance Pay ID", en)
        hidden = support_page.body("vi", repo=repo, donate={"binance": {
            "username": "hiddencat",
            "qr_image": "https://evil.example/qr.png",
            "pay_id": None,
            "usdt_addresses": [{"network": "TRC20", "address": trc}],
        }})
        self.assertNotIn('id="binance"', hidden)
        self.assertNotIn("evil.example", hidden)
        self.assertNotIn(trc, hidden)


if __name__ == "__main__":
    unittest.main()
