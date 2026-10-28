#!/usr/bin/env python3
"""Category hubs, feeds, and JobPosting rules. Stdlib unittest only."""
import os
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
import build
import hubs
import og_card


def company(slug, name="Acme", tz=None, kind=None):
    row = {"slug": slug, "name": name, "hires_roles": [], "_tz": list(tz or [])}
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


class ThresholdTests(unittest.TestCase):
    def test_under_three_is_skipped_and_three_is_indexable(self):
        cos = {"acme": company("acme")}
        thin = [job("a", "Python Engineer"), job("b", "Senior Python Developer")]
        self.assertFalse(any(h["slug"] == "python" for h in hubs.collect(thin, cos, [])))
        enough = thin + [job("c", "Python Backend", salary="$100K")]
        catalog = hubs.collect(enough, cos, [])
        page = next(h for h in catalog if h["slug"] == "python")
        self.assertTrue(page["indexable"])
        self.assertGreaterEqual(len(page["jobs"]), hubs.MIN_OPEN_JOBS)
        self.assertEqual(page["path"], "/viec-lam-remote/python/")

    def test_curated_role_below_threshold_stays_but_is_not_indexable(self):
        cos = {"acme": company("acme")}
        jobs = [job("a", "DevOps Engineer", roles=["devops"])]
        role_pages = [("devops", "DevOps", "DevOps", {"devops"}, r"devops", {"devops"})]
        catalog = hubs.collect(jobs, cos, role_pages)
        page = next(h for h in catalog if h["slug"] == "devops")
        self.assertEqual(page["origin"], "curated")
        self.assertFalse(page["indexable"])

    def test_aggregator_and_onsite_jobs_are_left_out(self):
        cos = {
            "acme": company("acme"),
            "board": company("board", "Board", kind="aggregator"),
        }
        jobs = [
            job("a", "Python one"),
            job("b", "Python two"),
            job("c", "Python three", company_slug="board"),
            job("d", "Python onsite", remote="no"),
        ]
        catalog = hubs.collect(jobs, cos, [])
        self.assertFalse(any(h["slug"] == "python" for h in catalog))

    def test_go_to_market_is_not_the_go_language(self):
        cos = {"acme": company("acme")}
        titles = [
            "Go-To-Market Engineer",
            "Go to Market Lead",
            "Don't see what you're looking for? (Go to Market)",
            "Senior Backend Engineer (Go)",
            "Python / Go",
            "Juju Software Engineer (Go)",
        ]
        jobs = [job(str(i), title) for i, title in enumerate(titles)]
        catalog = hubs.collect(jobs, cos, [])
        page = next(h for h in catalog if h["slug"] == "go")
        titles = {item["title"] for item in page["jobs"]}
        self.assertEqual(titles, {
            "Senior Backend Engineer (Go)",
            "Python / Go",
            "Juju Software Engineer (Go)",
        })

    def test_unlabeled_title_is_not_mid_and_explicit_levels_are(self):
        cos = {"acme": company("acme")}
        jobs = [
            job("a", "Software Engineer"),
            job("b", "Software Engineer II"),
            job("c", "Mid-level Engineer"),
            job("d", "Junior Engineer"),
            job("e", "Junior Developer"),
            job("f", "Graduate Engineer"),
            job("g", "Senior Engineer"),
            job("h", "Sr. Engineer"),
            job("i", "Senior Developer"),
            job("j", "Staff Engineer"),
            job("k", "Head of Engineering"),
            job("l", "Lead Engineer"),
        ]
        catalog = {h["slug"]: h for h in hubs.collect(jobs, cos, [])}
        self.assertNotIn("mid", catalog)  # a single "Mid-level" title is below the threshold
        self.assertEqual(len(catalog["junior"]["jobs"]), 3)
        self.assertEqual(len(catalog["senior"]["jobs"]), 3)
        self.assertEqual(len(catalog["lead"]["jobs"]), 3)
        senior_titles = {item["title"] for item in catalog["senior"]["jobs"]}
        self.assertNotIn("Software Engineer", senior_titles)

    def test_salary_hub_uses_only_published_strings(self):
        cos = {"acme": company("acme", "Acme")}
        jobs = [
            job("a", "Engineer", salary="$100K"),
            job("b", "Designer", salary="  $80K – $90K "),
            job("c", "Analyst", salary=None),
            job("d", "Writer", salary=""),
            job("e", "Editor", salary="$70K"),
        ]
        catalog = hubs.collect(jobs, cos, [])
        page = next(h for h in catalog if h["slug"] == "luong-cong-khai")
        self.assertEqual(len(page["jobs"]), 3)
        self.assertEqual(page["salary_samples"][0], "$100K")
        intro = hubs.intro_for(page, "vi")
        self.assertIn("3", intro)
        self.assertIn("Acme", intro)
        self.assertNotIn("120000", intro)

    def test_timezone_uses_notes_and_region_only(self):
        cos = {
            "vn": company("vn", "VN Co", tz=["vn"]),
            "us": company("us", "US Co", tz=["us"]),
            "both": company("both", "Both Co", tz=["vn", "us"]),
            "unknown": company("unknown", "Unknown Co", tz=["unknown"]),
        }
        jobs = [
            job("a", "Engineer A", company_slug="vn", region="other"),
            job("b", "Engineer B", company_slug="vn", region="other"),
            job("c", "Engineer C", company_slug="us", region="other"),
            job("d", "Engineer D", company_slug="us", region="other"),
            job("e", "Engineer E", company_slug="us", region="other"),
            job("f", "Engineer F", company_slug="both", region="other"),
            job("g", "Engineer G", company_slug="unknown", region="apac"),
            job("h", "Engineer H", company_slug="unknown", region="other"),
            job("i", "Engineer I", company_slug="unknown", region="apac"),
        ]
        # Pad EU/APAC above the threshold: vn a,b + both f + apac g,i = 5. US: c,d,e + both f = 4.
        catalog = {h["slug"]: h for h in hubs.collect(jobs, cos, [])}
        eu_keys = catalog["gio-eu-apac"]["keys"]
        us_keys = catalog["gio-my"]["keys"]
        self.assertIn("a", eu_keys)
        self.assertIn("g", eu_keys)
        self.assertNotIn("h", eu_keys)
        self.assertNotIn("c", eu_keys)
        self.assertIn("c", us_keys)
        self.assertIn("f", us_keys)
        self.assertIn("f", eu_keys)
        self.assertNotIn("h", us_keys)


