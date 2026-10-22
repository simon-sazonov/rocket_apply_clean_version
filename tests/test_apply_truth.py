"""The truth layer — what may be said, and what may not.

Half of these are generic rules. The other half are profile-specific, run
against the made-up example profile in `profile.example/`: work authorisation is
a topic block rather than a phrasing rule, specific attributions belong to
teammates, and one technique may not be claimed in one particular project.
"""

from __future__ import annotations

import pytest

from pitwall.apply.loader import load_profile
from pitwall.apply.truth import build_truth, derive_block_terms


@pytest.fixture(scope="module")
def profile():
    return load_profile()


@pytest.fixture(scope="module")
def truth(profile):
    return build_truth(profile)


def codes(violations) -> set[str]:
    return {v.code for v in violations}


# ── the run-specific clause: the gap the model just noticed ──

def test_missing_requirements_become_forbidden(profile):
    """The most dangerous hallucination is the one that closes the gap the
    matcher just found.

    SAP HANA rather than Snowflake, because Snowflake is already blocked — it is
    on the gap map at `confidence: none`. Only a term the profile has never heard
    of isolates the run-specific clause.
    """
    clean = build_truth(profile)
    assert not clean.check("The stack is built on SAP HANA.")

    gated = build_truth(profile, missing_requirements=["SAP HANA"])
    hits = gated.check("I have used SAP HANA in production.")
    assert "FORBIDDEN_CLAIM" in codes(hits)
    assert "the posting asks for it" in hits[0].detail


def test_zero_confidence_skills_are_always_forbidden(profile, truth):
    none_skills = [s.name for s in profile.skills if s.confidence == "none"]
    assert none_skills, "the gap map has emptied — check skills.yaml"
    for name in none_skills[:6]:
        assert "FORBIDDEN_CLAIM" in codes(truth.check(f"I have hands-on {name} experience."))


# ── the user's rules ──

@pytest.mark.parametrize("sentence", [
    "I am authorised to work in Portugal.",
    "I hold a valid work permit for the EU.",
    "I would not require sponsorship for this role.",
    "My residence permit is current.",
    "I am an EU citizen.",
    "I have the right to work in the United Kingdom.",
])
def test_work_authorisation_is_blocked_however_it_is_phrased(truth, sentence):
    """A topic block, not a phrase block — and it holds even when the posting
    raises the subject first. The user answers that one themselves."""
    assert "FORBIDDEN_TOPIC" in codes(truth.check(sentence)), sentence


def test_teammates_work_is_blocked(truth):
    assert "NOT_MY_WORK" in codes(truth.check("I built the Grafana dashboard for the pipeline."))
    assert "NOT_MY_WORK" in codes(truth.check("I wrote the warehouse API."))


def test_own_work_on_the_same_projects_is_not_blocked(truth):
    """The distinction that matters: the user really did build the ingestion and
    the data-quality checks on the same project, so only the phrase naming the
    part that is not theirs may be blocked."""
    assert not truth.check(
        "Co-built a PySpark ETL over a year of public taxi trips into partitioned Parquet."
    )
    assert not truth.check(
        "Designed a star schema over five years of lending records and wrote the load scripts."
    )


@pytest.mark.parametrize("sentence", [
    "I applied reinforcement learning in the Northwind internship.",
    "The demand model used a learned policy.",
    "I used RL in the churn model.",
])
def test_reinforcement_learning_in_the_wrong_project_is_blocked(truth, sentence):
    """A pairing rule: RL is real elsewhere in the profile, but claiming it for
    a project where it did not happen invites "walk me through the reward
    function", and there is no answer."""
    assert "FORBIDDEN_PAIRING" in codes(truth.check(sentence)), sentence


def test_reinforcement_learning_elsewhere_is_not_blocked(truth):
    """The other half, and the reason this is a pairing rule rather than a phrase
    block: the routing project is real RL evidence. Blocking the term outright
    would delete it."""
    assert truth.check(
        "Built a Gymnasium environment for warehouse routing and compared Q-learning with PPO."
    ) == []
    assert truth.check("Shaped the reward to cut collisions in the routing project.") == []


def test_cooccurrence_derivation_splits_technique_from_context(truth):
    by_claim = {claim: (t, c) for t, c, claim in truth.cooccurrence_blocks}
    techniques, contexts = by_claim[
        "reinforcement learning in the Northwind internship / demand forecasting work"
    ]
    assert techniques == ["reinforcement learning"]
    assert contexts == ["Northwind internship", "demand forecasting work"]


def test_evidence_private_skills_are_claimable_but_not_citable(profile, truth):
    """Real work, in a repository that is not published. The skill may be
    claimed; naming a project for it would be an invention."""
    assert truth.no_project_citation == {"TypeScript"}
    for name in truth.no_project_citation:
        assert name in truth.allowed_skills_letter


