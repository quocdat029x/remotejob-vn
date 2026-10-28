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


if __name__ == "__main__":
    unittest.main()
