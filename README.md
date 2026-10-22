# 🚀 RocketApply

A personal job-application assistant that runs on your own laptop. It:

1. **collects** job postings from free job boards and company career pages,
2. **ranks** them against your CV and what you are looking for,
3. **writes** a tailored one-page CV and cover letter for the jobs you pick, using
   only facts you wrote down yourself,
4. **tracks** every application, and
5. **finds people to contact** at the companies you applied to.

Everything runs locally with free API keys. Nothing is ever sent or posted for you.

> **New here? Follow [SETUP.md](SETUP.md).** It walks through every step: install,
> API keys, writing your own profile, and the first run. Plan about two hours, most
> of it on writing your profile.

## Quickstart (if you have done it before)

```bash
make venv              # .venv, requirements and an editable install
make setup             # copies the example profile, .env and config (never overwrites)
# edit .env (API keys) and everything in profile/
make validate-profile  # checks your profile fits the one-page CV
make profile-sync      # builds config/my_skills.yaml + config/my_profile.md from profile/
make fonts             # downloads the CV fonts once
make test              # the whole test suite, no network needed
make rocketapply       # the app, on http://localhost:8502
```

## What is yours and what is shared

The repository ships **an invented person, "Alex Morgan"**, so everything works out
of the box. You replace Alex with yourself. Your own files are all gitignored, so you
can pull updates without ever committing personal data:

| your file (gitignored) | made from | what it is |
|---|---|---|
| `profile/` | `profile.example/` | the single source of truth for your CV and letters |
| `.env` | `.env.example` | API keys |
| `config/job_search.yaml` | `config/job_search.example.yaml` | countries, roles, seniority, visa, score weights |
| `config/target_companies.csv` | `config/target_companies.example.csv` | employers you want to watch |
| `config/my_skills.yaml`, `config/my_profile.md` | `make profile-sync` | your skills and CV text, for job scoring |
| `data/`, `output/`, `run/` | the app | database, generated CVs and letters, run logs |

If `profile/` does not exist the app falls back to `profile.example/`, so a fresh
clone runs, but every CV it produces will say "Alex Morgan". You can also point the
app at a profile anywhere on disk with `ROCKETAPPLY_PROFILE_DIR=/path/to/profile`.

## The app

`make rocketapply` → http://localhost:8502. The navigation follows the process from
left to right, and each page shows how many jobs are waiting on it:

**Search → Selected → Generate → Review → Applications**

| page | what it is for |
|---|---|
| **Search** | every collected job, with a search box, filters, a score and the reasons behind it. *Fetch new jobs* runs a collection. Tick jobs to select them. |
| **Selected** | choose CV only or CV + cover letter, see how many fit in today's free LLM budget, add a hint per letter, then Generate. |
| **Generate** | live progress for each job: the skills found in the posting, the projects chosen and why, the letter as it is written, the checks. A run keeps going if you close the tab. |
| **Review** | read and edit the letter, preview the CV and letter PDFs, then Approve, Regenerate or mark Not interested. Export approved applications to a CSV with links and file paths. |
| **Applications** | mark applications as sent, then find people at that company (recruiters, hiring managers, alumni) with ready-to-edit connection notes. Nothing is ever sent for you. |
| **How it works** | sources, keys, scoring weights, run history and quality numbers. |
| **Settings** | the search profile, skills, target companies, who to contact, and a check of `profile/`. |

*Not interested* removes a job everywhere and stops later searches from bringing it
back. Generated files go to `output/`, one folder per application.

## How the CV and letter are made

> **The model decides what is relevant. The program guarantees what is true.**

**The CV is a frozen one-page frame.** The layout is always
`CONTACT → SKILLS → EXPERIENCE → PROJECTS → EDUCATION`. Your experience and
education print the same on every CV. Only three things change per job:

- which **3 of your projects** appear (you write at least 8),
- what fills each **skills row**, and
- which **pre-approved rewording** (variant) a bullet uses.

Every piece of text declares how many lines it takes, and `make validate-profile`
checks it, so the CV always fits exactly one page. `make calibrate` re-measures the
frame with the real fonts.

**The truth layer.** A cover letter may only state facts from `profile/`. Before
anything reaches `output/`, deterministic checks block:

- a number that is not in your profile (`metrics.yaml`),
- a skill you marked `confidence: none` or listed as a gap,
- anything in `forbidden.yaml`: claims you must never make, topics never to raise
  (e.g. visa status), work that was a teammate's, inflated verbs like "led" or
  "founded",
- words borrowed from your example letters (company names in `style.yaml`
  exemplars must not leak into a letter for another company).

