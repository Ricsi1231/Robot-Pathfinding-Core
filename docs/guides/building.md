# Building & running `robot-pathfinding-core`

How to install the library from a clone of this repository, run it, and use the development
workflow. To consume a **released** version in another project instead, see
[consuming.md](consuming.md).

## Requirements

- Python 3.11–3.14

The library has **zero runtime dependencies** — runtime code uses only the Python standard
library. Development tooling (ruff, mypy, pytest, …) lives in the `dev` optional-dependencies
group.

## Installation

```bash
# from a clone of this repository
python3 -m pip install -e ".[dev]"
```

This installs the package in editable mode together with the development tools. The install
name is `robot-pathfinding-core`; the import name is `robot_pathfinding`.

## Running it

Once installed, import the package and run a search:

```python
from robot_pathfinding import AStarPathfinder, Grid, Point

# A 10×10 grid with a short wall of obstacles.
grid = Grid(width=10, height=10, obstacles=[Point(3, 3), Point(3, 4), Point(3, 5)])

result = AStarPathfinder().find_path(grid, start=Point(0, 0), goal=Point(9, 9))

if result.found:
    print(f"path of {result.path_length} steps, visited {result.visited_nodes} nodes")
    print(f"search took {result.execution_time_ms:.3f} ms")
    for point in result.path:
        print(point)
else:
    print("no path found")
```

Any of `BfsPathfinder`, `DfsPathfinder`, `DijkstraPathfinder`, or `AStarPathfinder` can be
swapped in — they all share the same `find_path(grid, start, goal) -> PathResult` interface.

The `Grid` is dynamic and does more than binary obstacles: pass `allow_diagonal=False` for
4-connectivity, start from an empty grid (`Grid(0, 0)`) and grow it from sensor data via
`update()` / `ensure_contains()`, and bias the weighted planners (A\* / Dijkstra) with a per-cell
cost via `grid.set_cost(Point(x, y), value)` — e.g. `grid.set_cost(Point(2, 4), 5.0)` to steer
paths away from a cell. See [architecture.md](../reference/architecture.md) for how the pieces fit
together.

## Development

Common tasks are exposed through the `Makefile` (CI runs the same tools):

```bash
make install       # editable install + pre-commit hooks
make lint          # ruff check
make format        # ruff format
make typecheck     # mypy (strict)
make test          # pytest
make check         # lint + format-check + typecheck + test (CI parity)
make build         # build wheel + sdist
```

Run `make check` before committing — it mirrors the CI gate.

### Code style

Match the surrounding code. Do **not** add inline or block comments — the only permitted in-code
documentation is **docstrings** on modules, classes, and functions (functional directives such as
`# noqa` / `# type: ignore` are kept where required). Commits follow Conventional Commits
(`type(scope): message`, enforced by commitizen).

### Issue tracker automation

`scripts/vcs.sh` wraps the common REST calls for **both GitLab and GitHub** — create an issue, open
a merge request / pull request into `dev`, move a status label, add a comment, or close an issue —
so the issue → branch → MR → review workflow can be driven from the CLI. Run
`bash scripts/vcs.sh --help` for usage. `scripts/gitlab.sh` still works and is a thin shim that
pins the provider to GitLab.

The provider is chosen by the first of these that resolves: `--provider`, `$VCS_PROVIDER`,
`--remote NAME`, `origin`'s host, then a single unambiguous remote. Because `origin` wins, adding
the GitHub mirror as a second remote does not change the default behaviour.

Pass `--dry-run` to print the requests that would be made without calling either API. The full
process is in [development-guidelines.md](../reference/development-guidelines.md).

## CI/CD

The project runs **two pipelines** over the same commits. GitLab is the primary host; GitHub is a
push mirror that verifies every change independently.

### GitLab CI (`.gitlab-ci.yml`)

- **`test`** — runs ruff lint, ruff format-check, mypy, and pytest across Python 3.11–3.14.
  It runs **only on the `dev` branch** (i.e. once changes are merged into `dev`); feature-branch
  pushes and merge requests do not trigger it.
- **`bump`** — see [Versioning flow](#versioning-flow). GitLab is the **only** host that writes
  versions and tags.
- **`publish` / `release`** — on push to the `staging` branch, builds a wheel + sdist, uploads
  it to the GitLab **PyPI Package Registry**, and creates a tagged GitLab **Release**.

### GitHub Actions (`.github/workflows/`)

- **`ci.yml`** — the same four checks across Python 3.11–3.14, but on the native GitHub triggers:
  every **pull request** plus pushes to `dev`, `staging`, `master`, `main`, and `production`. This
  is broader than the GitLab `test` job, which only covers `dev`.
- **`release.yml`** — on push to `staging` or a `v*` tag, builds the wheel + sdist and attaches
  them to a **GitHub Release**. It resolves the version from
  `src/robot_pathfinding/__init__.py` with the same regex the GitLab `publish` job uses, so the two
  hosts always agree on the version.
- **`production.yml`** — port of `deploy-production`; emits the same `version.json`.

The package is **not** published to public PyPI. `release.yml` contains a `pypi-publish` job that
uses OIDC trusted publishing, but it is inert unless the repository variable
`ENABLE_PYPI_PUBLISH` is set to `true`. Enabling it also requires registering the project on PyPI
and configuring a trusted publisher for this repository and workflow filename.

There is deliberately **no `bump` job on GitHub**. Both hosts running `cz bump` would race for the
same tags; GitLab owns version state and the mirror carries the result to GitHub.

### The GitHub mirror

GitHub receives commits through GitLab's built-in **push mirror** (GitLab → *Settings → Repository
→ Mirroring repositories*), which propagates all branches and tags. The mirror is **one-way**:
anything committed directly on GitHub is overwritten by the next GitLab push, so never push to
GitHub or merge a pull request there.

### Versioning flow

`VERSION.txt` (repo root) holds `version=X.Y.Z` and `build=N`. The semver mirrors
`src/robot_pathfinding/__init__.py` (commitizen keeps both in sync via
`[tool.commitizen].version_files`); `build` is a counter. Promotion order is
`dev → staging → master → production`:

GitLab is the **sole writer** of versions and tags. GitHub Actions never pushes commits or tags; it
consumes whatever the mirror delivers.

- **dev** — development + tests. On each push, the `bump` CI job increments `build` and runs
  `cz bump` (semver derived from the Conventional Commits), commits with `[skip ci]` (no pipeline
  loop), tags `vX.Y.Z`, and pushes back. Needs the `BUMP_TOKEN` masked CI/CD variable (project
  access token with `write_repository`). Only `feat` / `fix` / breaking commits move the semver.
- **staging** — publishes the version, creates the GitLab Release, and is the **internal**
  testing stage (release available to the group's developers).
- **master** — promotes the staging release to **open testing / beta**, making it available to
  testers. (No dedicated CI job yet; it is a promotion target.)
- **production** — the `deploy-production` job serves the **same semver** with
  **build = dev build + 200** (emitted in `version.json`), making the release publicly available.

> The repository's physical default branch is still `main`; renaming it to `master` to match the
> model above is a pending git op.
