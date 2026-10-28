#!/usr/bin/env python3
"""Affiliate slot order and the Cloudflare Web Analytics CSP allow-list."""
import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ContentTests(unittest.TestCase):
    def test_affiliate_sections_follow_the_audience_order(self):
        with open(os.path.join(ROOT, "data/affiliates.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        ids = [c["id"] for c in data["categories"]]
        self.assertEqual(ids, ["payments", "learning", "home-office", "vps", "coworking"])
        names = [it["name"] for c in data["categories"] for it in c["items"]]
        for required in (
            "Wise", "Payoneer", "Coursera", "Udemy", "KodeKloud", "Duolingo", "ELSA Speak", "Kickresume",
            "Ghế công thái học", "Bàn đứng", "Màn hình", "Tai nghe", "Router", "UPS",
            "DigitalOcean", "Vultr", "Hostinger", "TP.HCM", "Hà Nội", "Đà Nẵng",
        ):
            self.assertIn(required, names)
        for cat in data["categories"]:
            self.assertTrue(cat["intro"]["vi"].strip())
            self.assertTrue(cat["intro"]["en"].strip())
            for it in cat["items"]:
                self.assertTrue(it["url"].startswith("https://"), it["url"])
                self.assertNotIn("?", it["url"])
                for key in ("name", "vi", "en"):
                    self.assertTrue(it[key].strip())

    def test_csp_allows_only_the_web_analytics_beacon(self):
        with open(os.path.join(ROOT, "site/_headers"), encoding="utf-8") as fh:
            text = fh.read()
        csp = next(ln for ln in text.splitlines() if ln.strip().startswith("Content-Security-Policy:"))
        script = csp.split("script-src ", 1)[1].split(";", 1)[0]
        connect = csp.split("connect-src ", 1)[1].split(";", 1)[0]
        self.assertIn("https://static.cloudflareinsights.com", script)
        self.assertNotIn("*", script)
        self.assertEqual(connect.strip(), "'self' https://cloudflareinsights.com")
        self.assertNotIn("beacon.min.js", text)
        self.assertNotIn("data-cf-beacon", text)

    def test_post_a_job_template_has_no_contact_details(self):
        with open(os.path.join(ROOT, ".github/ISSUE_TEMPLATE/post-a-job.yml"), encoding="utf-8") as fh:
            text = fh.read().lower()
        self.assertNotIn("mailto:", text)
        self.assertNotIn("id: email", text)
        self.assertNotIn("id: phone", text)
        self.assertIn("do not include personal phone numbers", text)
        self.assertIn("pricing", text)
        self.assertIn("vietnam", text)


if __name__ == "__main__":
    unittest.main()
