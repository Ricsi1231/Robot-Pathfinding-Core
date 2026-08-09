"""Extract a single release section from a Keep a Changelog file.

Usage::

    python3 scripts/changelog_section.py 1.0.0 [CHANGELOG.md]

Writes the body of the ``## [<version>]`` section to stdout and exits ``0``.
Exits ``1`` with a message on stderr and no stdout when the section is absent
or empty, which lets the release pipeline fall back to auto-generated notes.

A leading ``v`` on the requested version is ignored, the section ends at the
next ``##`` heading or at the trailing link-reference block, surrounding blank
lines are stripped, and ``## [Unreleased]`` is never matched.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DEFAULT_CHANGELOG = Path("CHANGELOG.md")
HEADING = re.compile(r"^##\s+")
VERSION_HEADING = re.compile(r"^##\s+\[(?P<version>[^\]]+)\]")
LINK_DEFINITION = re.compile(r"^\[[^\]]+\]:\s")
UNRELEASED = "unreleased"
USAGE = "usage: changelog_section.py VERSION [CHANGELOG]"


def normalize(version: str) -> str | None:
    """Return a comparable version string, or ``None`` if it is not a release."""
    cleaned = version.strip().lstrip("vV")
    if not cleaned or cleaned.lower() == UNRELEASED:
        return None
    return cleaned


def extract_section(text: str, version: str) -> str | None:
    """Return the changelog body for ``version``, or ``None`` when there is none."""
    wanted = normalize(version)
    if wanted is None:
        return None

    body: list[str] = []
    found = False

    for line in text.splitlines():
        if HEADING.match(line):
            if found:
                break
            heading = VERSION_HEADING.match(line)
            found = heading is not None and normalize(heading["version"]) == wanted
            continue
        if found:
            if LINK_DEFINITION.match(line):
                break
            body.append(line)

    if not found:
        return None
    return "\n".join(body).strip("\n") or None


def main(argv: list[str]) -> int:
    """Print the requested changelog section and return a process exit code."""
    if not 1 <= len(argv) <= 2:
        print(USAGE, file=sys.stderr)
        return 2

    path = Path(argv[1]) if len(argv) == 2 else DEFAULT_CHANGELOG
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"cannot read {path}: {error}", file=sys.stderr)
        return 1

    section = extract_section(text, argv[0])
    if section is None:
        print(f"no changelog section for {argv[0]} in {path}", file=sys.stderr)
        return 1

    print(section)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