A blocked draft is rewritten or saved as `NEEDS_REVIEW` with the problem sentences
listed. A second model can fact-check the letter (Advanced, on Selected). Every
application ships a `provenance.json` that lists which profile entries it used.

**Your voice.** Letters copy the rhythm of real letters you wrote far better than
they follow instructions, so `profile/style.yaml` holds your own writing samples and
whole letters marked `good` or `avoid`. This matters more than any other setting for
how the letters sound. See [SETUP.md, step 6](SETUP.md#step-6-your-writing-voice).

### Command line

Everything the app does also works from a terminal (`pitwall` is installed into
`.venv` by `make venv`; activate it with `source .venv/bin/activate`):

```bash
pitwall apply preview data_science     # render a CV with no job and no model
pitwall apply jobs                     # list stored jobs with their ids
pitwall apply analyze --job 930        # gap report for one job
pitwall apply generate --job 930       # CV + cover letter for one job
pitwall apply research Spotify         # cache public notes about a company for letters
make job-search                        # poll every source, filter, rank
make job-rerank                        # re-rank stored jobs after editing your profile
make job-calibrate                     # how well the score agrees with your ratings
make job-targets-ats                   # find the public job board of each target company
make cli                               # every command
```

## The job search

```
sources ─► normalise ─► dedupe ─► hard filters ─► score + reasons ─► inbox ─► tracker
```

**Sources**, all free. Each can be switched on or off in Settings:

| kind | sources |
|---|---|
| aggregators | Adzuna (DE NL FR GB CH IT ES US SG), Jooble (US), Arbeitnow (DE, UK), Workable search, Findwork |
| official portals | EURES (EU + CH), JobTech (SE), MyCareersFuture (SG), ITJobs.pt (PT) |
| country boards | GermanTechJobs, SwissDevJobs, DevITJobs UK and NL |
| remote boards | Himalayas, Jobicy, Remote OK |
| company boards | the job board of every target company (Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Recruitee, Personio, Teamtailor), plus boards found automatically in other postings |

Sources that need a key are skipped (and say so) until you add one. Keyless sources
obey `robots.txt`. No LinkedIn scraping, no logins, no browser impersonation.

**Scoring** has eight parts: role, experience, skills, location, visa, direction,
company and CV match. Only what a posting *states* can reject a job ("3+ years
required", "we cannot sponsor"). An unknown never does. Rejected jobs stay visible
under *Filtered out* with their reason. The UK and NL sponsor registers are used to
mark employers that sponsor visas.

To run the search every morning on a Mac, see
`scripts/launchd/com.pitwall.jobsearch.plist` (instructions inside).

## Configuration

Precedence: **command-line flags > `.env` > `config/settings.yaml` > code defaults.**

- `config/settings.yaml`: thresholds, budgets and weights. Committed, safe to edit.
- `.env`: API keys and machine-specific choices. **Never committed.**
- `config/job_search.yaml`: your search. Edit it in the app under Settings.

Config is validated at startup, so a typo fails loudly instead of quietly mid-run.

### LLM providers

| provider | cost | notes |
|---|---|---|
| `groq` | free tier, no card | **main provider.** `GROQ_API_KEY`. Up to three keys in parallel |
| `ollama` | free, local | fallback and independent fact-checker. `python scripts/setup_ollama.py` once |
| `zai`, `deepseek` | optional | extra OpenAI-compatible providers, skipped without a key |

A CV costs about 2.6k Groq tokens, a CV + letter 18–21k, with the fact-check up to
60k. One free Groq key gives about 200k tokens a day, so roughly ten letters.

### Search providers (used by company research and people search)

| provider | cost | notes |
|---|---|---|
| `searxng` | free, self-hosted in Docker | `make searxng`. The only one that supports `site:` operators |
| `ddgs` | free, keyless, slow | the default fallback |
| `serper` | 2,500 one-off free credits | optional, `SERPER_API_KEY` |

## Privacy and guardrails

- **Nothing is sent for you.** RocketApply drafts notes and messages; you send them.
- **Search engines only.** It never opens LinkedIn profile pages, never logs in and
  never uses cookies.
- **Minimal data.** Name, public headline, employer, profile URL, location and your
  own notes. An email address only when you ask for one, person by person.
- **Retention.** `python scripts/purge_stale.py --apply` deletes people you never
  acted on after 180 days. *Delete & blocklist* removes a person for good.
- **Never publish `data/`, `output/`, `profile/` or `.env`.** They are gitignored.
  Run `git status` before every push.

## The people CSV columns

The people search reads `config/companies.csv` and `config/roles.csv`
(`pitwall init` creates both with comments). The column reference below is
generated from the code with `pitwall columns --write`.

<!-- BEGIN generated: csv-columns -->
<!-- generated by `pitwall columns`; edit src/pitwall/inputs.py, not this block -->

#### `config/companies.csv`

| column | type | rule | why it matters |
|---|---|---|---|
| `name` | text | required, unique (case-insensitive); a duplicate row is skipped | The canonical spelling. Everything keys on it. |
| `aliases` | pipe-separated | warned about when empty | How the company is written in the wild — season names, sponsor names, the short form people type. The single biggest lever on RECALL. |
| `negative_keywords` | pipe-separated | warned about when empty | Other organisations that share the name. The single biggest lever on PRECISION: 'McLaren Health Care' is a hospital network. |
| `linkedin_slug` | text | optional | Unused by search; kept for your own reference. |
| `domain` | text | optional | Used to guess the ATS board in `discover_ats.py`. |
| `series` | text | optional | Free text, shown in the UI. |
| `country` | text | optional | A candidate located here scores slightly higher. |
| `tier` | 1-3 | must be 1, 2 or 3; anything else defaults to 2 | Search priority. Tier 1 is searched first and most. |
| `active` | true/false | defaults to true | false keeps the row without searching it. |

#### `config/roles.csv`

| column | type | rule | why it matters |
|---|---|---|---|
| `title` | text | required, unique (case-insensitive); a duplicate row is skipped | The canonical spelling of the job. |
| `aliases` | pipe-separated | warned about when empty | What the same job is called elsewhere. |
| `family` | enum | required, and must be one of the active profile's role families | Groups roles for the coverage matrix and the heuristic layer. `pitwall validate` prints the legal values. |
| `seniority` | pipe-separated | each value must be in the profile's seniority ladder | Empty means any level. |
| `keywords` | pipe-separated | optional | Words that, in a snippet, suggest this really is the job — each is worth a few points in the heuristic layer. |
| `priority` | 1-3 | must be 1, 2 or 3; anything else defaults to 2 | Search priority within a company. |
| `active` | true/false | defaults to true | false keeps the row without searching it. |

With the `motorsport` profile, `family` must be one of:

> `data_science`, `data_engineering`, `strategy`, `performance`, `simulation`, `vehicle_dynamics`, `software`, `operations`, `leadership`

and each `seniority` value one of:

> `intern`, `graduate`, `junior`, `mid`, `senior`, `lead`, `head`, `executive`, `unknown`

Pipe-separated columns use `|` as the separator: `McLaren F1|McLaren Applied|MTC`.
<!-- END generated: csv-columns -->

## Development

```bash
make test        # hermetic: no network, uses profile.example/, never your data
make lint        # ruff
make typecheck   # mypy
```

An autouse fixture in `tests/conftest.py` blocks every non-local network call, and
the tests always run against `profile.example/`, so they pass the same on every
machine.

```
apps/rocketapply/   the Streamlit app: app.py, views/, rocket/ (background worker)
src/pitwall/        the engine
  apply/            CV + cover letter: selector, layout, truth layer, prompts, render
  jobsearch/        queries, filters, scoring, tracker
  sources/jobs/     job boards and ATS adapters
  search/           searxng · ddgs · serper, with a cache
  enrich/           finding a work email address from public sources
  scoring/          LLM scoring for the people search
profile.example/    the invented example profile you copy to profile/
config/             settings and example configs
scripts/            setup, validation and maintenance scripts
docker/searxng/     the local search engine container
tests/              unit and integration tests, with recorded fixtures
```

## Troubleshooting

| symptom | fix |
|---|---|
| `ImportError` mentioning `NoDecode` | you used the system Python. Use `make ...` or `.venv/bin/python` |
| The CV says "Alex Morgan" | `profile/` does not exist yet. Run `make setup` and edit it |
| `make validate-profile` reports errors | each error names the file, the id and the fix. Rendered line counts are the usual one |
| A job source says "skipped: no key" | add that key to `.env` (see SETUP.md), or ignore it |
| Generation stops with a Groq rate limit | the free tier's per-minute ceiling. Add `GROQ_API_KEY_2`/`_3`, or wait |
| Groq says a model does not exist | Groq retired it. `make groq-check` lists what your key can use; set `LLM_MODEL` |
| `... has no num_ctx set` | run `python scripts/setup_ollama.py`. This is a guard, not a bug |
| Company research or people search finds nothing | SearXNG is not running: `make searxng`, then `make searxng-check` |
| The CV PDF uses the wrong font | run `make fonts` |
