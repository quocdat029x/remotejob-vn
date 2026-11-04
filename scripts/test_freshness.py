#!/usr/bin/env python3
"""ATS feeds, link checks, AdSense wiring, IndexNow URL diffs, llms.txt, robots.txt."""
import json
import os
import unittest

import adsense
import ats_feeds
import build
import data_health
import indexnow
import jobfilter as jf
import legal_pages
import linkcheck_jobs
import llms

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AdsenseTests(unittest.TestCase):
    def test_configured_publisher_id_and_ads_txt(self):
        with open(os.path.join(ROOT, "site.config.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
        self.assertEqual(adsense.client_id(cfg), "ca-pub-7257034493587502")
        self.assertEqual(adsense.slot_id(cfg, "sidebar"), "")
        self.assertEqual(
            adsense.ads_txt(cfg["adsense_client"]),
            "google.com, pub-7257034493587502, DIRECT, f08c47fec0942fa0\n",
        )
        tag = adsense.loader_tag(cfg["adsense_client"])
        self.assertIn("async", tag)
        self.assertIn("crossorigin=\"anonymous\"", tag)
        self.assertIn("?client=ca-pub-7257034493587502", tag)
        self.assertIn("google-adsense-account", adsense.meta_tag(cfg["adsense_client"]))

    def test_empty_client_is_ignored(self):
        self.assertEqual(adsense.client_id({"adsense_client": ""}), "")
        self.assertEqual(adsense.client_id({"adsense_client": "pub-1"}), "")

    def test_csp_gains_adsense_hosts_only_when_widened(self):
        with open(os.path.join(ROOT, "site", "_headers"), encoding="utf-8") as fh:
            raw = fh.read()
        self.assertIn("https://static.cloudflareinsights.com", raw)
        self.assertNotIn("pagead2.googlesyndication.com", raw)
        widened = adsense.widen_csp(raw, [])
        self.assertIn("https://pagead2.googlesyndication.com", widened)
        self.assertIn("https://googleads.g.doubleclick.net", widened)
        self.assertIn("frame-src", widened)
        self.assertIn("https://cloudflareinsights.com", widened)

    def test_house_slots_and_interstitial_are_not_adsense_units(self):
        with open(os.path.join(ROOT, "data", "ads.json"), encoding="utf-8") as fh:
            ads = json.load(fh)
        html = build.ad_sidebar("vi", ads) + build.ad_native("vi", ads) + build.ad_bottom("vi", ads)
        self.assertIn("300 × 250", html)
        self.assertNotIn("adsbygoogle", html)
        self.assertNotIn("data-ad-slot", html)
        ix = build.ix_script("vi")
        self.assertNotIn("adsbygoogle", ix)
        self.assertNotIn("googlesyndication", ix)

    def test_privacy_mentions_google_cookies_only_when_enabled(self):
        on = legal_pages.privacy_body("vi", ads_on=True) + legal_pages.privacy_body("en", ads_on=True)
        self.assertIn("https://adssettings.google.com/", on)
        self.assertIn("https://policies.google.com/technologies/ads", on)
        self.assertIn("Cloudflare Web Analytics", legal_pages.privacy_body("en", ads_on=True))
        self.assertIn("Affiliate", legal_pages.privacy_body("en", ads_on=True))
        off = legal_pages.privacy_body("en", ads_on=False)
        self.assertNotIn("adssettings.google.com", off)
        contact = legal_pages.contact_body("en", repo="https://example.com", report_url="https://example.com/r", add_url="https://example.com/a", post_url="https://example.com/p")
        self.assertNotIn("mailto:", contact)
        self.assertIn("phone number", contact.lower())


class FeedAndLinkTests(unittest.TestCase):
    def test_new_ats_urls_are_single_postings(self):
        cases = {
            "smartrecruiters": "https://jobs.smartrecruiters.com/Acme/743999936123456",
            "personio": "https://acme.jobs.personio.de/job/39958",
            "teamtailor": "https://acme.teamtailor.com/jobs/12345-engineer",
            "bamboohr": "https://acme.bamboohr.com/careers/17",
            "breezy": "https://acme.breezy.hr/p/abc123-engineer",
            "jazzhr": "https://acme.applytojob.com/apply/Ab12/engineer",
            "pinpoint": "https://acme.pinpointhq.com/en/postings/engineer",
            "rippling": "https://ats.rippling.com/accelerant/jobs/57ae5e12-9e90-481d-8a27-3653a955d669",
            "dover": "https://jobs.dover.com/TinyFish/ff0fcaa2-76ac-43d2-8e86-9453910eb642",
        }
        for ats, url in cases.items():
            ok, why = jf.is_job(ats, url, "Engineer", today=__import__("datetime").date(2026, 10, 28))
            self.assertTrue(ok, (ats, why))
        self.assertIn("rippling", jf.API_ATS)

    def test_rippling_and_personio_parsers(self):
        raw = json.dumps([{
            "uuid": "57ae5e12-9e90-481d-8a27-3653a955d669",
            "name": "Engineer",
            "url": "https://ats.rippling.com/accelerant/jobs/57ae5e12-9e90-481d-8a27-3653a955d669",
            "workLocation": {"label": "Remote (United States)"},
        }])
        jobs = ats_feeds.parse_rippling(raw, "accelerant", "accelerant")
        self.assertEqual(jobs[0]["title"], "Engineer")
        self.assertIn("Remote", jobs[0]["location"])
        xml = """<workzag-jobs><position><id>12</id><name>SRE</name><office>Remote</office>
                 <createdAt>2026-01-02T00:00:00+00:00</createdAt>
                 <jobDescriptions><jobDescription><value>Keep the lights on</value></jobDescription></jobDescriptions>
                 </position></workzag-jobs>"""
        parsed = ats_feeds.parse_personio(xml, "acme", "acme", "de")
        self.assertEqual(parsed[0]["url"], "https://acme.jobs.personio.de/job/12")
        self.assertEqual(parsed[0]["date_posted"], "2026-01-02")

    def test_dover_marks_remote_from_the_description(self):
        devsecops = ats_feeds.parse_dover_detail({
            "id": "ff0fcaa2-76ac-43d2-8e86-9453910eb642",
            "title": "Senior DevSecOps Engineer",
            "workplace_type": "HYBRID",
            "locations": [
                {"name": "Los Altos, CA"},
                {"name": "Ho Chi Minh City, Viet Nam"},
            ],
            "user_provided_description": (
                "<p>Location: In-office or Remote - (strong preference for overlap with Pacific Time).</p>"
                "<p>A remote, distributed, and async-friendly work environment.</p>"
            ),
            "created": "2026-08-25T16:54:42.306040Z",
            "compensation": {
                "open_to_sharing_comp": False,
                "lower_bound": 150000,
                "upper_bound": 200000,
                "currency_code": "USD",
                "salary_range_type": "YEARLY",
            },
        }, "tinyfish", "TinyFish")
        self.assertEqual(
            devsecops["url"],
            "https://jobs.dover.com/TinyFish/ff0fcaa2-76ac-43d2-8e86-9453910eb642",
        )
        self.assertEqual(jf.job_remote(devsecops["title"], devsecops["location"]), "yes")
        self.assertIsNone(devsecops["salary"])
        self.assertEqual(devsecops["date_posted"], "2026-08-25")
        self.assertIn("Pacific Time", devsecops["desc"])

        onsite = ats_feeds.parse_dover_detail({
            "id": "285c761b-b297-4dc4-96d2-09b63d683af8",
            "title": "Business Development Representative Intern",
            "workplace_type": "ONSITE",
            "locations": [{"name": "Ho Chi Minh City, Viet Nam"}],
            "user_provided_description": "<p>Location: Ho Chi Minh City, Vietnam. Experience with distributed systems.</p>",
        }, "tinyfish", "TinyFish")
        self.assertEqual(jf.job_remote(onsite["title"], onsite["location"]), "no")
        self.assertFalse(ats_feeds.description_allows_remote(onsite["desc"]))

        hybrid = ats_feeds.parse_dover_detail({
            "id": "23c970ad-73c7-4a89-9b1c-87e762528417",
            "title": "Product Marketing Manager",
            "workplace_type": "HYBRID",
            "locations": [{"name": "San Francisco, CA"}],
            "user_provided_description": "Base salary: Competitive",
            "compensation": {"open_to_sharing_comp": True, "lower_bound": None, "upper_bound": None},
        }, "tinyfish", "TinyFish")
        self.assertEqual(jf.job_remote(hybrid["title"], hybrid["location"]), "hybrid")
        self.assertIsNone(hybrid["salary"])

        remote = ats_feeds.parse_dover_detail({
            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "title": "Engineer",
            "workplace_type": "REMOTE",
            "locations": [{"location_option": {"display_name": "Remote"}}],
            "user_provided_description": "",
            "compensation": {
                "open_to_sharing_comp": True,
                "lower_bound": 100000,
                "upper_bound": 120000.0,
                "currency_code": "USD",
                "salary_range_type": "YEARLY",
            },
        }, "tinyfish", "TinyFish")
        self.assertEqual(jf.job_remote(remote["title"], remote["location"]), "yes")
        self.assertEqual(remote["salary"], "100000-120000 USD YEARLY")

        ok, why = jf.is_job("dover", devsecops["url"], devsecops["title"], today=__import__("datetime").date(2026, 11, 4))
        self.assertTrue(ok, why)
        careers = "https://jobs.dover.com/TinyFish/careers/1499366e-a68d-43f0-91e2-bc016d9eb5ee"
        self.assertFalse(jf.is_job("dover", careers, "Careers")[0])
        self.assertIn("dover", jf.API_ATS)

        calls = []

        def get(url, accept=None):
            calls.append(url)
            if url.endswith("/jobs"):
                return json.dumps({"count": 2, "next": None, "results": [
                    {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "title": "Engineer", "is_published": True},
                    {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "is_published": False},
                ]})
            return json.dumps({
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "title": "Engineer",
                "client_name": "TinyFish",
                "workplace_type": "HYBRID",
                "locations": [{"name": "Palo Alto, CA"}],
                "user_provided_description": "Location: In-office or Remote (strong preference for overlap with Pacific Time).",
                "created": "2026-10-26T08:09:25.335323Z",
                "active": True,
            })

        pauses = []
        src = {
            "slug": "tinyfish", "ats": "dover", "token": "TinyFish",
            "endpoint": "https://app.dover.com/api/v1/careers-page/1499366e-a68d-43f0-91e2-bc016d9eb5ee/jobs",
        }
        jobs = ats_feeds.fetch_dover(src, get, lambda: pauses.append(1))
        self.assertEqual(len(jobs), 1)
        self.assertEqual(pauses, [1])
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[1].endswith("/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
        self.assertEqual(jf.job_remote(jobs[0]["title"], jobs[0]["location"]), "yes")
        self.assertEqual(jobs[0]["date_posted"], "2026-10-26")

    def test_link_check_classification(self):
        job = "https://example.com/jobs/123-engineer"
        careers = "https://example.com/careers"
        self.assertEqual(linkcheck_jobs.classify(404, job, job, careers, None), "removed")
        self.assertEqual(linkcheck_jobs.classify(410, job, job, careers, None), "removed")
        self.assertEqual(linkcheck_jobs.classify(200, careers, job, careers, None), "removed")
        self.assertEqual(linkcheck_jobs.classify(200, job, job, careers, None), "alive")
        self.assertEqual(linkcheck_jobs.classify(200, job + "/", job, careers, None), "alive")
        self.assertEqual(linkcheck_jobs.classify(403, job, job, careers, None), "blocked")
        self.assertEqual(linkcheck_jobs.classify(None, job, job, careers, None, error="timeout"), "error")
        self.assertTrue(linkcheck_jobs.is_generic_listing("https://itviec.com/companies/fram", "https://itviec.com/it-jobs/devops-1", None, None))

    def test_health_threshold_is_above_thirty_percent(self):
        self.assertFalse(data_health.is_unhealthy(10, 3))
        self.assertTrue(data_health.is_unhealthy(10, 4))
        self.assertFalse(data_health.is_unhealthy(0, 0))


class LlmsAndIndexTests(unittest.TestCase):
    def test_robots_allows_named_crawlers_and_points_at_llms(self):
        text = llms.robots_txt("https://remotejob.nguyenquocdat.dev")
        self.assertIn("# Machine-readable summary for assistants: https://remotejob.nguyenquocdat.dev/llms.txt", text)
        self.assertIn("Allow: /", text)
        self.assertIn("Disallow: /data/jobs-index.json", text)
        for agent in ("Mediapartners-Google", "AdsBot-Google", "GPTBot", "OAI-SearchBot", "ChatGPT-User",
                      "ClaudeBot", "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bingbot"):
            self.assertIn(f"User-agent: {agent}", text)
        self.assertIn("Sitemap: https://remotejob.nguyenquocdat.dev/sitemap.xml", text)
        self.assertIn("Sitemap: https://remotejob.nguyenquocdat.dev/sitemap-vi.xml", text)
        self.assertIn("Sitemap: https://remotejob.nguyenquocdat.dev/sitemap-en.xml", text)

    def test_llms_txt_has_the_public_sections(self):
        text = llms.llms_txt("https://remotejob.nguyenquocdat.dev", "https://github.com/quocdat029x/remotejob-vn",
                             [("devops", "DevOps", "DevOps")])
        self.assertTrue(text.startswith("# RemoteJob VN"))
        self.assertIn("Vietnamese-first", text)
        for path in ("/viec-lam/", "/viec-lam-remote/devops/", "/cong-ty/", "/cong-cu/", "/dang-tin/",
                     "/gioi-thieu/", "/chinh-sach-bao-mat/", "/ung-ho/", "/en/", "/en/privacy/",
                     "/en/support/", "/llms-full.txt"):
            self.assertIn("https://remotejob.nguyenquocdat.dev" + path, text)
        self.assertIn("https://github.com/quocdat029x/remotejob-vn", text)
        self.assertIn("CC BY 4.0", text)

    def test_llms_full_lists_public_fields_only(self):
        companies = [{
            "slug": "acme", "name": "Acme", "remote_policy": "Fully remote",
            "vn_hiring_mode": "Direct hire", "careers_url": "https://example.com/careers",
        }]
        jobs = [{
            "path": "/viec-lam/acme-engineer/", "title": "Engineer", "company_name": "Acme",
            "location": "Remote", "remote": "yes", "last_checked": "2026-10-28",
        }]
        text = llms.llms_full_txt("https://remotejob.nguyenquocdat.dev", companies, jobs, "2026-10-28")
        self.assertIn("https://remotejob.nguyenquocdat.dev/cong-ty/acme/", text)
        self.assertIn("https://example.com/careers", text)
        self.assertIn("checked 2026-10-28", text)
        self.assertNotIn("@", text)

    def test_indexnow_submits_added_and_removed_job_urls_only(self):
        old = [{"key": "a:1", "company_slug": "acme", "title": "Engineer", "url": "https://example.com/1",
                "status": "open", "location": "Remote", "description": "x", "last_checked": "2026-10-01"}]
        new = [{"key": "a:1", "company_slug": "acme", "title": "Engineer", "url": "https://example.com/1",
                "status": "open", "location": "Remote", "description": "x", "last_checked": "2026-10-28"},
               {"key": "a:2", "company_slug": "acme", "title": "SRE", "url": "https://example.com/2",
                "status": "open", "location": None, "description": None}]
        urls = indexnow.changed_job_urls(old, new, "https://remotejob.nguyenquocdat.dev")
        self.assertTrue(any(u.endswith("/en/viec-lam/acme-sre/") or "/viec-lam/acme-sre/" in u for u in urls))
        self.assertFalse(any("engineer" in u and "sre" not in u for u in urls))

    def test_headers_declare_llms_as_text(self):
        with open(os.path.join(ROOT, "site", "_headers"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("/llms.txt", text)
        self.assertIn("/llms-full.txt", text)
        self.assertEqual(text.count("Content-Type: text/plain; charset=utf-8"), 2)


if __name__ == "__main__":
    unittest.main()
