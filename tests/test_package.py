"""Smoke tests for the package skeleton.

These verify the package is importable and exposes basic metadata. Algorithm
tests will be added alongside their implementations.
"""

from __future__ import annotations

import robot_pathfinding


def test_package_is_importable() -> None:
    assert robot_pathfinding is not None


def test_version_is_non_empty_string() -> None:
    assert isinstance(robot_pathfinding.__version__, str)
    assert robot_pathfinding.__version__


def test_public_api_is_defined() -> None:
    assert isinstance(robot_pathfinding.__all__, list)
