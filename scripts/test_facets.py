#!/usr/bin/env python3
"""Facet tokens stay aligned with category hubs."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import facets
import hubs
from site_text import ROLE_PAGES


def company(slug, name="Acme", tz=None, kind=None, group="B"):
    row = {"slug": slug, "name": name, "hires_roles": [], "_tz": list(tz or []), "group": group}
    if kind:
        row["kind"] = kind
    return row


def job(key, title, company_slug="acme", **extra):
    row = {
        "key": key,
        "title": title,
        "company_slug": company_slug,
        "remote": "yes",
        "region": "global",
        "roles": [],
        "last_checked": "2026-10-28",
        "path": f"/viec-lam/{key}/",
        "status": "open",
    }
    row.update(extra)
    return row


class TokenAgreementTests(unittest.TestCase):
    def test_published_hubs_and_tokens_select_the_same_jobs(self):
        cos = {
            "acme": company("acme", tz=["eu"]),
            "usco": company("usco", "US Co", tz=["us"], group="A"),
            "vnco": company("vnco", "VN Co", tz=[]),
            "board": company("board", "Board", tz=["eu"], kind="aggregator"),
        }
        jobs = []
        for i in range(3):
            jobs.append(job(f"py{i}", "Python Engineer", salary="$100K"))
            jobs.append(job(f"dev{i}", "Senior DevOps Engineer", roles=["devops"]))
            jobs.append(job(f"k8s{i}", "Kubernetes Platform Engineer"))
            jobs.append(job(f"sre{i}", "Site Reliability Engineer", company_slug="usco", roles=["sre"]))
            jobs.append(job(f"go{i}", "Golang Engineer"))
        jobs.append(job("gtm", "Go-To-Market Engineer"))
        jobs.append(job("gtm2", "Go to Market Lead"))
        jobs.append(job("vn", "Support Engineer", company_slug="vnco", region="vn"))
        onsite = job("onsite", "Python Engineer", remote="no")
        boarded = job("board", "Python Engineer", company_slug="board")
        jobs.extend([onsite, boarded])

        catalog = hubs.collect(jobs, cos, ROLE_PAGES)
        kind_key = {"role": "role", "tech": "skill", "timezone": "tz", "seniority": "level", "salary": "salary"}
        url_slug = {"gio-eu-apac": "eu-apac", "gio-my": "us"}
        self.assertTrue(catalog)
        for hub in catalog:
            key = kind_key[hub["kind"]]
            slug = url_slug.get(hub["slug"], hub["slug"])
            for item in jobs:
                co = cos[item["company_slug"]]
                if co.get("kind") == "aggregator" or item.get("remote") == "no":
                    continue
                tok = facets.tokens(item, co)
                has = tok["salary"] == "yes" if key == "salary" else slug in tok[key]
                self.assertEqual(has, item["key"] in hub["keys"], f"{item['title']} vs {hub['slug']}")

        self.assertNotIn(onsite["key"], next(h["keys"] for h in catalog if h["slug"] == "python"))
        self.assertIn("python", facets.tokens(onsite, cos["acme"])["skill"])
        self.assertNotIn(boarded["key"], next(h["keys"] for h in catalog if h["slug"] == "python"))
        self.assertIn("python", facets.tokens(boarded, cos["board"])["skill"])
        go = next(h for h in catalog if h["slug"] == "go")
        self.assertNotIn("gtm", go["keys"])
        self.assertNotIn("go", facets.tokens(job("gtm", "Go-To-Market Engineer"), cos["acme"])["skill"])
        self.assertIn("eu-apac", facets.tokens(job("vn", "Support Engineer", region="vn"), cos["vnco"])["tz"])
        self.assertIn("us", facets.tokens(job("sre0", "Site Reliability Engineer"), cos["usco"])["tz"])
        senior = facets.tokens(job("dev0", "Senior DevOps Engineer", roles=["devops"]), cos["acme"])
        self.assertIn("senior", senior["level"])
        self.assertIn("devops", senior["role"])
        self.assertNotIn("mid", senior["level"])

    def test_catalog_uses_filter_slugs_and_skips_empty_facets(self):
        seen = facets.empty_seen()
        sample = job("a", "Senior DevOps Kubernetes", roles=["devops"], salary="$1", date_posted="2026-10-01", region="vn")
        tok = facets.tokens(sample, company("acme", tz=["eu"], group="A"))
        facets.observe(seen, sample, tok)
        fx = {row[0]: row for row in facets.catalog(seen, [("acme", "Acme")])}
        self.assertEqual([opt[0] for opt in fx["tz"][3]], ["eu-apac"])
        self.assertIn("devops", [opt[0] for opt in fx["role"][3]])
        self.assertIn("kubernetes", [opt[0] for opt in fx["skill"][3]])
        self.assertIn("senior", [opt[0] for opt in fx["level"][3]])
        self.assertEqual(fx["salary"][3][0][0], "yes")
        self.assertEqual([opt[0] for opt in fx["posted"][3]], ["7", "30", "90"])
        self.assertEqual(fx["company"][3][0][0], "acme")
        self.assertNotIn("gio-eu-apac", fx)
        empty = facets.catalog(facets.empty_seen(), [])
        self.assertEqual(empty, [])


if __name__ == "__main__":
    unittest.main()
