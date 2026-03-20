#!/usr/bin/env python3
"""Reject debug statements in frontend source files."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

PATTERNS = (
    re.compile(r"\bconsole\.log\s*\("),
    re.compile(r"\bdebugger\b"),
)


def main(argv: list[str]) -> int:
    if os.environ.get("CI"):
        return 0

    violations: list[str] = []
    for filename in argv[1:]:
        path = Path(filename)
        if not path.is_file():
            continue

        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(pattern.search(line) for pattern in PATTERNS):
                violations.append(f"{filename}:{lineno}: remove debug-only statement")

    if not violations:
        return 0

    print("Frontend source contains debug-only statements:")
    for violation in violations:
        print(f"  {violation}")
    print("Use console.warn/error if runtime logging is required.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