def test_block_term_derivation_drops_terms_that_describe_own_work():
    own = "i built the ema regime confirmation on breakout strategy v2"
    derived = derive_block_terms("the EMA regime filter in Breakout Strategy V2", own)
    assert "EMA" not in derived
    assert "Breakout Strategy" not in derived


# ── generic gates ──

def test_derived_numbers_are_rejected(truth):
    """15,832 -> 63 is in the profile. "over 99%" is a NEW number, and deriving
    one is where exaggeration creeps in."""
    assert "UNSUPPORTED_NUMBER" in codes(truth.check("I reduced query time by over 99%."))


def test_profile_numbers_are_accepted(truth):
    assert not truth.unsupported_numbers(
        "Built a churn model on 4,000 student accounts, reaching 0.81 ROC-AUC"
    )


@pytest.mark.parametrize("verb", ["led", "managed", "architected", "spearheaded"])
def test_seniority_verbs_are_gated(truth, verb):
    assert "UNSUPPORTED_SENIORITY_VERB" in codes(truth.check(f"I {verb} the data team."))


def test_preferred_verbs_pass(truth):
    for verb in ("built", "designed", "benchmarked", "validated", "measured"):
        assert not truth.check(f"I {verb} the evaluation harness.")


def test_supported_sentences_pass_every_gate(truth):
    for sentence in [
        "Built a gradient-boosted demand model on two years of store-level sales.",
        "Automated the monthly model-monitoring report in Python.",
        "Fine-tuned DistilBERT on 12,000 labelled reviews.",
    ]:
        assert truth.check(sentence) == [], sentence


def test_allowed_facts_cover_every_bullet_and_variant(profile, truth):
    ids = {f.id for f in truth.allowed_facts}
    for bullet in profile.experience_bullets:
        assert bullet.id in ids
        for variant in bullet.variants:
            assert variant.id in ids
    for project in profile.projects:
        for bullet in project.bullets:
            assert bullet.id in ids


# ─────────────────────── the adversarial corpus (§14.2) ───────────────────
#
# Hand-written sentences, half true and half subtly false. Run this on every
# prompt or gate change: an edit that drops recall here is a regression no
# matter how much nicer the prose got.
#
# The generic half is the same for everyone. The rest is specific to the
# example profile — decisions about what is and is not the user's own work,
# which no generic rule would ever recover.

BLOCKED = [
    # numbers that were never measured
    ("I reduced query time by over 99%.", "UNSUPPORTED_NUMBER"),
    ("The classifier reached 0.99 AUC on held-out data.", "UNSUPPORTED_NUMBER"),
    ("I trained on 4.2 million labelled examples.", "UNSUPPORTED_NUMBER"),
    # tools that are not in the profile
    ("I have production experience deploying models on AWS.", "FORBIDDEN_CLAIM"),
    ("I ran the training jobs on Kubernetes.", "FORBIDDEN_CLAIM"),
    ("I built the orchestration in Airflow.", "FORBIDDEN_CLAIM"),
    ("I modelled causal inference for the pricing team.", "FORBIDDEN_CLAIM"),
    # seniority, in every inflection
    ("I led a team of data scientists.", "UNSUPPORTED_SENIORITY_VERB"),
    ("I own the deployment pipeline end to end.", "UNSUPPORTED_SENIORITY_VERB"),
    ("I am managing two junior analysts.", "UNSUPPORTED_SENIORITY_VERB"),
    ("I architected the whole platform.", "UNSUPPORTED_SENIORITY_VERB"),
    ("I directed the migration to a new stack.", "UNSUPPORTED_SENIORITY_VERB"),
    # the topic that is off-limits however it is phrased
    ("I am authorised to work anywhere in the EU.", "FORBIDDEN_TOPIC"),
    ("No visa sponsorship would be required.", "FORBIDDEN_TOPIC"),
    ("I hold Portuguese residency.", "FORBIDDEN_TOPIC"),
    # work that belongs to teammates
    ("My Grafana dashboard caught the pipeline failures.", "NOT_MY_WORK"),
    ("I designed the monitoring dashboard for the taxi project.", "NOT_MY_WORK"),
    ("I wrote the warehouse API on top of the schema.", "NOT_MY_WORK"),
    # a technique claimed in the one place it did not happen
    ("I applied reinforcement learning in the demand forecasting work.", "FORBIDDEN_PAIRING"),
    ("The churn model learned a policy over time.", "FORBIDDEN_PAIRING"),
]

