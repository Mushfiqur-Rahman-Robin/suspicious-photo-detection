---
name: git-conventions
description: Universal skill for consistent git usage. Covers commit messages, branching strategy, pull request standards, and merge practices.
license: MIT
---

# Skill: Git Conventions

## Purpose
Consistent git practices make a codebase history readable, reviewable, and recoverable. They reduce friction in code review, simplify debugging with `git bisect`, and enable meaningful changelogs. These conventions apply to every developer and AI agent contributing to the project.

---

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org) specification. Every commit message must communicate what changed and why.

**Format:**
```
<type>(<scope>): <short summary>

<optional body>

<optional footer>
```

**Types:**
| Type | When to Use |
|---|---|
| `feat` | A new feature or capability |
| `fix` | A bug fix |
| `refactor` | Code restructuring with no behavior change |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `chore` | Tooling, CI, dependency updates, config |
| `perf` | Performance improvement |
| `security` | Security fix |
| `build` | Build system or packaging changes |

**Rules:**
- The summary line is 72 characters maximum
- Use the imperative mood: "Add validation" not "Added validation" or "Adds validation"
- The scope is optional but helpful - use the module or area affected (e.g., `feat(auth):`, `fix(payment):`)
- Breaking changes must be noted in the footer: `BREAKING CHANGE: <description>`
- The body explains the *why*, not the *what* - the diff shows what changed

**Examples:**
```
feat(detection): add percentage deviation detection method

fix(prompt): prevent null reference when tenant language is not set

docs(readme): update local setup instructions for new env variable

BREAKING CHANGE: The signal schema now requires severity_basis to be non-null.
Consumers must update their parsers before upgrading.
```

---

## Branching Strategy

Use a consistent naming convention for all branches.

**Pattern:** `<type>/<short-description>`

| Prefix | Use |
|---|---|
| `feat/` | New feature work |
| `fix/` | Bug fix |
| `refactor/` | Refactoring |
| `docs/` | Documentation updates |
| `chore/` | Tooling, CI, dependency changes |
| `security/` | Security fixes |
| `hotfix/` | Production hotfix (branches from main or release tag) |

**Rules:**
- Use lowercase and hyphens - no spaces or underscores
- Keep names short and descriptive: `feat/duplicate-invoice-detection` not `feat/johns-new-feature`
- Delete branches after they are merged - keep the remote clean
- Never commit directly to `main` or `develop` - always work on a branch

---

## Pull Requests

**Before opening a PR:**
- The branch is up to date with the base branch
- All tests pass locally
- Linting and type checking pass
- CHANGELOG.md is updated (if the change is user-facing)
- ARCHITECTURE.md is updated (if the design changed)

**PR description must include:**
- What the change does (one paragraph)
- Why the change is needed
- How to test or verify it
- Any relevant context for the reviewer (design decisions, tradeoffs, known limitations)

**PR size:**
- Keep PRs focused - one logical change per PR
- If a PR is too large to review in a single session, it should be split
- Draft PRs are acceptable for early feedback before a change is complete

**Review requirements:**
- At least one approval required before merging
- All review comments must be resolved or explicitly deferred before merge
- The author merges - not the reviewer

---

## Merge Practices

- Use **squash merge** for feature branches - keeps main history clean and readable
- Use **merge commit** (not squash) for long-lived branches where individual commit history is meaningful
- Do not use force-push on shared branches
- Rebase local feature branches on top of the base branch to keep them current - do not merge the base branch into the feature branch
- Delete the feature branch immediately after merging

---

## What Not to Do

- Committing large chunks of unrelated changes together - makes review and bisect painful
- Using vague commit messages: "fix", "update", "wip", "changes" - say what changed
- Committing directly to main or shared branches
- Leaving stale branches in the remote after merging
- Including secrets, credentials, or generated files in commits
- Force-pushing to a shared or protected branch
