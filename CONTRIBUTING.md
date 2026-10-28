# Contributing to RemoteJob VN

Thanks for helping people in Vietnam find remote work! The easiest contributions are adding a company,
fixing a fact, or reporting a broken job link.

Repository: https://github.com/quocdat029x/remotejob-vn

## Ground rules

1. **Public facts only.** Every company needs at least one public source URL (careers page, job post, blog post).
   Never add personal data: no names of individuals, emails, phone numbers, CVs, private notes, ratings or scores.
2. **Remote-first and hires in Vietnam.** The company must allow fully remote (or remote-friendly) work for people
   based in Vietnam, either as a direct hire, via an EOR, or as a contractor.
3. **No gambling.** Gambling, betting, casino and iGaming companies are not accepted (enforced by `scripts/policy.py`).
4. **Be neutral.** Describe policies factually; avoid marketing language.

## Add or edit a company

1. Fork https://github.com/quocdat029x/remotejob-vn and create a branch.
2. Edit `data/companies.json` (or use the "Suggest an edit" link on any company page). Fields:

| Field | Required | Notes |
| --- | --- | --- |
| `slug` | yes | ASCII lowercase with hyphens, unique, becomes `/cong-ty/<slug>/` |
| `name` | yes | Official company name |
| `website` | no | `https://…` or `null` |
| `careers_url` | yes | Public careers page |
| `group` | yes | `A` = Vietnamese company / VN entity, `B` = international company |
| `hq` | yes | Headquarters city/country |
| `remote_policy` | yes | Short factual description |
| `vn_hiring_mode` | yes | Direct hire, EOR, contractor, freelance, via agency/platform, or "not verified" |
| `hires_roles` | yes | Tags such as `devops`, `sre`, `platform`, `backend`, `data`, `ai-infra` |
| `timezone_note` | yes | e.g. "VN hours", "overlap 2h with EU" |
| `salary_public` | no | Only if published by the company |
| `source_urls` | yes | One or more public URLs that back the facts |
| `verified` | yes | `true` only if a source explicitly confirms remote hiring in Vietnam |
| `last_checked` | yes | `YYYY-MM-DD` |
| `kind` | no | `employer` (default when omitted) or `aggregator` for a job board. Aggregator jobs stay on the company page and are omitted from default mixed listings. See `docs/JOB_FILTER_RULES.md`. |

3. If the company uses a public ATS, add an entry to `data/sources.json` so jobs refresh automatically:

```json
{"slug": "example", "ats": "greenhouse", "token": "example", "endpoint": "https://boards-api.greenhouse.io/v1/boards/example/jobs", "method": "api", "last_checked": null, "status": "ok"}
```

Supported `ats` values with APIs: `greenhouse`, `lever`, `ashby`, `workable`, `recruitee`.

4. Run the checks locally:

```bash
python3 scripts/validate.py
python3 scripts/build.py && python3 scripts/check_jsonld.py
```

5. Open a pull request. The `validate` workflow runs the same checks. Use English for commit messages and PR text.

## Report a problem

Open an issue: https://github.com/quocdat029x/remotejob-vn/issues — broken link, wrong fact, closed job, or a
company that should be removed. Please include the page URL and a public source.

## Code contributions

- Python 3.10+, stdlib only (Pillow optional for images). Keep the site framework-free.
- Budgets: CSS < 30 KB, JS < 20 KB, no web fonts, no third-party scripts, no tracking.
- Every page must work without JavaScript.
- Code, comments, docs and commit messages are in English; user-facing site text is Vietnamese-first with English under `/en/`.