class PageCopyTests(unittest.TestCase):
    def _python(self):
        cos = {"acme": company("acme", "Acme"), "beta": company("beta", "Beta")}
        jobs = [
            job("a", "Python Engineer", company_slug="acme", region="vn", salary="$100K"),
            job("b", "Python Developer", company_slug="acme", region="apac"),
            job("c", "Senior Python", company_slug="beta", region="global"),
        ]
        page = next(h for h in hubs.collect(jobs, cos, []) if h["slug"] == "python")
        return page

    def test_vi_and_en_copy_are_unique_and_use_real_counts(self):
        page = self._python()
        vi = hubs.page_copy(page, "vi")
        en = hubs.page_copy(page, "en")
        self.assertNotEqual(vi["h1"], en["h1"])
        self.assertIn("Python", vi["h1"])
        self.assertIn("Python", en["h1"])
        for copy in (vi, en):
            self.assertIn("3", copy["intro"])
            self.assertIn("Acme", copy["intro"])
            self.assertIn("28/10/2026" if copy is vi else "2026-10-28", copy["intro"])
            self.assertGreaterEqual(len(copy["faq"]), 3)
        questions = " ".join(q for q, _a in vi["faq"])
        self.assertIn("Python", questions)
        answers = " ".join(a for _q, a in vi["faq"])
        self.assertIn("Acme", answers)
        self.assertNotIn("Gamma", answers)
        self.assertNotIn("lorem", answers.lower())
        ld = hubs.faq_jsonld(vi["faq"])
        self.assertEqual(ld["@type"], "FAQPage")
        self.assertEqual(ld["mainEntity"][0]["name"], vi["faq"][0][0])
        self.assertEqual(ld["mainEntity"][0]["acceptedAnswer"]["text"], vi["faq"][0][1])

    def test_rendered_hub_has_faq_links_and_job_list(self):
        page = self._python()
        other = dict(page)
        other = {
            "kind": "role", "slug": "backend", "path": "/viec-lam-remote/backend/",
            "vi": "Backend", "en": "Backend", "jobs": page["jobs"], "keys": page["keys"],
            "indexable": True,
        }
        body, copy = hubs.sections_html(
            page, "vi", "<ul><li>Python Engineer</li></ul>", [other], lambda path: path)
        self.assertIn(f"<h1>{copy['h1']}</h1>", body)
        self.assertIn('id="faq"', body)
        self.assertIn("Python Engineer", body)
        self.assertIn('href="/viec-lam-remote/backend/"', body)
        self.assertIn('href="/cong-ty/acme/"', body)
        html = build.page(
            "vi", page["path"], copy["title"], copy["description"], body,
            jsonld=[hubs.faq_jsonld(copy["faq"])],
            crumbs=[("Danh mục", "/viec-lam-remote/"), (page["vi"], page["path"])])
        self.assertIn("FAQPage", html)
        self.assertIn("BreadcrumbList", html)
        self.assertIn('rel="canonical" href="https://remotejob.nguyenquocdat.dev/viec-lam-remote/python/"', html)
        self.assertIn('hreflang="en" href="https://remotejob.nguyenquocdat.dev/en/viec-lam-remote/python/"', html)
        self.assertIn('rel="alternate" type="application/rss+xml"', html)
        self.assertIn('rel="alternate" type="application/feed+json"', html)
        self.assertNotIn("fit_score", html)

    def test_index_skips_empty_kinds(self):
        page = self._python()
        html = hubs.index_html([page], "vi", lambda path: path, "Danh mục", "Có 1 trang.")
        self.assertIn("Python", html)
        self.assertIn("Kỹ năng", html)
        self.assertNotIn("Múi giờ", html)


