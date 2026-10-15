# Development process

How changes get from an idea to `main`, how versions are tracked, and how to undo things.
Written for Z (owner/approver); the agent follows the same process (see `CLAUDE.md`).

## The flow

```
research ──► proposal issue ──► Z approves ──► feature branch ──► pull request ──► CI ──► Z merges
                (label: proposal)   (adds label: approved)   feat/<#>-<slug>      "Closes #<#>"
```

1. **Proposal.** The agent opens an issue labeled `proposal` describing the problem, what you'll
   see, the approach, acceptance criteria and size. Nothing is coded yet.
2. **Your decision.** On the issue:
   - **Approve:** add the `approved` label.
   - **Change it:** comment what you want different; the agent revises and waits.
   - **Reject:** close the issue (optionally label `wontfix`).
3. **Build.** The agent codes only approved proposals, on a branch named `feat/<issue#>-<slug>`.
4. **Pull request.** It opens a PR linked to the issue. CI runs lint, tests on Python 3.10–3.12
   and Windows, and a Docker build. The PR says how to try it locally:
   `git fetch && git switch feat/<#>-<slug> && ./dev.sh`.
5. **Review.** Comment on lines or use "Request changes"; the agent addresses them next run.
6. **Merge.** Only you merge. Use **Squash and merge** so each feature is exactly one commit on
   `main` — that's what makes undoing a feature a one-click operation.

Questions from the agent are issues labeled `question`; answer by commenting.
Research notes arrive as `docs/research-<date>` PRs — merge them when you've skimmed them.

## Version history and change logs

| Layer | What it gives you | Where |
|---|---|---|
| Git history | Every change, who made it, why (one squashed commit per PR) | Commits tab |
| Pull requests | The discussion, review and CI result behind each change | Pull requests → Closed |
| Issues | The original proposal and your approval | Issues → `proposal` label |
| CHANGELOG.md | Human-readable list of changes per version (Keep a Changelog) | repo root |
| Tags + Releases | Named snapshots like `v1.2.0` you can return to (Semantic Versioning) | Releases |

**Versioning (SemVer):** `MAJOR.MINOR.PATCH` — new features bump MINOR (1.1 → 1.2), fixes bump
PATCH (1.2.0 → 1.2.1), breaking changes bump MAJOR. Ask the agent for a release whenever a batch
of features is worth naming; it opens a release PR, and after you merge it, tags the version and
publishes a GitHub Release with the changelog notes.

## Going back

| Situation | Do this |
|---|---|
| Don't like a feature that was merged | Open the merged PR on GitHub → **Revert** → merge the revert PR. History is kept; only that feature is undone. (Or tell the agent "revert #N".) |
| Want to see / run an older version | `git switch --detach v1.1.0 && ./dev.sh` — then `git switch main` to come back. |
| Want the whole app back at a past release | Ask for a revert PR of everything after that tag, or deploy the tag. Avoid rewriting `main` history. |
| A PR isn't right yet | Request changes, or just close it — nothing reaches `main` until you merge. |
| Undo a proposal you approved but that isn't built | Remove the `approved` label. |

Because nothing reaches `main` without your merge and every feature is one commit, every step is
reversible without force-pushing or losing history.

## Branch naming and commits

- `feat/<issue#>-<slug>`, `fix/<issue#>-<slug>`, `docs/<slug>`, `chore/<slug>`
- Conventional Commits: `feat: …`, `fix: …`, `docs: …`, `chore: …`, `test: …`, `refactor: …`

## Recommended repo setting (owner action)

Protect `main` (Settings → Branches → Add rule): require a pull request before merging and require
the CI checks to pass. Leave "Do not allow bypassing" off so you can still push in an emergency.
Set Settings → General → Pull Requests to allow **squash merging** (and optionally disable the others).