ALLOWED = [
    # every one of these is traceable to a bullet, a variant or a metric
    "Built a gradient-boosted demand model on two years of store-level sales.",
    "The model cut weekly forecast error 18% against the existing baseline.",
    "Built a churn model on 4,000 student accounts that reached 0.81 ROC-AUC.",
    "Fine-tuned DistilBERT on 12,000 labelled reviews to tag five complaint categories.",
    "Reached macro-F1 0.79 against 0.61 for a TF-IDF baseline.",
    "Simulated 10,000 experiments to check the false-positive rate stays at 5%.",
    "Compared Q-learning with PPO on a warehouse routing environment.",
    "I wrote the ingestion and data-quality stages of the taxi ETL.",
    # ordinary uses of gated-verb stems, which must not trip anything
    "I built my own evaluation harness before trusting the numbers.",
    "The finding is directly relevant to how the model is used.",
    "I was already ahead of the schedule I set myself.",
    # framing and opinion, which assert nothing checkable
    "Equal budgets are the only way to find out which algorithm is better.",
    "I want to work where the models are actually used for decisions.",
]


@pytest.mark.parametrize("sentence,code", BLOCKED)
def test_adversarial_sentences_are_caught(truth, sentence, code):
    assert code in codes(truth.check(sentence)), sentence


@pytest.mark.parametrize("sentence", ALLOWED)
def test_true_sentences_pass_every_gate(truth, sentence):
    assert truth.check(sentence) == [], sentence


# ── the attraction sentence ──────────────────────────────────────────────────


@pytest.fixture(scope="module")
def gapped(profile):
    """A truth layer with two real gaps, unverified so they survive as written.

    `verify=False` because `verify_gaps` drops a term the profile can prove and
    `looks_like_a_product` drops an activity phrase — neither of which is what
    this test is about.
    """
    return build_truth(
        profile, missing_requirements=["RL environments", "Real estate"], verify=False,
    )


def test_the_sentence_the_prompt_demands_does_not_block_the_letter(gapped):
    """The writer prompt REQUIRES a closing that says what draws them to the work,
    which cannot be written without naming the role's subject. This gate used to
    block the letter for naming it — two of three DO_NOT_SEND letters on
    28 Sep 2026 were exactly that, and both were shippable prose."""
    from pitwall.apply.truth import blocks_sending, severity

    letter = (
        "Dear Hiring Manager,\n\nI built a seven-stage pipeline.\n\n"
        "What excites me most about this role is the blend of research and "
        "engineering: designing new RL environments and reward signals.\n\n"
        "Alex Morgan"
    )
    hits = gapped.forbidden_hits(letter)
    assert [v.code for v in hits] == ["DOMAIN_IN_INTEREST"]
    assert severity(hits[0].code) == "style"
    assert blocks_sending(hits) == []
    # Still reported, and the note has to read as a judgement call rather than
    # as a verdict.
    assert "read the sentence and decide" in hits[0].detail


@pytest.mark.parametrize("letter,why", [
    (
        "Dear Hiring Manager,\n\nI have built RL environments for three years.\n\n"
        "Alex Morgan",
        "a plain claim, nowhere near the frame",
    ),
    (
        "Dear Hiring Manager,\n\nI built RL environments at work.\n\n"
        "What draws me to this role is designing new RL environments.\n\n"
        "Alex Morgan",
        "named once inside the frame and once outside it",
    ),
    (
        "Dear Hiring Manager,\n\nI have built RL environments and am drawn to "
        "more of it.\n\nAlex Morgan",
        "the frame worn as a coat, mid-sentence",
    ),
])
def test_a_claim_still_blocks_however_it_is_dressed(gapped, letter, why):
    from pitwall.apply.truth import blocks_sending

    hits = gapped.forbidden_hits(letter)
    assert [v.code for v in hits] == ["FORBIDDEN_CLAIM"], why
    assert blocks_sending(hits), why


def test_the_interest_sentence_is_never_operated_on():
    """Surgery here would strip the role's own subject out of the one sentence
    whose job is to name it."""
    from pitwall.apply.truth import NO_SURGERY

    assert "DOMAIN_IN_INTEREST" in NO_SURGERY


def test_a_short_acronym_is_matched_as_written():
    """The posting wanted an MS; the letter said "110 ms per Monte Carlo race".
    That sent a real letter to DO_NOT_SEND on 29 Sep 2026."""
    from pitwall.apply.loader import load_profile
    from pitwall.apply.truth import build_truth

    truth = build_truth(load_profile(), missing_requirements=["MS"])
    if "MS" not in truth.forbidden_claims:
        import pytest

        pytest.skip("the profile itself records an MS")
    assert truth.forbidden_hits("I reached 110 ms per Monte Carlo race.") == []
    assert truth.forbidden_hits("I hold an MS in data science.")
