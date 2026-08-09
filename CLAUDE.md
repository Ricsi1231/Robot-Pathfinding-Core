# CLAUDE.md

Working notes for Claude in this repository. Project documentation for humans lives in
`README.md` and under `docs/`; **this file is Claude-specific and is not part of that doc set —
do not link to it from the README or the docs.**

## Where the project docs are

Read these for detail rather than duplicating them here:

- Architecture, modules, and the `BasePathfinder` contract → `docs/reference/architecture.md`
- Build, install, run, dev workflow, CI/CD, versioning → `docs/guides/building.md`
- Consuming the published package elsewhere → `docs/guides/consuming.md`
- Team development guidelines (branching, tasks, daily push) → `docs/reference/development-guidelines.md`
- Formal specification → `docs/reference/specification.md`

## Project (orientation)

`robot-pathfinding-core` — a pure-Python, **stdlib-only / zero-runtime-dependency** library of
robot search / pathfinding algorithms (BFS, DFS, Dijkstra, A\*). Python 3.11–3.14, build backend
hatchling with src-layout. Source lives under `src/robot_pathfinding/` (`models/` + `algorithms/`);
`__version__` in `src/robot_pathfinding/__init__.py` is the single source of truth.

## Working rules

- **Never commit or push without the user's explicit permission.** Stage changes, show what would
  be committed, and wait for approval.
- **Never** add AI-generated attribution to commits or PRs (no `Co-Authored-By: Claude`, no
  "Generated with" notices). Write plain commit messages.
- **Commit message format** — Conventional Commits enforced by commitizen: `type(scope): message`
  (a **scope is required**). Types: `feat`, `fix`, `ci`, `docs`, `build`, `refactor`, `test`,
  `chore`. Create commits with `cz commit` (alias `cz c`); the `commit-msg` pre-commit hook
  validates them. Bump the release version with `cz bump` (updates `__init__.py`, tags `vX.Y.Z`).
- **No code comments** — do not add inline or block explanatory comments to code, tests, or
  config/CI files. The only permitted in-code documentation is **docstrings** on modules,
  classes, and functions. Preserve functional directives (`# noqa`, `# type: ignore`,
  `# pragma`) when they are actually required.
- **Run `make check` before committing** — ruff lint + format-check + mypy (strict) + pytest, the
  same gate CI runs.
- Keep the runtime **dependency-free**; dev-only tools go in the `dev` optional-dependencies group.
- Bump `__version__` in `src/robot_pathfinding/__init__.py` only — hatchling reads it.
- Branch roles / promotion order: `dev` (development + tests) → `staging` (publishes + GitLab
  Release, internal testing) → `master` (open testing / beta) → `production` (deploy, public).
  Full versioning flow is in `docs/guides/building.md`. (The repo's physical default branch is
  still `main`; renaming it to `master` is a pending git op.)
- Follow the team workflow in `docs/reference/development-guidelines.md`.

## Commands

```bash
make install     # editable install + pre-commit hooks
make lint        # ruff check .
make format      # ruff format .
make typecheck   # mypy (strict)
make test        # pytest
make check       # lint + format-check + typecheck + test  <-- run before committing
make build       # wheel + sdist
```

There is no `python` on this machine — use `python3` (3.14). `venv` symlinks fail on the project
mount; create virtualenvs outside the repo tree if needed.

## Issue tracker automation (GitLab primary, GitHub mirror)

The full team process lives in `docs/reference/development-guidelines.md`. This section is the
Claude-specific automation for driving it via the REST API. Prefer the `scripts/vcs.sh` wrapper —
drop to raw `curl` only for endpoints it doesn't cover.

