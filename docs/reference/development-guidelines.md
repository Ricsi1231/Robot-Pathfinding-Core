# Development Guidelines

This development workflow applies to every software project in the group (hardware
designs are excluded).

## Branching

Every change in the codebase is done through feature branches; pushing changes directly
to the `dev` branch is forbidden.

Each feature branch must be linked to its GitLab issue — see
[Crosslinking issues](https://docs.gitlab.com/ee/user/project/issues/crosslinking_issues.html).
Name the branch `<issue-number>-short-description` (e.g. `4-remove-inline-comments`).

When the issue is ready, open a merge request (MR) into the **dev** branch and change the
issue label to **Status::CODE REVIEW**.

Branches:

- **dev** — Development branch used for aggregating feature branches and running tests.
  Tests are triggered on each merge into the branch.
- **staging** — Staging branch used for releasing the current version for internal
  development usage. The release is built only on `staging`; the build is triggered on
  merging `dev` into `staging`.
- **master** — Master branch used for promoting the staging release to open testing,
  making it available to testers.
- **production** — Production branch used for promoting the release from open testing into
  production, making it publicly available.

> **Note:** the repository's physical default branch is still `main`. Renaming it to `master`
> to match the model above is a pending git operation; the docs describe the target state.

### The GitHub mirror

Some repositories are mirrored to GitHub so a second CI pipeline verifies every change. The mirror
is **one-way** (GitLab → GitHub):

- **Never push to GitHub and never merge a pull request there.** The next GitLab push overwrites
  whatever is on GitHub.
- Issues and merge requests are still filed **on GitLab**. GitHub issue templates exist only for
  external contributors.
- GitHub uses the same label names, including the scoped-looking ones (`Status::IN PROGRESS`,
  `Priority::HIGH`). They are ordinary flat labels there and are created on demand by
  `scripts/vcs.sh`. GitHub has no scoped-label mutual exclusion, so always pass both `--add` and
  `--remove` when moving a status.
- `Closes #N` in a pull request description does **not** auto-close the issue on GitHub unless the
  pull request targets the repository default branch, which this branching model does not use.

## Project management

Issues are managed on the group-level issue board:
<https://gitlab.com/groups/robot-pathfinding-ros2-platfrom/-/boards>

Every issue carries three kinds of labels:

- **Type** — `BUG`, `FEATURE`, or `Improvement` (unscoped).
- **Priority** (scoped) — `Priority::HIGH`, `Priority::MEDIUM`, or `Priority::LOW`.
- **Status** (scoped) — `Status::WAITING`, `Status::IN PROGRESS`, `Status::CODE REVIEW`,
  `Status::QA`, `Status::ALMOST DONE`, `Status::INTERNAL`, or `Status::BETA`
  (the board column an issue sits in).

Columns (issue stages):

- **Open** — Issues are sorted in the Open column by priority, top to bottom. The issue at
  the top is the most important.
- **Status::WAITING** — Issues that can't be finished because of external factors not
  related to the assignee. Always leave a comment in the issue explaining why it can't be
  finished, tagging the related people.
- **Status::ALMOST DONE** — Issues returned from **Status::CODE REVIEW** or
  **Status::QA**. These have higher priority than issues in the **Open** column, except
  issues tagged **Priority::HIGH**. When there are high-priority issues in both
  **Status::ALMOST DONE** and **Open**, **Status::ALMOST DONE** still takes priority.
- **Status::IN PROGRESS** — The started issue you are currently working on. Only one issue
  per developer may be in this column at a time.
- **Status::CODE REVIEW** — After **Status::IN PROGRESS**, issues go to code review. Every
  feature branch requested to merge into **dev** must have this status. Code review is done
  by the lead of the technology related to the issue. From code review, an issue moves to
  **Status::ALMOST DONE** if something needs to be fixed, or to **Status::QA** when
  everything is fine.
- **Status::QA** — Testing process where changes are tested manually and/or with automated
  tests, depending on the changes. Depending on the result, the issue moves to
  **Status::ALMOST DONE** if there is a problem, or is merged into the **dev** branch when
  testing is successful.
- **Status::INTERNAL** — Internal testing process: changes from the **dev** branch are
  merged into the **staging** branch and released internally to the group's developers.
- **Status::BETA** — Open testing process: changes from the **staging** branch are merged
  into the **master** branch, making them available to beta testers.
- **CLOSED** — Issues are closed when the changes are merged from the **master** branch
  into the **production** branch.

### Time tracking

Every issue must be estimated by the person who creates it. The assignee can modify the
estimate before starting the issue, or while working on it if the estimate is not enough
to finish the task.

Time must be tracked in the issue it relates to.

Meetings must be tracked in the issue the meeting relates to. For planning meetings, create
a new issue in the related milestone and track the time there.

## Continuity & Transparency

*So anyone can pick up where you left off at any moment.*

1. **Push your work to your feature branch at the end of every day** — even if it's incomplete or doesn't compile. Use `WIP:` prefix in commit messages for unfinished work.
2. **Post a status comment on your GitLab task at the end of every day** — 2-3 sentences: what you did, what's blocking you, what you plan to do tomorrow.
3. **Update task status in GitLab immediately** when it changes — not at the end of the week. If you start working on it, move it to `Status::IN PROGRESS`. If you're blocked, move it to `Status::WAITING` and say why.

## Communication & Collaboration

*Problems grow when they're silent. Speak up early.*

4. **If you're blocked, raise it within 2 hours, not at end of day.** Post in the team channel and tag the person who can help. Don't wait for a meeting.
5. **If you find something unexpected** (wrong pinout, undocumented behavior, broken assumption), create a GitLab issue immediately — even a short one. Don't keep it in your head.
6. **If you change your approach** on a task, comment on the issue explaining what changed and why before continuing. Your future self and teammates will thank you.

## Code & Branch Hygiene

*Clean branches, clean handovers.*

7. **One task = one branch.** Name it `<issue-number>-short-description` (e.g., `62-face-recognition-analysis`).
8. **Keep commits small and meaningful.** Each commit message starts with the type: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
9. **Never push directly to `dev` or `staging`.** Everything goes through a merge request, even single-line changes.
10. **Add raw measurements, captures, and datasheets to the repo** — not to personal drives, not to chat messages. If it's project knowledge, it lives in the repo under `docs/`.

## Documentation

*If it's not written down, it doesn't exist.*

11. **Document findings as you go, not at the end.** A rough note today is worth more than a polished doc you never get to write.
12. **Use the deliverable checklists in your GitLab issues** — tick items off as you complete them. This is how we track real progress, not just time spent.
