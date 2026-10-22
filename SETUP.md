# Setting up RocketApply for yourself

This guide takes you from a fresh clone to your first tailored CV and cover letter.
The repository ships an invented person, **Alex Morgan**, in `profile.example/`.
You will copy that folder and replace Alex with yourself.

Rough time: 20 minutes for install and keys, 1–2 hours for your profile. The
profile is the part that decides how good the CVs and letters are, so it is worth
the time.

- [Step 1: Install](#step-1-install)
- [Step 2: API keys](#step-2-api-keys)
- [Step 3: Create your profile](#step-3-create-your-profile)
- [Step 4: Your experience, projects and education](#step-4-your-experience-projects-and-education)
- [Step 5: Your skills and numbers](#step-5-your-skills-and-numbers)
- [Step 6: Your writing voice](#step-6-your-writing-voice)
- [Step 7: What letters must never say](#step-7-what-letters-must-never-say)
- [Step 8: Validate and sync](#step-8-validate-and-sync)
- [Step 9: Your job search](#step-9-your-job-search)
- [Step 10: First run](#step-10-first-run)
- [Keeping your data private](#keeping-your-data-private)

---

## Step 1: Install

You need **Python 3.11 or newer**, `make` and `git`. Docker is optional (for the
local search engine, see step 2). macOS and Linux work as is; on Windows use WSL.

```bash
git clone <this repository's URL> rocketapply
cd rocketapply
make venv        # creates .venv and installs everything
make setup       # creates profile/, .env, config/job_search.yaml and
                 # config/target_companies.csv from the examples (never overwrites)
make fonts       # downloads the free CV fonts into assets/fonts
make test        # should end with every test passing; no network needed
```

Always run things through `make ...` or `.venv/bin/python`. If you want the
`pitwall` command in your shell, run `source .venv/bin/activate` first.

---

## Step 2: API keys

All keys go in `.env` (created by `make setup`). `.env` is gitignored, so it never
gets committed. **Every service below is free and none needs a credit card.**

Only **Groq** is needed to write CVs and letters. Everything else is optional: a
missing key just skips that source, and the app tells you which ones it skipped.

| key in `.env` | what it is for | needed? |
|---|---|---|
| `GROQ_API_KEY` | the AI that reads postings and writes letters | **yes** |
| `GROQ_API_KEY_2`, `GROQ_API_KEY_3` | more letters per day | optional |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | the biggest job source (9 countries) | recommended |
| `JOOBLE_API_KEY_US` | US jobs | optional |
| `ITJOBS_API_KEY` | Portuguese IT jobs | optional |
| `FINDWORK_API_KEY` | remote-heavy tech jobs | optional |
| `HUNTER_API_KEY` | finding a work email, one click at a time | optional |
| `GITHUB_TOKEN` | public commit emails for people search | optional |
| `SERPER_API_KEY` | backup Google search | optional |

### Groq (required)

1. Go to https://console.groq.com and sign up (Google or GitHub login works).
2. Open **API Keys** in the left menu and click **Create API Key**. Name it
   anything, for example `rocketapply`.
3. Copy the key (it starts with `gsk_`). Groq shows it only once.
4. Paste it into `.env`: `GROQ_API_KEY=gsk_...`
5. Check it works: `make groq-check`. It lists the models your key can use and
   confirms the default one is available.

One free key allows about 200,000 tokens a day, which is roughly ten CV + letter
pairs. A CV alone is cheap (about 2,600 tokens). If you want more per day, create
extra keys **on separate Groq accounts** (limits are per organisation, so two keys
on one account share one limit) and put them in `GROQ_API_KEY_2` and
`GROQ_API_KEY_3`. The app spreads work across them automatically.

If Groq ever says a model no longer exists, run `make groq-check` and set
`LLM_MODEL=` in `.env` to one it lists.

### Adzuna (recommended)

1. Go to https://developer.adzuna.com and click **Register**.
2. After confirming your email, open your dashboard. It shows an **Application ID**
   and an **Application Key**.
3. Put them in `.env`:
   ```
   ADZUNA_APP_ID=12345678
   ADZUNA_APP_KEY=abcdef...
   ```

The free tier allows 250 calls a day, and the app paces itself to stay inside it.

### Jooble (optional, US jobs)

1. Go to https://jooble.org/api/about and fill in the short form.
2. The key arrives by email. Put it in `JOOBLE_API_KEY_US=`.

### ITJobs.pt (optional, Portugal)

1. Go to https://www.itjobs.pt/api, enter your email, and the key is emailed to you
   straight away.
2. Put it in `ITJOBS_API_KEY=`.

### Findwork (optional, remote tech jobs)

1. Sign up at https://findwork.dev, then open https://findwork.dev/developers/.
2. Copy the API token into `FINDWORK_API_KEY=`.

### Hunter (optional, email finder)

1. Sign up at https://hunter.io (free plan: 50 credits a month).
2. Open **API** in your account settings (https://hunter.io/api-keys) and copy the
   key into `HUNTER_API_KEY=`.

Hunter is never called automatically. It only runs when you click its button for
one person, and each click costs one credit only if it finds an address.

### GitHub token (optional)

Raises GitHub's limit from 60 to 5,000 requests an hour for the people search.

1. Go to https://github.com/settings/tokens and click **Generate new token
   (classic)**.
2. Give it a name and an expiry, and **tick no scopes at all**. It only reads
   public data.
3. Copy it into `GITHUB_TOKEN=`.

### Serper (optional)

https://serper.dev gives 2,500 free Google searches once (they do not refill).
Sign up, copy the key from the dashboard into `SERPER_API_KEY=`. The app keeps a
reserve and only uses it when the free search engines fail.

### Local search engine: SearXNG (optional, no key)

Company research and the people search work much better with a local SearXNG,
which needs Docker:

```bash
make searxng         # starts it on http://localhost:8888 (creates its secret on first run)
make searxng-check   # proves it answers
make searxng-stop    # stops it
```

Without it, searches fall back to DuckDuckGo, which is slower and supports fewer
search operators.

### Local AI: Ollama (optional, no key)

Ollama runs a small model on your own computer. RocketApply uses it as a fallback
when Groq is out of quota, and as an independent fact-checker for letters.

1. Install Ollama from https://ollama.com.
2. Run `python scripts/setup_ollama.py` once. It downloads `qwen2.5:7b` (about
   5 GB) and creates the `pitwall-qwen2.5` model the app expects.

It is slow on a laptop without a GPU (minutes per batch), so think of it as a
backup.

---

## Step 3: Create your profile

`make setup` copied `profile.example/` to `profile/`. **Everything in `profile/`
is about you, and it is gitignored.** Each file starts with comments that explain
every field; read them as you go. Alex's data is there to show the shape, so
replace it all.

| file | what goes in it | effort |
|---|---|---|
| `personal.yaml` | name, contact details, title line, languages, what you are looking for | 5 min |
| `experience.yaml` | every job, with its bullets exactly as they should print | 30 min |
| `projects.yaml` | at least 8 projects, 2 short bullets each | 30 min |
| `education.yaml` | degrees, institutions, coursework | 10 min |
| `skills.yaml` | every skill, which CV row it goes in, how confident you are, and proof | 20 min |
| `metrics.yaml` | every number you quote, and how you measured it | 10 min |
| `evidence.yaml` | 5–8 short stories about your work, for cover letters | 20 min |
| `style.yaml` | your writing samples and old cover letters | 15 min |
| `forbidden.yaml` | things letters must never claim or mention | 10 min |
| `summaries.yaml` | one-sentence summaries per role family | 5 min |
| `companies.yaml` | your own notes on companies you care about | optional |
| `layout.yaml` | the CV frame; you only edit the experience entries list | 2 min |
| `taxonomy.yaml` | the tag vocabulary; add tags here before using them | as needed |

**How the pieces connect.** Everything has an `id`. Skills point to the bullets
that prove them (`evidence: [northwind.b1]`), bullets point to the numbers they
quote (`metrics: [m.northwind.error]`), cover-letter stories point to the bullets
they are about (`source_refs`). The validator checks every link, so you cannot end
up with a skill on your CV that nothing supports.

Work file by file in the order below, and run `make validate-profile` often. It
tells you exactly what is wrong and how to fix it.

**`personal.yaml`.** Straightforward. Two fields to think about:

- `target_role`: one or two sentences on what you want. The job search uses it to
  score each posting's fit.
- `work_authorization_policy`: if you do not want letters to mention visas or work
  permits at all, keep `never_mention` (and keep the matching topics in
  `forbidden.yaml`). If you want them mentioned, write the sentence in
  `work_authorization` and remove the topics from `forbidden.yaml`.

---

## Step 4: Your experience, projects and education

The CV is a fixed one-page design. Experience and education print the same way on
every CV. Only the projects, the skills rows and pre-approved bullet rewordings
change per job.

### `experience.yaml`

- One entry per job, newest first. Give each a short `id` (`acme`, `uni_lab`).
- `bullets`: write each one **exactly as it should print**. One sentence, plain
  double-quoted string. Start with a verb, include what you measured against.
- `rendered_lines`: how many lines the bullet takes on the CV (1 or 2). Guess, then
  run `make validate-profile`: it tells you the right number.
- `tags`: at least 3 from `taxonomy.yaml`. These are how a posting is matched to
  your work.
- `strength`: `strong`, `medium` or `supporting`.
- `use_for`: which role families this bullet suits. The families are
  `data_science`, `machine_learning`, `data_engineering`, `analytics`, `research`,
  `software`, `quantitative`.
- `variants` (optional): a rewording for some role families. It must take the
  **same number of lines** as the original. RocketApply never writes new bullet
  text; it only picks between yours.

**Then update `layout.yaml`**, `sections → experience → entries`: one line per job,
in the same order, with its number of bullets:

```yaml
    entries:
      - {id: acme,    bullets: 3}
      - {id: uni_lab, bullets: 2}
```

The experience section has a budget of 17 lines (`line_budget`). Count: each job
takes 1 title line plus its bullet lines. If you have more jobs than fit, keep the
most relevant ones or shorten bullets to one line.

### `projects.yaml`

This is the part that changes per job: RocketApply picks the **3 projects** that
fit each posting best. Rules (all checked by the validator):

- **at least 8 projects**, so there is a real choice,
- **exactly 2 bullets** per project,
- every bullet **55–95 characters**, so each project takes exactly 3 lines,
- project name plus link label at most 90 characters.

Other useful fields:

- `readme_state`: `ok`, `stub` or `none`. If the repository's README is weak, the
  CV keeps the project but drops the GitHub link.
- `conflicts_with`: experience bullet ids describing the same work, so both never
  print on one page.
- `team_size` and `role_note`: be honest about team projects. Letters use this.

University projects, hackathons, Kaggle competitions and personal tools all count.

### `education.yaml`

Degrees, dates, coursework. `end_label` overrides how the end date prints (for
example `"expected Jul 2027"`). The `tags` on courses help match postings that ask
for something you studied but have not used in a job.

---

## Step 5: Your skills and numbers

### `skills.yaml`

**The rows** at the top are the four skill lines on the CV:

- `row.programming` (1 line, 95 characters): languages,
- `row.methods` (2 lines, 195 characters): techniques,
- `row.tools` (2 lines, 195 characters): libraries and tools,
- `row.spoken` (1 line, fixed): your languages. Edit `fixed_text`.

`pinned` items always print; the rest are chosen per job.

**The skills list** has one record per skill. The key field is `confidence`, which
is how the app stays honest:

| confidence | meaning | needs |
|---|---|---|
| `high` | you have used it properly, more than once | 2+ evidence ids |
| `medium` | you have used it for real | 1+ evidence id |
| `low` | some familiarity; never printed on the CV | `low_phrasing`: how a letter may mention it |
| `none` | **a gap**: you do not have it | nothing. It never prints, and letters are forbidden to claim it |

`evidence` lists the ids that prove the skill: experience bullets (`acme.b1`),
project bullets (`proj.x.b2`) or degrees (`edu.msc`).

Add the skills you **do not** have but often see in postings as `confidence: none`.
That stops letters from closing the gap with a bluff, and it doubles as a learning
list.

`aliases` are other names a posting might use (`sklearn` for scikit-learn).

### `metrics.yaml`

Every number on your CV or in a letter must be here, with:

- `claim`: the words exactly as they should print (`"cut weekly forecast error 18%"`),
- `method`: how you measured it. Required; this is your answer in an interview.

A bullet that quotes a number lists the metric id in its `metrics:` field. The
letter checker rejects any number that is not somewhere in your profile, so the AI
can never invent a figure for you.

### `evidence.yaml`

5–8 stories that cover letters are built from. Each has:

- `facts`: 3–6 plain, checkable statements. The **only** things a letter may assert
  about this story.
- `story`: a few sentences in your own words about what was hard or what you
  learned. This is what stops letters sounding machine-written.
- `source_refs`: the bullet ids the story is about.
- `use_for`: role families it suits.

---

## Step 6: Your writing voice

**`style.yaml` matters more than any other file for how letters sound.** The AI
copies real examples far better than it follows descriptions.

- `writing_samples`: at least one paragraph you wrote yourself (a report, an essay,
  an email). Paste it unedited.
- `exemplars`: whole cover letters you have written. Mark your best ones
  `verdict: good` and one or two weaker ones `verdict: avoid`. Paste the full text.
  The validator warns until you have both kinds.
- `spelling`: `british` or `american`.
- `banned_phrases`: phrases you never want to see. The list in the example is a
  good start; add your own pet hates.
- `voice_notes`, `preferred_openings`, `signature_moves`: short notes on your style.

Company names inside your exemplars are automatically blocked from appearing in
other letters, so you do not need to anonymise them.

If you have never written a cover letter, write one by hand for a job you like
before you start. It is the single best input you can give.

---

## Step 7: What letters must never say

`forbidden.yaml` is checked on every letter. A draft that breaks a rule is rewritten
or held for your review.

- `never_claim`: things you cannot back up (leading a team, years of experience you
  do not have, tools you have not used).
- `never_mention`: whole topics a letter must not raise, even if the posting asks.
  Visa status is the usual one; delete the lines if you want it mentioned.
- `never_say`: framings to avoid ("an internship was a permanent job").
- `not_my_work`: parts of team projects someone else did. `block_terms` are the
  phrases the checker looks for.
- `never_claim_specifically`: a skill you have, but not in a particular job
  ("reinforcement learning in my internship" when you only used it at university).
- `gated_verbs`: verbs that overstate a junior role (led, owned, founded). Blocked
  unless one of your own bullets already uses that verb.

`summaries.yaml` holds one or two sentences per role family that a letter's opening
can draw from. `companies.yaml` is optional: your own notes on why a company
interests you. Without notes, `pitwall apply research <Company>` can draft some from
the company's public pages, and otherwise the letter simply does not praise the
company.

---

## Step 8: Validate and sync

```bash
make validate-profile
```

Fix every **error** (the CV would break or a link is missing). **Warnings** are
advice. Typical first-run errors and fixes:

| message says | fix |
|---|---|
| `declared N lines, wraps to M` | set `rendered_lines` to the number it reports, or shorten the bullet |
| a project bullet is too long or `short bullets waste the line` | rewrite it to 55–95 characters |
| `tag '...' is not in taxonomy.yaml` | add the tag under `canonical` in `taxonomy.yaml`, or use an existing one |
| an evidence or metric id does not exist | fix the id, or add what it refers to |
| `... is not listed in layout.yaml` | add the job to `layout.yaml → sections → experience → entries` |
| `LINE-NEUTRALITY FAIL` | a variant wraps to a different number of lines than its bullet; reword it |
| `TODO_ME marker(s) awaiting your input` | fill in the fields marked `TODO_ME` |

Then look at a real CV, with no job and no AI involved:

```bash
.venv/bin/pitwall apply preview data_science    # or machine_learning, data_engineering, ...
```

The PDF path is printed. If it looks right, build the files the job search uses:

```bash
make profile-sync    # writes config/my_skills.yaml and config/my_profile.md
```

Run `make profile-sync` again whenever you change your profile, and
`make job-rerank` to re-score stored jobs.

---

## Step 9: Your job search

**`config/job_search.yaml`**: where and what you are looking for: countries,
preferred cities, remote or not, role labels, seniority, years of experience, work
authorisation and score weights. Every field is explained in the file. You can also
edit it in the app under **Settings**.

**`config/target_companies.csv`**: employers you want to watch, with priority
A/B/C. Replace the examples with your own list, then run:

```bash
make job-targets-ats   # finds each company's public job board (Greenhouse, Lever, ...)
```

**`config/outreach_templates.yaml`**: the LinkedIn connection notes and follow-up
messages the Applications page drafts. **Rewrite them in your own words.**

**Optional, people search.** If you want the people search, run
`.venv/bin/pitwall init`. It creates `config/companies.csv` and `config/roles.csv`
with explanations inside. Both are gitignored.

---

## Step 10: First run

```bash
make rocketapply      # open http://localhost:8502
```

1. **Search** → *Fetch new jobs*. The first collection takes a few minutes.
2. Tick a few jobs that look good → they move to **Selected**.
3. On **Selected**, choose *CV + letter* and click **Generate**.
4. Watch **Generate**, then read every letter on **Review**. Edit, approve or
   regenerate.
5. Export the approved ones to CSV, apply, and mark them applied on
   **Applications**.

Read every letter before you send it. The checks stop invented facts, but only you
can tell whether it sounds like you. If letters feel generic, the fix is almost
always more of your own writing in `style.yaml` and better stories in
`evidence.yaml`.

To collect jobs every morning automatically on a Mac, follow the instructions at the
top of `scripts/launchd/com.pitwall.jobsearch.plist`.

---

## Keeping your data private

These are gitignored and must never be committed:

- `profile/` (your CV data, letters and writing samples),
- `.env` (your API keys),
- `config/job_search.yaml`, `config/target_companies.csv`, `config/my_skills.yaml`,
  `config/my_profile.md`, `config/companies.csv`, `config/roles.csv`,
- `data/` (the database), `output/` (your CVs and letters), `run/` (logs).

Before every `git push`, run `git status` and check none of them is listed. If you
fork this repository and want to keep your profile under version control, keep it in
a **separate private repository** and point the app at it with
`ROCKETAPPLY_PROFILE_DIR=/path/to/private/profile` in `.env`.

If a key ever does get committed, revoke it on the provider's website straight away
and create a new one. Deleting the commit is not enough.
