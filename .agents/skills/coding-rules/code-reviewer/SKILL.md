---
name: code-reviewer
description: Universal code review skill. Applies to any backend or AI-integrated project. Enforces correctness, safety, maintainability, and auditability standards.
license: MIT
---

# Skill: Code Reviewer

## Purpose
Review code changes with a focus on correctness, safety, clarity, and long-term maintainability. A good review is not a hunt for style preferences - it is a structured evaluation of risk, quality, and alignment with the project's agreed design.

---

## Review Areas

### Correctness
- Does the code do what it claims to do?
- Are edge cases handled - empty inputs, null values, out-of-range parameters?
- Are boundary conditions tested and correct?
- Is error handling complete and meaningful?

### Architecture Compliance
- Does the change follow the design described in `ARCHITECTURE.md`?
- Does it respect the defined module boundaries and responsibilities?
- Does it follow the documented data flow?
- If the design changed, has `ARCHITECTURE.md` been updated in this PR?

### Security
- Is user or external input validated before use?
- Is sensitive data (credentials, keys, PII) kept out of logs, responses, and version control?
- Are permissions and access controls enforced server-side?
- Is there any risk of injection - SQL, prompt, or otherwise?
- Does the code expose internal implementation details in error messages?

### Data Integrity
- Are transactions used where multiple writes must succeed or fail together?
- Is there a risk of partial state - an operation that can succeed halfway and leave data inconsistent?
- Are writes idempotent where they need to be?

### Error Handling
- Are exceptions caught intentionally - not with a blanket catch-all?
- Are caught exceptions always logged before being transformed or re-raised?
- Does the code degrade gracefully when external dependencies fail?
- Are timeouts configured for all external calls?

### Maintainability
- Are functions focused on a single responsibility?
- Is the code easy to read without requiring the author to explain it?
- Are magic numbers, hardcoded strings, and assumptions documented or externalized to config?
- Are dependencies between modules minimal and explicit?

### Observability
- Are meaningful log messages present at appropriate levels?
- Are errors logged with enough context to diagnose the problem?
- Are there no `print` statements or debug artifacts left in production code?

### Testing
- Are new functions covered by unit tests?
- Are new integration paths covered by integration tests?
- Are tests testing behavior, not implementation details?
- Are external dependencies (APIs, LLMs, databases) mocked in unit tests?

### Code Quality
- Are type hints present on all functions in typed languages?
- Are public functions and classes documented with docstrings?
- Is the code consistent with the conventions already in the project?
- Is there any dead code, commented-out logic, or unused imports?

### Documentation
- Is `CHANGELOG.md` updated if the change is user-facing (new feature, bug fix, breaking change, security fix)?
- Is `ARCHITECTURE.md` updated if the change affects system structure or design decisions?
- Are docstrings updated for modified public functions?
- Are API descriptions updated if endpoints changed?

### Git & PR
- Does the commit message follow the project's convention (Conventional Commits)?
- Is the PR focused on a single logical change?
- Is there a clear description of what the change does and why?

---

## Severity Guide

| Rating | When to Use |
|---|---|
| **Block - must fix** | Security vulnerability, data integrity risk, broken functionality, missing critical validation, breaking change without CHANGELOG entry |
| **Major - should fix** | Missing error handling, no tests for new logic, missing CHANGELOG or ARCHITECTURE update, unclear or misleading naming |
| **Minor - nice to fix** | Style inconsistency, redundant code, minor readability improvement |
| **Note** | A suggestion or alternative approach worth considering but not requiring action |

---

## Review Decision

- ✅ **Approved** - no significant issues
- 🟡 **Approved with notes** - minor issues noted; no blocking concerns
- ❌ **Changes requested** - one or more major or blocking issues must be addressed before merge
