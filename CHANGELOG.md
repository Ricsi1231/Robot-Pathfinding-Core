# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Per-cell **cost channel** on `Grid` (a gradient costmap layer): `Grid.cost(point)`,
  `set_cost(point, value)`, a `costs=` constructor argument, and `update(costs=...)`. A\* and
  Dijkstra add the destination cell's cost to their step cost, so paths prefer clearance while
  remaining able to traverse costly cells when cheaper; BFS and DFS ignore it. Costs must be finite
  and non-negative.
- Support for **empty (0-size) grids**: `Grid(0, 0)` (or any zero dimension) is now valid — searches
  return a not-found result and the grid can grow from sensor data via `update()` /
  `ensure_contains()`. New `Grid.is_empty` property for a clean guard.
- `VERSION.txt` (semver mirror + `build` counter) and automated versioning: a `dev` CI job bumps the
  semver via commitizen and ticks the build counter on each push; a `production` branch deploy job
  serves the same semver with `build + 200`.
- `scripts/gitlab.sh` — a helper that wraps the GitLab REST API (create issue, open MR, move a
  status label, comment, close) for the issue → branch → MR → review workflow (development tooling).
- **GitHub Actions pipeline** (`.github/workflows/`) running alongside GitLab CI: `tests.yml` (the
  reusable ruff / mypy / pytest gate across Python 3.11–3.14) and `ci.yml` (that gate on every pull
  request and on pushes to every branch except `staging`). Version bumping is deliberately not
  ported — GitLab remains the sole writer of versions and tags.
- **Public GitHub Releases** — `release.yml` turns a push to `staging` into a public,
  non-prerelease GitHub Release tagged `vX.Y.Z` with the wheel and sdist attached. It resolves the
  version by importing the package, reuses an already-mirrored tag when one exists, and skips with
  a green run when that version is already released, so re-pushing `staging` is a no-op. An inert
  OIDC trusted-publishing job is gated behind the `ENABLE_PYPI_PUBLISH` repository variable.
- `scripts/changelog_section.py` — extracts a single `## [X.Y.Z]` section from this file to use as
  the GitHub Release body, with GitHub's auto-generated notes as the fallback.

### Changed
- `scripts/gitlab.sh` is now a compatibility shim over **`scripts/vcs.sh`**, a provider-agnostic
  rewrite that drives both GitLab and GitHub from the same five subcommands. The provider is
  detected from `--provider`, `$VCS_PROVIDER`, `--remote`, or `origin`'s host. Existing
  `bash scripts/gitlab.sh …` invocations and the `<kind> #<number>  <url>` output contract are
  unchanged. Adds `--dry-run`, `--key=value` arguments, and rejection of a missing flag value that
  previously swallowed the next flag.
- A\* and Dijkstra now weight moves (cardinal `1.0`, diagonal `√2`) and A\* uses an octile heuristic
  when diagonals are allowed (Manhattan otherwise); with `allow_diagonal=True` they return true
  shortest diagonal paths instead of 4-connected Manhattan staircases.
- `Grid` dimension validation now rejects only *negative* sizes (`0` is valid); the error message is
  reworded to "grid width and height must be non-negative".
- CI: the test matrix now runs only on the `dev` branch (previously on every branch push and merge
  request).
- `[project.urls]` and the README badges now point at the public GitHub repository, which is what
  PyPI and GitHub render; the previous targets were a private GitLab project and two repository
  paths that do not exist.
- Documentation: `consuming.md` now leads with the public GitHub Release install path (wheel asset
  URL, `gh release download`, tagged `git+` revision) and keeps the GitLab registry as the internal
  channel; `building.md`'s CI/CD section describes the workflows that actually exist.
- Development workflow: adopted a four-branch promotion model (`dev → staging → master →
  production`) and expanded the contributor guidelines; documentation synced to match.
- Code style: removed non-docstring comments across the codebase and adopted a docstrings-only
  policy (docstrings on modules, classes, and functions are the only permitted in-code docs).

### Removed
- `.github/workflows/publish.yml` — it stamped a `.dev<run_number>` suffix into `__version__` and
  published a *pre-release* on every `staging` push. Superseded by `release.yml`, which publishes
  the real semver as a public release.

### Fixed
- A\*, Dijkstra, and DFS ignored `Grid.allow_diagonal` — they were hardcoded to 4-connected cardinal
  movement and always produced Manhattan paths. They now honour the grid's diagonal setting via
  `Grid.neighbors` (including the no-corner-cutting rule).
- `scripts/gitlab.sh comment` printed `note on issue #?` with an empty URL; the GitLab note
  response carries neither `iid` nor `web_url`, so both parses missed. It now reports the issue
  number and URL.
- `make check` broke on a pristine tree once ruff began formatting Python blocks inside markdown:
  the public-API listings in `docs/reference/architecture.md` and `specification.md` are name lists,
  not code, and were reformatted into tuples. They are now fenced as `text`, and ruff is capped
  (`ruff>=0.6,<0.17`) so a future release cannot silently break the gate the same way.

## [1.0.0] - 2026-06-27

### Added
- BFS, DFS, Dijkstra, and A\* pathfinders over a `Grid` of `Point`s.
- `Grid`, `Point`, and `PathResult` models.
- GitLab CI pipeline (`.gitlab-ci.yml`): test matrix on Python 3.11–3.14, a
  `staging`-branch pre-release publish, and a tag-triggered (`vX.Y.Z`) release
  that publishes to the Package Registry and creates a GitLab Release.

### Changed
- Migrated the project from GitHub to GitLab; CI moved from GitHub Actions to GitLab CI.
