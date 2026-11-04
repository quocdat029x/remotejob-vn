#!/usr/bin/env python3
"""Aggregator companies stay out of default mixed listings. Stdlib unittest only."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import build


class ListingTests(unittest.TestCase):
    def test_kind_flags_aggregators_only(self):
        self.assertTrue(build.company_is_aggregator({"slug": "huzzle", "kind": "aggregator"}))
        self.assertFalse(build.company_is_aggregator({"slug": "acme"}))
        self.assertFalse(build.company_is_aggregator({"slug": "acme", "kind": "employer"}))

    def test_default_listings_omit_aggregator_jobs(self):
        cos = {
            "huzzle": {"slug": "huzzle", "kind": "aggregator"},
            "acme": {"slug": "acme"},
        }
        jobs = [
            {"company_slug": "huzzle", "title": "Board role"},
            {"company_slug": "acme", "title": "Direct role"},
        ]
        listed = build.jobs_for_default_listings(jobs, cos)
        self.assertEqual([j["company_slug"] for j in listed], ["acme"])

    def test_interstitial_script_follows_config_flag(self):
        previous = build.CFG.get("outbound_interstitial")
        build.CFG["outbound_interstitial"] = False
        try:
            self.assertEqual(build.ix_script("vi"), "")
        finally:
            if previous is None:
                build.CFG.pop("outbound_interstitial", None)
            else:
                build.CFG["outbound_interstitial"] = previous
        build.CFG["outbound_interstitial"] = True
        build.ADS = {"interstitial": {"label": "Quảng cáo / Advertisement", "seconds": 5, "href": "/quang-cao/",
                                       "vi": {"title": "Nhà tuyển dụng", "continue": "Tiếp tục tới tin tuyển dụng"}}}
        try:
            html = build.ix_script("vi")
        finally:
            build.ADS = {}
            if previous is None:
                build.CFG.pop("outbound_interstitial", None)
            else:
                build.CFG["outbound_interstitial"] = previous
        self.assertIn('id="rj-ix"', html)
        self.assertIn("Quảng cáo / Advertisement", html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("adsbygoogle", html)
        self.assertIn('"first_click": true', html)
        self.assertIn('"every_n": 2', html)
        self.assertIn('"min_gap_ms": 180000', html)


class FreshnessOrderTests(unittest.TestCase):
    @staticmethod
    def job(slug, title, date_posted=None, first_seen=None, region="vn", remote="yes"):
        return {"company_slug": slug, "title": title, "region": region, "remote": remote,
                "date_posted": date_posted, "first_seen": first_seen, "last_checked": "2026-11-02"}

    def test_jobs_newest_posted_date_first(self):
        co_by = {"acme": {"slug": "acme", "name": "Acme"}, "beta": {"slug": "beta", "name": "Beta"}}
        jobs = [
            self.job("acme", "Old role", date_posted="2026-08-01"),
            self.job("beta", "New role", date_posted="2026-10-20"),
            self.job("acme", "No posted date", first_seen="2026-09-15"),
        ]
        ordered = build.order_jobs_newest_first(jobs, co_by)
        self.assertEqual([j["title"] for j in ordered], ["New role", "No posted date", "Old role"])

    def test_job_ties_keep_region_order(self):
        co_by = {"acme": {"slug": "acme", "name": "Acme"}, "beta": {"slug": "beta", "name": "Beta"}}
        jobs = [
            self.job("beta", "Global role", date_posted="2026-10-20", region="global"),
            self.job("acme", "VN role", date_posted="2026-10-20"),
        ]
        ordered = build.order_jobs_newest_first(jobs, co_by)
        self.assertEqual([j["title"] for j in ordered], ["VN role", "Global role"])

    def test_companies_ranked_by_newest_job(self):
        cos = [
            {"slug": "oldco", "name": "Oldco", "group": "A"},
            {"slug": "newco", "name": "Newco", "group": "B"},
            {"slug": "empty", "name": "Empty", "group": "A"},
        ]
        jobs_by_co = {
            "oldco": [self.job("oldco", "Old", date_posted="2026-05-01")],
            "newco": [self.job("newco", "New", date_posted="2026-10-20")],
            "empty": [],
        }
        self.assertEqual([c["slug"] for c in build.rank_companies_by_freshness(cos, jobs_by_co)],
                         ["newco", "oldco", "empty"])

    def test_aggregators_rank_after_employers(self):
        cos = [
            {"slug": "board", "name": "Board", "group": "B", "kind": "aggregator"},
            {"slug": "acme", "name": "Acme", "group": "B"},
        ]
        jobs_by_co = {
            "board": [self.job("board", "Board job", date_posted="2026-11-01")],
            "acme": [self.job("acme", "Job", date_posted="2026-01-01")],
        }
        self.assertEqual([c["slug"] for c in build.rank_companies_by_freshness(cos, jobs_by_co)],
                         ["acme", "board"])


if __name__ == "__main__":
    unittest.main()
