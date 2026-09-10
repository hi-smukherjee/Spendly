---
description: Commit, push, open a PR, merge it, and delete the local branch for a finished feature
argument-hint: [commit message]
allowed-tools: Bash(git *), Read, Grep, Glob, mcp__github__get_me, mcp__github__create_pull_request, mcp__github__pull_request_read, mcp__github__merge_pull_request
---

# Ship Feature

Ship the current feature branch end-to-end: **commit → push → PR → merge → clean up local branch**.

Current branch: !`git branch --show-current`
Status: !`git status --short`

Never run this against `main`/`master` — stop and tell the user if the current branch is the default branch.

## Step 1 — Commit

1. Run `git status` and `git diff` to see what changed.
2. Stage the relevant changes with `git add`. Leave out stray scratch/DB files (e.g. `*.db` copies) unless the user clearly wants them tracked.
3. Commit:
   - If `$ARGUMENTS` was given, use it as the commit message.
   - Otherwise write a concise message summarizing the diff.
4. If there is nothing to commit (clean tree), skip to Step 2 using the existing HEAD.

## Step 2 — Push

Push the branch to `origin` and set upstream:

```
git push -u origin <current-branch>
```

Confirm with the user before pushing if you're unsure the changes are ready to be public.

## Step 3 — Pull Request

1. Determine the repo `owner`/`repo` (from `git remote get-url origin`, or `mcp__github__get_me` plus the remote) and the default base branch (`main`).
2. Check for a PR template: `.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE/*`. Use it to structure the body if present.
3. Create the PR with `mcp__github__create_pull_request` (`head` = current branch, `base` = `main`).
4. Share the PR URL with the user.

## Step 4 — Merge

1. **Confirm with the user before merging** — this is an outward-facing, hard-to-reverse step.
2. Check PR status with `mcp__github__pull_request_read` (`get_status` / `get_check_runs`). If checks are failing, stop and report instead of merging through them.
3. Merge with `mcp__github__merge_pull_request` (default `merge_method: "squash"` unless the user prefers otherwise).

## Step 5 — Clean up local branch

```
git checkout main
git pull
git branch -d <feature-branch>
```

Use `git branch -D` only if the user explicitly confirms a force-delete is fine (e.g. the merge used a strategy where `-d` won't detect the branch as merged).

## Notes

- Stop and report at the first failure (push rejected, PR checks red, merge conflict) rather than forcing through.
- Steps 2 and 4 (push, merge) are the risky/irreversible ones — always get explicit go-ahead before running them unless the user already said "ship it" for this exact change.
