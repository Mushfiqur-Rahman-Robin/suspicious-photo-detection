---
name: verify-alignment
description: Universal release gate skill. Synthesizes code review, alignment check, security audit, and test validation into a single go/no-go decision before merge or release.
license: MIT
---

# Skill: Verify Alignment

## Purpose
This is the final checkpoint before code is merged to the main branch or released to production. It combines code review, spec alignment, security audit, and test verification into a single structured pass/fail decision. Do not skip this step for any meaningful change.

---

## When to Run

- Before merging a feature branch to `main`
- Before any production release or hotfix
- After significant refactoring that touches multiple modules
- When a change affects security-sensitive areas, data access, or external integrations

---

## Verification Steps

### Step 1 - Tests
Run the full automated test suite.

Gate: All unit tests pass. All integration tests pass. Coverage meets project thresholds. No external services were called during the test run.

### Step 2 - Static Analysis
Run linting, type checking, and dependency/security scanning.

Gate: No linting errors. No type errors. No dependency vulnerabilities above the accepted severity threshold.

### Step 3 - Code Review
Confirm a code review has been completed using the `.agents/skills/coding-rules/code-reviewer/SKILL.md` skill.

Gate: No blocking issues remain open. Any approved-with-notes items are tracked in the issue tracker.

### Step 4 - Spec Alignment
Work through the `.agents/skills/coding-rules/alignment-checker/SKILL.md` skill for any feature with documented requirements.

Gate: All applicable spec items are aligned. No significant deviations from agreed design.

### Step 5 - Security Audit
Work through the `.agents/skills/coding-rules/security-auditer/SKILL.md` skill for any change touching authentication, data access, external services, or configuration.

Gate: No critical or high-severity findings remain open.

### Step 6 - Architecture Compliance
Verify the change follows and is reflected in `ARCHITECTURE.md`.

Gate: The change respects all module boundaries and data flows described in ARCHITECTURE.md. If the design changed, ARCHITECTURE.md has been updated in this PR with the rationale.

### Step 7 - Changelog
Verify `CHANGELOG.md` is updated for any user-facing change.

Gate: All new features, bug fixes, breaking changes, and security fixes have a CHANGELOG entry in the `[Unreleased]` section. Breaking changes are explicitly marked as **BREAKING:**. Entries are written for humans, not as git log summaries.

### Step 8 - Documentation
Verify all documentation is current for everything changed in this release.

Gate: Docstrings updated for modified public functions. SPEC updated if data contracts or API changed. README updated if setup or configuration changed.

---

## Final Checklist

**Correctness**
- [ ] Core logic behaves as specified and is covered by tests
- [ ] Edge cases are handled and tested

**Security**
- [ ] No secrets in code, logs, or responses
- [ ] Access control enforced for all new or modified endpoints
- [ ] Input validation present for all external inputs

**Error Handling**
- [ ] External calls have timeouts configured
- [ ] Fallback or degraded mode exists for non-critical dependency failures
- [ ] No exceptions silently swallowed

**Data Integrity**
- [ ] Database migrations tested in staging before production
- [ ] No partial write scenarios that could leave data in an inconsistent state

**Architecture**
- [ ] Change respects all module boundaries in ARCHITECTURE.md
- [ ] If design changed, ARCHITECTURE.md is updated with rationale

**Changelog**
- [ ] CHANGELOG.md `[Unreleased]` section has entries for all user-facing changes
- [ ] Breaking changes are marked **BREAKING:**
- [ ] Entries are written from the consumer's perspective, not the implementation's

**Observability**
- [ ] Meaningful logs present for new operations
- [ ] Errors are logged with enough context for diagnosis

**Deployment Readiness**
- [ ] Rollback plan is known before deployment begins
- [ ] All required environment variables are documented and provisioned

**Documentation**
- [ ] Docstrings, SPEC, and README are current
- [ ] Any breaking changes are clearly marked and communicated

**Git**
- [ ] Commit messages follow the project convention
- [ ] PR description explains what and why

---

## Verdict

- ✅ **Pass** - all gates cleared; safe to merge or deploy
- 🟡 **Conditional pass** - minor issues noted and tracked; no blocking concerns
- 🔴 **Fail** - one or more blocking items unresolved; must fix before merge or release
