"""Tests for the changelog section extractor used to build release notes."""

from __future__ import annotations

from pathlib import Path

import pytest

from changelog_section import extract_section, main, normalize

REPO_ROOT = Path(__file__).resolve().parents[1]

SAMPLE = """# Changelog

Preamble text that belongs to no release.

## [Unreleased]

### Added
- Something not yet released.

## [1.2.0] - 2026-05-01

### Added
- A shiny `feature` worth **10x** more.

### Fixed
- A bug.

## [1.1.0] - 2026-04-01

### Added
- The previous release.

[1.2.0]: https://example.invalid/compare/v1.1.0...v1.2.0
"""


def test_extracts_requested_section() -> None:
    section = extract_section(SAMPLE, "1.2.0")

    assert section is not None
    assert "A shiny `feature` worth **10x** more." in section


def test_stops_at_next_version_heading() -> None:
    section = extract_section(SAMPLE, "1.2.0")

    assert section is not None
    assert "The previous release." not in section


def test_keeps_subsection_headings() -> None:
    section = extract_section(SAMPLE, "1.2.0")

    assert section is not None
    assert "### Added" in section
    assert "### Fixed" in section


def test_unreleased_is_never_matched() -> None:
    assert extract_section(SAMPLE, "Unreleased") is None
    assert normalize("Unreleased") is None


def test_unreleased_body_is_not_leaked() -> None:
    section = extract_section(SAMPLE, "1.2.0")

    assert section is not None
    assert "Something not yet released." not in section


def test_strips_surrounding_blank_lines() -> None:
    section = extract_section(SAMPLE, "1.2.0")

    assert section is not None
    assert section == section.strip("\n")


def test_accepts_a_v_prefix() -> None:
    assert extract_section(SAMPLE, "v1.2.0") == extract_section(SAMPLE, "1.2.0")


def test_stops_at_the_link_reference_block() -> None:
    section = extract_section(SAMPLE, "1.1.0")

    assert section is not None
    assert "https://example.invalid" not in section


def test_missing_version_returns_none() -> None:
    assert extract_section(SAMPLE, "9.9.9") is None


def test_empty_section_returns_none() -> None:
    text = "## [1.0.0] - 2026-01-01\n\n## [0.9.0] - 2025-12-01\n\n- Older.\n"

    assert extract_section(text, "1.0.0") is None


def test_blank_version_returns_none() -> None:
    assert extract_section(SAMPLE, "  ") is None


def test_repository_changelog_documents_the_current_version() -> None:
    text = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert extract_section(text, "1.0.0")


def test_main_prints_the_section(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(SAMPLE, encoding="utf-8")

    exit_code = main(["1.2.0", str(changelog)])

    assert exit_code == 0
    assert "A shiny `feature` worth **10x** more." in capsys.readouterr().out


def test_main_reports_a_missing_section(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(SAMPLE, encoding="utf-8")

    exit_code = main(["9.9.9", str(changelog)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "no changelog section for 9.9.9" in captured.err


def test_main_reports_an_unreadable_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["1.2.0", str(tmp_path / "missing.md")])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "cannot read" in captured.err


def test_main_rejects_bad_usage(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "usage:" in captured.err
