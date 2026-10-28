"""llmstxt.org documents and robots.txt. Public facts only. Stdlib."""

# Crawlers called out by name. The `*` group still allows the site and keeps
# the jobs-index disallow; each named agent repeats that so a specific group
# does not drop the disallow (robots uses the most specific group only).
NAMED_AGENTS = (
    "Mediapartners-Google",
    "AdsBot-Google",
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "PerplexityBot",
    "Google-Extended",
    "Applebot-Extended",
    "Bingbot",
)


def robots_txt(site):
    site = site.rstrip("/")
    blocks = [
        f"# Machine-readable summary for assistants: {site}/llms.txt",
        "",
        "User-agent: *",
        "Allow: /",
        "Disallow: /data/jobs-index.json",
        "",
    ]
    for agent in NAMED_AGENTS:
        blocks.extend([
            f"User-agent: {agent}",
            "Allow: /",
            "Disallow: /data/jobs-index.json",
            "",
        ])
    blocks.extend([
        f"Sitemap: {site}/sitemap.xml",
        f"Sitemap: {site}/sitemap-vi.xml",
        f"Sitemap: {site}/sitemap-en.xml",
        "",
    ])
    return "\n".join(blocks)


def llms_txt(site, repo, role_pages):
    """Short llmstxt.org document. `role_pages` is a list of (slug, vi, en)."""
    site = site.rstrip("/")
    repo = repo.rstrip("/")
    roles = "\n".join(
        f"- [{vi} / {en}]({site}/viec-lam-remote/{slug}/): remote {en} roles open to people in Vietnam"
        for slug, vi, en in role_pages
    )
    return f"""# RemoteJob VN

> RemoteJob VN is a Vietnamese-first directory of remote-first companies that hire people in Vietnam, with an English mirror under /en/. It lists public careers pages and the remote jobs currently open on them. The site is free, open source, and community maintained.

Jobs are read from public applicant-tracking feeds (Greenhouse, Lever, Ashby, Workable, Recruitee, and other public JSON or XML feeds when a company uses one). Sources with no feed are checked by URL once a week. Listings that disappear are removed from the index and kept as noindex pages for 30 days. There is no sign-in and no private applicant data.

## Vietnamese

- [Trang chủ]({site}/): search, Vietnam/APAC jobs, Vietnamese companies
- [Việc làm]({site}/viec-lam/): open remote jobs, paginated
- [Việc làm theo vai trò]({site}/viec-lam-remote/): role landing pages
- [Công ty]({site}/cong-ty/): company directory
- [Công cụ]({site}/cong-cu/): tools for remote workers, affiliate slots labeled
- [Đăng tin]({site}/dang-tin/): sponsored listing info for employers
- [Giới thiệu]({site}/gioi-thieu/): about, criteria, data license
- [Chính sách bảo mật]({site}/chinh-sach-bao-mat/): Cloudflare Web Analytics, affiliates, advertising
- [Điều khoản]({site}/dieu-khoan/): disclaimer
- [Liên hệ]({site}/lien-he/): GitHub issues only
- [Ủng hộ]({site}/ung-ho/): optional donations, VietQR and Buy Me a Coffee

## Roles

{roles}

## English

- [Home]({site}/en/): English mirror of the home page
- [Jobs]({site}/en/viec-lam/): open remote jobs
- [Roles]({site}/en/viec-lam-remote/): role landing pages
- [Companies]({site}/en/cong-ty/): company directory
- [Tools]({site}/en/cong-cu/): tools page
- [Post a job]({site}/en/dang-tin/): sponsored listings
- [About]({site}/en/gioi-thieu/): about and license
- [Privacy]({site}/en/privacy/): privacy policy
- [Terms]({site}/en/terms/): terms and disclaimer
- [Contact]({site}/en/contact/): GitHub issues only
- [Support]({site}/en/support/): optional donations, Buy Me a Coffee and VietQR

## Data

- Jobs refresh daily from public, unauthenticated ATS APIs at about one request per second. HTML-only job URLs are checked weekly; a 404, 410, or redirect to a generic careers page marks the job removed. Network errors leave the job unchanged.
- Company facts are public and each record has source URLs and a last-checked date. Gambling, betting, casino, and iGaming companies are excluded.
- A compact full listing of companies and current direct-employer jobs is at [{site}/llms-full.txt]({site}/llms-full.txt).

## License

- Data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribute RemoteJob VN and link to the page you used.
- Code: MIT, in the same repository.

## Optional

- [Repository]({repo}): source, issues, and pull requests
- [Contributing]({repo}/blob/main/CONTRIBUTING.md): how to add or correct a company
- [Sitemap]({site}/sitemap.xml): sitemap index
"""


def _one_line(text):
    return " ".join((text or "").split())


def llms_full_txt(site, companies, jobs, today):
    """Compact public listing. `jobs` must already be active and non-aggregator."""
    site = site.rstrip("/")
    company_lines = []
    for company in sorted(companies, key=lambda c: c["name"].lower()):
        company_lines.append(
            f"- [{company['name']}]({site}/cong-ty/{company['slug']}/): "
            f"{_one_line(company.get('remote_policy'))} "
            f"VN hiring: {_one_line(company.get('vn_hiring_mode'))}. "
            f"Careers: {company.get('careers_url')}"
        )
    job_lines = []
    for job in jobs:
        loc = _one_line(job.get("location")) or "location not stated"
        remote = job.get("remote") or "unknown"
        job_lines.append(
            f"- [{_one_line(job.get('title'))}]({site}{job['path']}) — {job.get('company_name')} — "
            f"{loc} — remote: {remote} — checked {str(job.get('last_checked') or '')[:10]}"
        )
    return (
        f"# RemoteJob VN — companies and open jobs\n\n"
        f"> Public facts only, generated {today}. {len(companies)} companies and "
        f"{len(jobs)} open jobs from direct employers (job-board aggregators are omitted from the job list). "
        f"English pages use the same path under {site}/en/.\n\n"
        f"## Companies\n\n"
        + "\n".join(company_lines)
        + "\n\n## Jobs\n\n"
        + ("\n".join(job_lines) if job_lines else "- None.\n")
        + "\n"
    )
