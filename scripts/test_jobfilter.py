#!/usr/bin/env python3
"""Stale-year filtering follows the calendar year. Stdlib unittest only."""
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import jobfilter as jf

HTML_URL = "https://itviec.com/it-jobs/devops-engineer-12345"
API_URL = "https://boards.greenhouse.io/acme/jobs/12345"


class StaleYearTests(unittest.TestCase):
    def test_year_before_current_is_stale(self):
        ok, why = jf.is_job("custom", HTML_URL, "DevOps Engineer - 07/2025", today=datetime.date(2026, 10, 28))
        self.assertFalse(ok)
        self.assertIn("stale", why)

    def test_current_year_is_kept(self):
        ok, why = jf.is_job("custom", HTML_URL, "DevOps Engineer 2026", today=datetime.date(2026, 10, 28))
        self.assertTrue(ok, why)

    def test_cutoff_moves_when_the_year_changes(self):
        ok, why = jf.is_job("custom", HTML_URL, "DevOps Engineer 2026", today=datetime.date(2027, 1, 1))
        self.assertFalse(ok)
        self.assertIn("stale", why)

    def test_future_year_is_not_treated_as_stale(self):
        ok, why = jf.is_job("custom", HTML_URL, "DevOps Engineer 2028", today=datetime.date(2026, 10, 28))
        self.assertTrue(ok, why)

    def test_years_before_2010_are_ignored(self):
        ok, why = jf.is_job("custom", HTML_URL, "Engineer 2009 cohort", today=datetime.date(2026, 10, 28))
        self.assertTrue(ok, why)

    def test_api_postings_use_the_same_year_rule(self):
        ok, why = jf.is_job("greenhouse", API_URL, "Engineer 2019", today=datetime.date(2026, 1, 1))
        self.assertFalse(ok)
        self.assertIn("stale", why)

    def test_api_posting_with_current_year_is_kept(self):
        ok, why = jf.is_job("greenhouse", API_URL, "Engineer 2026", today=datetime.date(2026, 6, 1))
        self.assertTrue(ok, why)


if __name__ == "__main__":
    unittest.main()
