#!/usr/bin/env python3
"""Validate commit messages against a conventional-commit subset."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ALLOWED_TYPES = ("feat", "fix", "docs", "style", "refactor", "test", "chore", "perf", "ci", "build", "revert")
TYPE_PATTERN = "|".join(ALLOWED_TYPES)
MESSAGE_PATTERN = re.compile(
    rf"^(?:fixup! |squash! )?(?:({TYPE_PATTERN})\([a-z0-9][a-z0-9._/-]*\): \S.*|Merge .+|Revert .+)$"
)


def load_subject(message_file: Path) -> str:
    for raw_line in message_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            return line
    return ""


def main(argv: list[str]) -> int:
    if os.environ.get("CI"):
        return 0

    if len(argv) == 2:
        message_file = Path(argv[1])
    else:
        message_file = Path(".git/COMMIT_EDITMSG")

    if not message_file.exists():
        print("commit-msg hook could not find the commit message file.", file=sys.stderr)
        return 1

    subject = load_subject(message_file)
    if MESSAGE_PATTERN.match(subject):
        return 0

    print("Commit message must match conventional commits: type(scope): description", file=sys.stderr)
    print(f"Allowed types: {', '.join(ALLOWED_TYPES)}", file=sys.stderr)
    print("Example: feat(auth): add phone-based login validation", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
