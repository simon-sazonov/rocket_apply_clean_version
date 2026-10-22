#!/usr/bin/env python
"""Feed `profile/` into the two files PitWall's job search actually reads.

    python3 scripts/profile_to_pitwall.py            # review only
    python3 scripts/profile_to_pitwall.py --apply    # write both files

`profile/` is the single source of truth for your CV and cover-letter data:
tagged bullets, honest confidence levels, evidence pointers, metrics with a
stated method. PitWall's job search wants the same facts in two other shapes:

    config/my_skills.yaml   §18-19 — skill inventory with proficiency + evidence,
                            mapped onto config/skills_vocab.yaml. Without it the
                            loader falls back to my_skills.example.yaml, where
                            every entry sits at a flat proficiency 2 and almost
                            nothing carries evidence.

    config/my_profile.md    §2.6 — prose CV, scored against each open posting for
                            a 0-100 fit. config/profile.md is still the shipped
                            template, so nothing is scoring today.

Both outputs are gitignored, so this writes personal files and touches no
repository content. Re-run it whenever profile/ changes; nothing is hand-edited
downstream, which is the point.

Two rules enforced here rather than left to whoever edits the output:

  * Work authorisation is never written. profile/forbidden.yaml carries a
    never_mention block for it, and config/profile.md's Constraints section
    invites exactly that - so the Constraints section is emitted without it.
  * confidence -> proficiency maps high=3, medium=2, low=1. Skills at
    confidence `none` are emitted only where profile/skills.yaml records an
    explicit user_override, and then at proficiency 1 with no evidence.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from pitwall.apply import resolve_profile_dir  # noqa: E402

PROFILE = resolve_profile_dir()
CONFIG = ROOT / "config"

PROFICIENCY = {"high": 3, "medium": 2, "low": 1}

#: profile/skills.yaml is usually finer-grained than config/skills_vocab.yaml, so
#: some skills need to be told where they land. This map is explicit on purpose:
#: fuzzy matching here would invent claims ("Azure OpenAI" is NOT cloud Azure), and
#: a near-miss would quietly undo a gap you declared.
#:
#: Anything not listed and not directly matched is dropped, which is the safe default:
#: a skill absent from the inventory reads as "missing" on a posting that asks for it.
EXTRA_MAP = {
    "skill.monte_carlo": "monte_carlo",
    "skill.time_series": "time_series",
    "skill.etl": "data_pipelines",
    "skill.data_quality": "data_pipelines",
    "skill.dimensional_modelling": "data_pipelines",
    "skill.parquet": "data_pipelines",
    "skill.hyperparameter_tuning": "optimization",
    "skill.optuna": "optimization",
    "skill.big_data": "spark",
    "skill.sparksql": "spark",
    "skill.system_design": "software_engineering",
    "skill.gymnasium": "reinforcement_learning",
    "skill.nltk": "nlp",
    "skill.bi": "bi_tools",
    "skill.powerbi": "bi_tools",
    "skill.matplotlib": "data_visualization",
    "skill.github_actions": "ci_cd",
    "skill.git": "git",
}
# A skill record in profile/skills.yaml can also say where it lands itself, which
# wins over this map:  {id: skill.kedro, name: Kedro, vocab: airflow, ...}
# and `vocab_note:` adds a note to the emitted line ("via Kedro, not Airflow").

#: Dropped, but a posting might genuinely name them. Surfaced as a suggestion rather
#: than silently mapped onto something adjacent.
WORTH_ADDING_TO_VOCAB = {
    "MongoDB", "Query Optimisation", "Model Explainability", "Transformers",
    "Experimental Design", "Clustering", "Entity Resolution", "Simulation",
}


def load(name: str):
    return yaml.safe_load((PROFILE / name).read_text(encoding="utf-8"))


def readable_evidence(profile_ids, projects, experience) -> list[str]:
    """Turn bullet ids into the short names a human would recognise."""
    names: dict[str, str] = {}
    for p in projects:
        short = p["name"].split("–")[0].split("(")[0].strip()
        for b in p.get("bullets") or []:
            names[b["id"]] = short
    for e in experience:
        for b in e.get("bullets") or []:
            names[b["id"]] = e["org"]
    out: list[str] = []
    for i in profile_ids:
        n = names.get(i) or ("MSc coursework" if i.startswith("edu.") else None)
        if n and n not in out:
            out.append(n)
    return out


def build_skills() -> tuple[str, list[str]]:
    vocab = yaml.safe_load((CONFIG / "skills_vocab.yaml").read_text(encoding="utf-8"))
    skills = load("skills.yaml")["skills"]
    projects, experience = load("projects.yaml"), load("experience.yaml")

    # Every spelling the vocabulary knows -> its canonical id.
    spelling_to_id: dict[str, str] = {}
    for vid, meta in vocab.items():
        for s in [meta["label"], *(meta.get("synonyms") or [])]:
            spelling_to_id.setdefault(s.lower(), vid)

    def vocab_id(s: dict) -> str | None:
        candidates = [s["name"], *(s.get("aliases") or [])]
        vid = s.get("vocab") or EXTRA_MAP.get(s["id"]) or next(
            (spelling_to_id[c.lower()] for c in candidates
             if c.lower() in spelling_to_id), None)
        if vid is not None and vid not in vocab:
            raise SystemExit(f"{s['id']} maps to '{vid}', "
                             f"which is not in config/skills_vocab.yaml")
        return vid

    # Vocabulary labels that would amount to claiming something in the gap map
    # (confidence: none). Emitting one is a bug, so it stops the run.
    gap_labels = {vocab[v]["label"] for v in (
        vocab_id(s) for s in skills
        if s.get("confidence") == "none" and not s.get("user_override")) if v}

    best: dict[str, dict] = {}
    unmatched: list[str] = []
    for s in skills:
        conf = s.get("confidence")
        override = bool(s.get("user_override"))
        if conf == "none" and not override:
            continue
        vid = vocab_id(s)
        if vid is None:
            unmatched.append(s["name"])
            continue
        prof = 1 if (conf == "none" or override) else PROFICIENCY.get(conf, 1)
        ev = [] if (conf == "none" or override) else readable_evidence(
            s.get("evidence") or [], projects, experience)
        prior = best.get(vid)
        if prior is None or prof > prior["proficiency"]:
            entry = {"skill": vocab[vid]["label"], "proficiency": prof}
            if s.get("years"):
                entry["years"] = s["years"]
            if ev:
                entry["evidence"] = ev
            if override:
                entry["_note"] = f"no evidence — {s['user_override']}"
            if s.get("vocab_note"):
                entry["_note"] = s["vocab_note"]
            best[vid] = entry

    leaked = {e["skill"] for e in best.values()} & gap_labels
    if leaked:
        raise SystemExit(
            "refusing to write: these are in profile/skills.yaml's gap map "
            f"(confidence none, no evidence) but reached the inventory: {sorted(leaked)}")

    by_cat: dict[str, list] = {}
    for vid, entry in best.items():
        by_cat.setdefault(vocab[vid].get("category", "other"), []).append(entry)

    lines = [
        "# Your skill inventory — GENERATED from profile/skills.yaml.",
        "#",
        "#   python3 scripts/profile_to_pitwall.py --apply",
        "#",
        "# Do not hand-edit: edit profile/skills.yaml and regenerate, or the CV and the",
        "# job scoring drift apart. proficiency is derived from `confidence` there,",
        "# where high=3 (2+ pieces of work, interviewable for 30 minutes), medium=2",
        "# (one real piece of work), low=1 (coursework or brief exposure).",
        "#",
        "# `evidence` is what a CV line could point to. A skill without it is one the CV",
        "# tailoring will not put forward, which is the behaviour you want.",
        "",
        "skills:",
    ]
    for cat in sorted(by_cat):
        lines.append(f"  # {cat}")
        for e in sorted(by_cat[cat], key=lambda x: (-x["proficiency"], x["skill"])):
            note = e.pop("_note", None)
            body = ", ".join(
                f"{k}: {yaml.safe_dump(v, default_flow_style=True).strip().removesuffix('...').strip()}"
                for k, v in e.items())
            lines.append(f"  - {{{body}}}" + (f"   # {note}" if note else ""))
        lines.append("")
    return "\n".join(lines), unmatched


MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def pretty_date(v) -> str:
    """YAML parses 2025-09 as a string but 2025-09-01 as a date; handle both."""
    t = str(v)
    parts = t.split("-")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{MONTHS[int(parts[1])]} {parts[0]}"
    return t


def build_profile_md() -> str:
    """A prose CV for the job search's AI fit score, built only from profile/."""
    personal, edu = load("personal.yaml"), load("education.yaml") or []
    exp, projects, skills = load("experience.yaml"), load("projects.yaml"), load("skills.yaml")["skills"]

    def row(r):
        return ", ".join(s["name"] for s in skills
                         if s.get("row") == r and s.get("printable")
                         and s.get("confidence") in {"high", "medium"})

    target = (personal.get("target_role") or "").strip() or (
        f"Graduate or junior {personal.get('title') or 'data'} roles.")

    education = []
    for school in edu:
        degrees = school.get("degrees") or []
        if degrees:
            for d in degrees:
                education.append(f"- {d['degree']}, {school['institution']} "
                                 f"({pretty_date(d.get('start', ''))} to {pretty_date(d.get('end', ''))})")
        elif school.get("note"):
            education.append(f"- {school['institution']}: {school['note']}")

    jobs = []
    for e in exp:
        period = f"{pretty_date(e.get('start', ''))} to {pretty_date(e.get('end', ''))}"
        context = " ".join(str(e.get("context") or "").split())
        bullets = " ".join(b["text"].rstrip(".") + "." for b in e.get("bullets") or [])
        jobs.append(f"**{e['role']}, {e['org']}** ({period}). {context} {bullets}".strip())

    top = [p for p in projects if p.get("strength") == "strong"] or projects[:3]
    proj_lines = [f"**{p['name'].split('–')[0].strip()}** — "
                  + " ".join(b["text"].rstrip(".") + "." for b in p["bullets"]) for p in top]

    relocate = ""
    if personal.get("willing_to_relocate"):
        relocate = "Willing to relocate"
        if personal.get("relocation_targets"):
            relocate += "; targets include " + ", ".join(personal["relocation_targets"][:4])
        relocate += "."
    languages = ", ".join(f"{lang['name']} ({lang['level']})" for lang in personal.get("languages") or [])

    return f"""# Target role

{target}

# Background

{chr(10).join(education)}

{chr(10).join(chr(10).join(['', j]) for j in jobs).strip()}

# Selected work

{chr(10).join('- ' + line for line in proj_lines)}

# Skills

Languages: {row('row.programming')}

Methods: {row('row.methods')}

Tools: {row('row.tools')}

# Constraints

Based in {personal.get('location', '')}. {str(personal.get('notice_period', '')).capitalize()}. {relocate}

Languages spoken: {languages}.

<!-- Work authorisation is deliberately not stated here when profile/forbidden.yaml
     lists it under `never_mention`. A constraint that is not stated is one the
     model is told not to invent. -->
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the files")
    args = ap.parse_args()

    skills_yaml, unmatched = build_skills()
    profile_md = build_profile_md()
    n_skills = skills_yaml.count("\n  - {")

    targets = [(CONFIG / "my_skills.yaml", skills_yaml),
               (CONFIG / "my_profile.md", profile_md)]

    print(f"my_skills.yaml   {n_skills} skills mapped onto the vocabulary")
    if unmatched:
        notable = sorted(set(unmatched) & WORTH_ADDING_TO_VOCAB)
        rest = sorted(set(unmatched) - WORTH_ADDING_TO_VOCAB)
        print(f"  {len(unmatched)} dropped — not in config/skills_vocab.yaml.")
        if notable:
            print("  Worth adding to the vocabulary, a posting may name these:")
            print("   ", ", ".join(notable))
        if rest:
            print(f"  Correctly dropped ({len(rest)}), too specific or not a job-posting skill:")
            print("   ", ", ".join(rest))
    print(f"my_profile.md    {len(profile_md.splitlines())} lines, "
          f"{len(profile_md.split())} words")

    if not args.apply:
        print("\nReview only. Re-run with --apply to write.")
        return 0
    for path, body in targets:
        existed = path.exists()
        path.write_text(body, encoding="utf-8")
        print(f"{'overwrote' if existed else 'wrote'}  {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
