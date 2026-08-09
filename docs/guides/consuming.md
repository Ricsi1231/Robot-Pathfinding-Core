# Consuming `robot-pathfinding-core` in another project

`robot-pathfinding-core` is published to the **GitLab PyPI Package Registry** on every `staging`
release (see [`.gitlab-ci.yml`](../../.gitlab-ci.yml)). This guide shows how another Python project — in
the same `robot-pathfinding-ros2-platfrom` group — installs a released version as a normal `pip`
dependency.

- **Install (distribution) name:** `robot-pathfinding-core`
- **Import name:** `robot_pathfinding`
- Always **pin the exact released version** (e.g. `==1.0.0`). To publish a new one, bump the version on
  `dev`, then merge to `staging`.

GitLab's PyPI registry requires authentication to download — even for public projects — so you need a
read-scoped token and the group index URL.

> The package is **not** on public PyPI. Besides the GitLab registry, the same wheel and sdist are
> attached as assets to each **GitHub Release** on the mirror
> (`.github/workflows/release.yml`), which is an alternative if you already have GitHub access —
> `pip install <url-to-the-wheel-asset>`. The GitLab registry remains the canonical source.

## 1. One-time setup

### Find the group ID
Open the group `robot-pathfinding-ros2-platfrom`. The numeric **Group ID** is shown under the group
name (and in **Group → Settings → General**). Used as `<GROUP_ID>` below.

### Create a group Deploy Token
**Group → Settings → Repository → Deploy tokens** → create a token with **only** the
`read_package_registry` scope. GitLab shows the **username** (`<TOKEN_USER>`) and **token** (`<TOKEN>`)
once — save them somewhere safe.

> **Never commit the token.** Put it in a local `pip.conf`, an environment variable, or a masked CI/CD
> variable — never in a file tracked by git.

### The group PyPI index URL
```
https://gitlab.com/api/v4/groups/<GROUP_ID>/-/packages/pypi/simple
```

## 2. Install recipes

### A. Local development — `pip.conf`
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

### B. `requirements.txt` (inject the token from an env var — don't hard-code it)
```
--extra-index-url https://<TOKEN_USER>:${RPC_TOKEN}@gitlab.com/api/v4/groups/<GROUP_ID>/-/packages/pypi/simple
robot-pathfinding-core==1.0.0
```
```bash
RPC_TOKEN=<TOKEN> pip install -r requirements.txt
```

### C. Consumer project's GitLab CI
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

### poetry / uv
Configure the same URL as a named source instead of `--extra-index-url`:
- **poetry:** `poetry source add --priority=supplemental gitlab "https://gitlab.com/api/v4/groups/<GROUP_ID>/-/packages/pypi/simple"` then add credentials via `poetry config`.
- **uv:** add an `[[tool.uv.index]]` entry with the URL and supply credentials via env vars.

## 3. Notes & rationale

- Use **`--extra-index-url`**, not `--index-url`, so dependencies from public PyPI still resolve.
- Because `--extra-index-url` makes pip consider both indexes, keep the dependency **pinned** to a
  version that exists only in the GitLab registry to avoid resolving an unexpected package.
- The **group** endpoint aggregates packages from every project in the group, so one URL + token works
  for any current or future shared library — no per-project URL needed.

## 4. Verify it works

```bash
python3 -m venv /tmp/consume-test && . /tmp/consume-test/bin/activate
pip install "robot-pathfinding-core==1.0.0" \
  --extra-index-url "https://<TOKEN_USER>:<TOKEN>@gitlab.com/api/v4/groups/<GROUP_ID>/-/packages/pypi/simple"
python -c "from robot_pathfinding import AStarPathfinder, Grid, Point; \
  g=Grid(5,5); r=AStarPathfinder().find_path(g, Point(0,0), Point(4,4)); print('found:', r.found, 'len:', r.path_length)"
```
Expected: the install succeeds and the snippet prints `found: True ...`.

## 5. Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| `401 Unauthorized` | Token wrong/expired, or missing the `read_package_registry` scope. |
| `404` / package not found | Wrong `<GROUP_ID>`, or that version hasn't been published yet (check **Deploy → Package Registry**). |
| pip installs a different/unexpected package | Used `--index-url` instead of `--extra-index-url`, or the pinned version doesn't exist in the registry. |
| Works locally, fails in CI | CI/CD variables not set/masked, or (for `CI_JOB_TOKEN`) the consumer project isn't in the Token Access allowlist. |
