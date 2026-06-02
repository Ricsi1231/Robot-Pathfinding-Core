# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project scaffold: `src/` layout package `robot_pathfinding`, packaging
  via `pyproject.toml` (hatchling), strict mypy, ruff lint/format, pytest, a
  Makefile, pre-commit hooks, and GitHub Actions CI.
- Staging publish pipeline: merging to the `staging` branch runs the full check
  matrix (reusable `tests.yml` workflow) and, on success, builds a uniquely
  versioned wheel + sdist (`<version>.dev<run>`) and attaches them to an
  automatically created GitHub pre-release.
- Core models `Point`, `Grid` (bounds, obstacles, 4-connected neighbour
  generation), and `PathResult`, plus the `BasePathfinder` abstract interface.
- `BfsPathfinder`: breadth-first search that returns a fewest-moves path under
  uniform movement cost, with full endpoint validation.
- `Grid` is a dynamic occupancy grid: `update(occupied=..., free=...)`, `resize`,
  and `ensure_contains` let it grow and flip cells as sensor data arrives without
  knowing the map size in advance.

### Changed

- Grid movement is now 8-connected (cardinals + diagonals) with corner-cutting
  disallowed; pass `allow_diagonal=False` for 4-connectivity. BFS consequently
  returns the path with the fewest moves (Chebyshev), not the shortest Euclidean
  distance.

[Unreleased]: https://github.com/Richard/Robot-Pathfinding-Core/commits/main
