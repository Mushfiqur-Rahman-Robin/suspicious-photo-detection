---
name: changelog-maintainer
description: Universal skill for maintaining CHANGELOG.md. Covers the Keep a Changelog format, update triggers, versioning conventions, and common mistakes.
license: MIT
---

# Skill: Changelog

## Purpose
Maintain a clear, human-readable record of every meaningful change to the project. A changelog is not a git log - it is written for humans who need to understand what changed, why it matters, and whether they need to act (e.g., migrations, breaking changes). Every meaningful change must be recorded here before it is merged.

---

## Format Standard

Follow the [Keep a Changelog](https://keepachangelog.com) format. This is the industry standard and keeps changelogs consistent, parseable, and predictable.

**Structure:**

```
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- ...

### Changed
- ...

### Deprecated
- ...

### Removed
- ...

### Fixed
- ...

### Security
- ...

## [1.2.0] - 2026-07-03

### Added
- ...
```

---

## Rules

### Always update CHANGELOG.md in the same PR as the change
The changelog entry must be part of the same pull request as the code it describes - not a follow-up commit. A PR without a changelog entry is incomplete unless the change is explicitly exempt (see below).

### Write entries for humans, not machines
- Write from the perspective of a developer or user upgrading to this version
- Describe the impact, not the mechanism: "API now returns 422 for malformed requests" not "Added validation in handler.py line 34"
- Use plain language - no jargon specific to the internal implementation

### Use the correct section
| Section | Use for |
|---|---|
| `Added` | New features, new endpoints, new configuration options |
| `Changed` | Changes to existing behavior, updated defaults, modified API contracts |
| `Deprecated` | Features that still work but will be removed in a future version |
| `Removed` | Features, endpoints, or config options that have been deleted |
| `Fixed` | Bug fixes |
| `Security` | Changes that address a vulnerability - always include these |

### Breaking changes must be prominently marked
If a change requires consumers to update their code, configuration, or data, mark it clearly:

```
### Changed
- **BREAKING:** The `entity_ref` field in anomaly signals now requires `entity_type` to be
  one of the registered domain values. Previously accepted any string.
```

### The `[Unreleased]` section is always at the top
All in-progress work goes into `[Unreleased]`. When a release is cut, `[Unreleased]` becomes the new version section and a fresh `[Unreleased]` is added above it.

### Versions follow Semantic Versioning
- **MAJOR** - breaking change; consumers must take action to upgrade
- **MINOR** - new capability added in a backward-compatible way
- **PATCH** - backward-compatible bug fix

---

## What Requires a Changelog Entry

| Change Type | Requires Entry |
|---|---|
| New feature or capability | ✅ Yes |
| Bug fix | ✅ Yes |
| Breaking change of any kind | ✅ Yes (mark as BREAKING) |
| Security fix | ✅ Yes (in Security section) |
| New or modified configuration variable | ✅ Yes |
| New or modified API endpoint or response shape | ✅ Yes |
| Dependency upgrade that changes behavior | ✅ Yes |
| Refactoring with no external behavior change | ❌ No |
| Test-only changes | ❌ No |
| Documentation-only changes | ❌ No (optional) |
| CI/CD pipeline changes | ❌ No (optional) |

---

## Common Mistakes

- Writing changelog entries after release, from memory - entries become vague and incomplete
- Logging every commit rather than every meaningful change - changelogs are not git logs
- Using implementation language: "Refactored service layer to use repository pattern" - say what changed for users, not for developers
- Omitting breaking changes or marking them as `Changed` without a BREAKING label
- Leaving `[Unreleased]` empty at release time - the release has no documented changes
