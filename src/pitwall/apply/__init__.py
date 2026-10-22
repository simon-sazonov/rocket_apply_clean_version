"""Tailored CV and cover-letter generation.

Ninety per cent deterministic, ten per cent model. The model decides what is
*relevant*; this package guarantees what is *true*.

The CV is a frozen frame with exactly three variable slots — which three projects
appear, which skills fill each row, and which pre-approved phrasing an experience
bullet uses. Everything else on the page is a constant, and the model has no field
in its output schema with which to change it.

    from pitwall.apply.loader import load_profile
    from pitwall.apply.layout import Frame

    profile = load_profile()
    frame = Frame.load(profile)
"""

from __future__ import annotations

__all__ = ["PROFILE_DIR", "EXAMPLE_PROFILE_DIR", "project_root", "resolve_profile_dir"]

import os
import pathlib


def project_root() -> pathlib.Path:
    """The repository root — src/pitwall/apply/__init__.py is three levels down."""
    return pathlib.Path(__file__).resolve().parents[3]


#: The made-up example profile that ships with the repository.
EXAMPLE_PROFILE_DIR = project_root() / "profile.example"


def resolve_profile_dir() -> pathlib.Path:
    """Where your profile lives.

    `ROCKETAPPLY_PROFILE_DIR` (environment or `.env`) wins; otherwise `profile/`
    (your own, gitignored); otherwise the made-up `profile.example/`, so a fresh
    clone runs before you have written anything. `make setup` copies the example
    into `profile/`.
    """
    env = os.getenv("ROCKETAPPLY_PROFILE_DIR")
    if not env:
        dotenv = project_root() / ".env"
        if dotenv.is_file():
            from dotenv import dotenv_values

            env = dotenv_values(dotenv).get("ROCKETAPPLY_PROFILE_DIR") or None
    if env:
        return pathlib.Path(env).expanduser().resolve()
    own = project_root() / "profile"
    return own if own.is_dir() else EXAMPLE_PROFILE_DIR


#: The single source of truth for every fact on your CV and in your letters.
#: Hand-written by you, never written by a model: no fact may live in a prompt,
#: a template or in Python source.
PROFILE_DIR = resolve_profile_dir()