- **Helper** — `scripts/vcs.sh` wraps the common writes for **both** hosts (tokens never printed;
  defaults to this repo's project id and `dev` as the MR target):
  ```bash
  bash scripts/vcs.sh issue   --title T --desc D --labels "Improvement,Status::IN PROGRESS"
  bash scripts/vcs.sh mr      --source <issue#>-slug --title "type: summary" --closes <issue#>
  bash scripts/vcs.sh label   --issue N --add "Status::CODE REVIEW" --remove "Status::IN PROGRESS"
  bash scripts/vcs.sh comment --issue N --body "text"
  bash scripts/vcs.sh close   --issue N
  ```
  `bash scripts/gitlab.sh …` still works — it is a shim that pins `--provider gitlab`. Both allow
  rules are useful: `bash scripts/vcs.sh:*` and `bash scripts/gitlab.sh:*`.
- **Output contract** — one line: `<kind> #<number>  <url>`. Kinds are `issue`, `MR` (GitLab) /
  `PR` (GitHub), `note on issue`, `closed issue`.
- **Provider detection** — `--provider` › `$VCS_PROVIDER` › `--remote NAME` › `origin`'s host › a
  single unambiguous remote. `origin` wins, so adding the GitHub mirror remote does not change the
  default. Two providers with no usable `origin` is a hard error.
- **`--dry-run`** prints the requests to stderr and exits without calling either API. Use it to
  check a GitHub mapping before the mirror exists.
- **Project** — this repo (`robot-pathfinding-core`) is numeric project ID **`83833586`**;
  API base `https://gitlab.com/api/v4`. (Note: `83835542` is the *separate* platform project
  `…/robot-pathfinding-ros2-platfrom` — do **not** use it for this repo's issues or MRs.)
  Feature branches are cut from `dev` and MRs target `dev`; issues appear on the group board.
- **Labels** (the real scoped set — not ad-hoc lowercase): type = `BUG` / `FEATURE` /
  `Improvement`; priority = `Priority::HIGH|MEDIUM|LOW`; stage =
  `Status::WAITING|IN PROGRESS|CODE REVIEW|QA|ALMOST DONE|INTERNAL|BETA`. The same names are used
  on GitHub and are created there on demand (`VCS_GH_CREATE_LABELS=0` disables that).
- **GitHub caveats** — `Closes #N` does not auto-close unless the PR targets the default branch
  (this model doesn't); a review is never requested from the PR author (GitHub 422s); GitHub has no
  scoped-label mutual exclusion, so always pass both `--add` and `--remove`; `remove_source_branch`
  is a repo-level setting and is dropped. `mr` and `label` make several calls — the first is fatal,
  follow-up failures are warnings so a retry can't create a duplicate PR.
- **Mirror direction** — GitLab → GitHub only, via GitLab's push mirror. Never push to GitHub,
  never merge a PR there, and never run version bumps from GitHub Actions.
- **Env overrides** — GitLab: `GITLAB_API`, `GITLAB_PROJECT_ID`, `GITLAB_ASSIGNEE`,
  `GITLAB_TARGET_BRANCH`. GitHub: `GITHUB_API`, `GITHUB_REPO`, `GITHUB_ASSIGNEE`,
  `GITHUB_TARGET_BRANCH`, `GH_TOKEN`/`GITHUB_TOKEN`. Both: `VCS_PROVIDER`, `VCS_TARGET_BRANCH`.

Workflow each time:

1. **Issue first** — create it (a type label + a `Priority::*` + `Status::IN PROGRESS`).
2. **Branch off `dev`**, named `<issue#>-slug`.
3. Do the work; never push to `dev` directly; run `make check` before committing.
4. Push the branch, open an MR into `dev` with `Closes #<issue#>` in the description.
5. Set the issue to `Status::CODE REVIEW`.

Underlying REST endpoints (for anything the wrapper doesn't cover): read the token with
```bash
TOKEN=$(grep -oiE 'https://[^:/@]+:[^@]+@gitlab\.com' ~/.git-credentials \
  | head -1 | sed -E 's#https://[^:]+:##; s#@gitlab\.com##')
```
then `POST …/projects/83833586/issues`, `POST …/projects/83833586/merge_requests`, and
`PUT …/projects/83833586/issues/<iid>` (labels/state). Always pass fields with
`--data-urlencode` (labels contain spaces and `::`). Parse a response without a JSON tool via
`grep -oE '"iid":[0-9]+|/merge_requests/[0-9]+|/(issues|work_items)/[0-9]+'`.
