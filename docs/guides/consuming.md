# Consuming `robot-pathfinding-core` in another project

Every promotion to `staging` publishes the same wheel and sdist through more than one channel. This
guide covers all of them.

- **Install (distribution) name:** `robot-pathfinding-core`
- **Import name:** `robot_pathfinding`
- Always **pin the exact released version** (e.g. `==1.0.0`). To publish a new one, bump the version on
  `dev`, move the changelog's `[Unreleased]` section under that version, then merge to `staging`.

| Channel | Public? | Authentication | Use it when |
|---------|---------|----------------|-------------|
| [GitHub Release](#0-github-release-public) | Yes | None | Default for anyone outside the group |
| [PyPI](#1-pypi) | Yes | None | Once `ENABLE_PYPI_PUBLISH` is switched on |
| [GitLab Package Registry](#2-gitlab-package-registry-internal) | No | Read-scoped token | Projects inside the `robot-pathfinding-ros2-platfrom` group |

## 0. GitHub Release (public)

`.github/workflows/release.yml` attaches `robot_pathfinding_core-<version>-py3-none-any.whl` and
`robot_pathfinding_core-<version>.tar.gz` to a public
[GitHub Release](https://github.com/Ricsi1231/Robot-Pathfinding-Core/releases) tagged `vX.Y.Z`. No
token, no index configuration.

```bash
pip install https://github.com/Ricsi1231/Robot-Pathfinding-Core/releases/download/v1.0.0/robot_pathfinding_core-1.0.0-py3-none-any.whl
```

In a `requirements.txt`, use the PEP 508 direct-reference form so the pin stays readable:

```
robot-pathfinding-core @ https://github.com/Ricsi1231/Robot-Pathfinding-Core/releases/download/v1.0.0/robot_pathfinding_core-1.0.0-py3-none-any.whl
```

To fetch the assets without pip — for vendoring or an air-gapped mirror:

```bash
gh release download v1.0.0 --repo Ricsi1231/Robot-Pathfinding-Core --pattern '*.whl'
```

Installing from a tagged source revision works too, and does not depend on the asset filename:

```bash
pip install "robot-pathfinding-core @ git+https://github.com/Ricsi1231/Robot-Pathfinding-Core@v1.0.0"
```

## 1. PyPI

The package is **not on public PyPI yet**. `release.yml` contains a `pypi` job that uses OIDC
trusted publishing, but it stays skipped unless the repository variable `ENABLE_PYPI_PUBLISH` is set
to `true` — which also requires registering the project on PyPI with a trusted publisher for this
repository, the `release.yml` workflow, and the `pypi` environment. Once that is done, the install
is the ordinary one:

```bash
pip install "robot-pathfinding-core==1.0.0"
```

## 2. GitLab Package Registry (internal)

For projects inside the `robot-pathfinding-ros2-platfrom` group. GitLab's PyPI registry requires
authentication to download — even for public projects — so you need a read-scoped token and the
group index URL.

### One-time setup

#### Find the group ID
Open the group `robot-pathfinding-ros2-platfrom`. The numeric **Group ID** is shown under the group
name (and in **Group → Settings → General**). Used as `<GROUP_ID>` below.

#### Create a group Deploy Token
**Group → Settings → Repository → Deploy tokens** → create a token with **only** the
`read_package_registry` scope. GitLab shows the **username** (`<TOKEN_USER>`) and **token** (`<TOKEN>`)
once — save them somewhere safe.

> **Never commit the token.** Put it in a local `pip.conf`, an environment variable, or a masked CI/CD
> variable — never in a file tracked by git.

#### The group PyPI index URL
```
https://gitlab.com/api/v4/groups/<GROUP_ID>/-/packages/pypi/simple
```

### Install recipes

#### A. Local development — `pip.conf`
Put your token in pip's user config (`~/.config/pip/pip.conf` on Linux/macOS), which lives outside any
repo:
```ini
[global]
extra-index-url = https://<TOKEN_USER>:<TOKEN>@gitlab.com/api/v4/groups/<GROUP_ID>/-/packages/pypi/simple
```
Then:
```bash
pip install "robot-pathfinding-core==1.0.0"
```

#### B. `requirements.txt` (inject the token from an env var — don't hard-code it)
```
--extra-index-url https://<TOKEN_USER>:${RPC_TOKEN}@gitlab.com/api/v4/groups/<GROUP_ID>/-/packages/pypi/simple
robot-pathfinding-core==1.0.0
```
```bash
RPC_TOKEN=<TOKEN> pip install -r requirements.txt
```

#### C. Consumer project's GitLab CI
Store `RPC_TOKEN_USER` and `RPC_TOKEN` as **masked** CI/CD variables in the consumer project
(Settings → CI/CD → Variables), then:
```yaml
before_script:
  - pip install --extra-index-url "https://${RPC_TOKEN_USER}:${RPC_TOKEN}@gitlab.com/api/v4/groups/<GROUP_ID>/-/packages/pypi/simple" "robot-pathfinding-core==1.0.0"
```

> **Alternative (same group, CI only):** use `gitlab-ci-token:${CI_JOB_TOKEN}` in place of the deploy
> token. This requires adding the consumer project to **this** project's
> *Settings → CI/CD → Token Access* allowlist. The deploy token avoids that, which is why it's the
> default here.

#### poetry / uv
Configure the same URL as a named source instead of `--extra-index-url`:
- **poetry:** `poetry source add --priority=supplemental gitlab "https://gitlab.com/api/v4/groups/<GROUP_ID>/-/packages/pypi/simple"` then add credentials via `poetry config`.
- **uv:** add an `[[tool.uv.index]]` entry with the URL and supply credentials via env vars.

### Notes & rationale

- Use **`--extra-index-url`**, not `--index-url`, so dependencies from public PyPI still resolve.
- Because `--extra-index-url` makes pip consider both indexes, keep the dependency **pinned** to a
  version that exists only in the GitLab registry to avoid resolving an unexpected package.
- The **group** endpoint aggregates packages from every project in the group, so one URL + token works
  for any current or future shared library — no per-project URL needed.

## 3. Verify it works

From the public GitHub Release:

```bash
python3 -m venv /tmp/consume-test && . /tmp/consume-test/bin/activate
pip install https://github.com/Ricsi1231/Robot-Pathfinding-Core/releases/download/v1.0.0/robot_pathfinding_core-1.0.0-py3-none-any.whl
python -c "from robot_pathfinding import AStarPathfinder, Grid, Point; \
  g=Grid(5,5); r=AStarPathfinder().find_path(g, Point(0,0), Point(4,4)); print('found:', r.found, 'len:', r.path_length)"
```

From the GitLab registry, swap the install line for:

```bash
pip install "robot-pathfinding-core==1.0.0" \
  --extra-index-url "https://<TOKEN_USER>:<TOKEN>@gitlab.com/api/v4/groups/<GROUP_ID>/-/packages/pypi/simple"
```

Expected either way: the install succeeds and the snippet prints `found: True ...`.

## 4. Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| `404` on a release asset URL | That version has no release yet, or the filename is wrong — check [Releases](https://github.com/Ricsi1231/Robot-Pathfinding-Core/releases). The wheel is `robot_pathfinding_core-<version>-py3-none-any.whl` (underscores), not the hyphenated distribution name. |
| `robot-pathfinding-core` not found on PyPI | `ENABLE_PYPI_PUBLISH` has not been enabled yet — use the GitHub Release instead. |
| No new release after merging to `staging` | `__version__` was not bumped, so the run skipped an already-published version. Bump on `dev` and merge again. |
| `401 Unauthorized` | GitLab token wrong/expired, or missing the `read_package_registry` scope. |
| `404` / package not found in the registry | Wrong `<GROUP_ID>`, or that version hasn't been published yet (check **Deploy → Package Registry**). |
| pip installs a different/unexpected package | Used `--index-url` instead of `--extra-index-url`, or the pinned version doesn't exist in the registry. |
| Works locally, fails in CI | CI/CD variables not set/masked, or (for `CI_JOB_TOKEN`) the consumer project isn't in the Token Access allowlist. |
