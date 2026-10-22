#!/usr/bin/env python3
"""Check your profile before RocketApply uses it.

    python scripts/validate_profile.py            # report
    python scripts/validate_profile.py --strict   # TODO_ME markers become errors
    python scripts/validate_profile.py path/to/profile

The CV is a one-page frame with no slack: one character too many wraps a bullet
onto a new line and pushes the page to two. This tells you before an employer does.
The checks live in `src/pitwall/apply/validate.py` (the same code the app runs).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from pitwall.apply import resolve_profile_dir  # noqa: E402
from pitwall.apply.validate import format_report, validate  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
strict = "--strict" in sys.argv
directory = pathlib.Path(args[0]) if args else resolve_profile_dir()
print(f"profile: {directory}")
report = validate(directory)
print(format_report(report, strict=strict))
sys.exit(1 if report.failed(strict=strict) else 0)