class FeedTests(unittest.TestCase):
    def test_newest_first_and_salary_only_when_published(self):
        cos = {"acme": company("acme", "Acme & Co")}
        jobs = [
            job("old", "Old Role", date_posted="2026-01-01", first_seen="2026-01-01"),
            job("new", "New Role", date_posted="2026-10-20", salary="$90K"),
            job("mid", "Mid Role", first_seen="2026-06-01"),
        ]
        items = hubs.feed_items(jobs, cos, "en", lambda path: "https://example.test" + path, limit=2)
        self.assertEqual([item["title"] for item in items], ["New Role – Acme & Co", "Mid Role – Acme & Co"])
        self.assertIn("$90K", items[0]["summary"])
        self.assertNotIn("$", items[1]["summary"])
        rss = hubs.rss_xml(items, title="T", link="https://example.test/", description="D",
                           language="en", self_url="https://example.test/feed.xml")
        root = ET.fromstring(rss)
        self.assertEqual(root.find("channel/item/title").text, "New Role – Acme & Co")
        self.assertIn("Acme &amp; Co", rss)
        atom = hubs.atom_xml(items, title="T", link="https://example.test/", description="D",
                             self_url="https://example.test/atom.xml", updated="2026-10-28")
        ET.fromstring(atom)
        payload = hubs.json_feed(items, title="T", link="https://example.test/", description="D",
                                  language="en", self_url="https://example.test/feed.json")
        self.assertEqual(payload["version"], "https://jsonfeed.org/version/1.1")
        self.assertEqual(payload["items"][0]["date_published"], "2026-10-20T00:00:00Z")
        self.assertNotIn("email", payload["items"][0])


class JobPostingTests(unittest.TestCase):
    def _job(self, **extra):
        row = {
            "key": "acme:1", "title": "Engineer", "url": "https://jobs.example/1",
            "date_posted": "2026-10-01", "last_checked": "2026-10-28",
            "remote": "yes", "region": "vn", "status": "open", "description": "Build systems.",
        }
        row.update(extra)
        return row

    def _company(self, **extra):
        row = {"name": "Acme", "website": "https://acme.example", "careers_url": "https://acme.example/jobs"}
        row.update(extra)
        return row

    def test_removed_and_incomplete_jobs_emit_nothing(self):
        self.assertIsNone(build.job_posting_ld(self._job(status="removed"), self._company()))
        self.assertIsNone(build.job_posting_ld(self._job(date_posted=None), self._company()))
        self.assertIsNone(build.job_posting_ld(self._job(remote="no"), self._company()))
        self.assertIsNone(build.job_posting_ld(self._job(region="apac"), self._company()))
        self.assertIsNone(build.job_posting_ld(self._job(), self._company(kind="aggregator")))

    def test_open_remote_job_uses_real_fields_only(self):
        data = build.job_posting_ld(self._job(salary="$100K"), self._company())
        self.assertEqual(data["datePosted"], "2026-10-01")
        self.assertEqual(data["validThrough"], "2026-11-27")
        self.assertEqual(data["jobLocationType"], "TELECOMMUTE")
        self.assertEqual(data["applicantLocationRequirements"], {"@type": "Country", "name": "Vietnam"})
        self.assertEqual(data["hiringOrganization"]["name"], "Acme")
        self.assertEqual(data["hiringOrganization"]["@type"], "Organization")
        self.assertIn("$100K", data["description"])
        self.assertNotIn("100000", data["description"])
        self.assertNotIn("baseSalary", data)
        undated = build.job_posting_ld(self._job(last_checked=None), self._company())
        self.assertNotIn("validThrough", undated)


class OgCardTests(unittest.TestCase):
    def test_png_is_1200x630_and_changes_with_the_title(self):
        first = og_card.render_hub_png("PYTHON", 3, "2026-10-28")
        second = og_card.render_hub_png("PUBLIC SALARY", 12, "2026-10-01")
        self.assertTrue(first.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertNotEqual(first, second)
        width, height = struct.unpack(">II", first[16:24])
        self.assertEqual((width, height), (1200, 630))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "python.png")
            self.assertTrue(og_card.write_hub_png(path, "PYTHON", 3, "2026-10-28"))
            self.assertGreater(os.path.getsize(path), 1000)


if __name__ == "__main__":
    unittest.main()
