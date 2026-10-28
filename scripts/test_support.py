#!/usr/bin/env python3
"""Support page: VietQR + Buy Me a Coffee, hreflang, and the soft ask."""
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
        self.assertIn('width="887"', html)
        self.assertIn('height="1150"', html)
        self.assertIn('srcset="/assets/vietqr-tpbank.webp"', html)
        self.assertIn('src="/assets/vietqr-tpbank.png"', html)
        self.assertNotIn('loading="lazy"', html)
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
        self.assertIn('width="887"', html)
        self.assertIn('height="1150"', html)
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
        for name in ("vietqr-tpbank.webp", "vietqr-tpbank.png"):
            path = os.path.join(assets, name)
            self.assertTrue(os.path.isfile(path), path)
            self.assertGreater(os.path.getsize(path), 1000)


if __name__ == "__main__":
    unittest.main()
