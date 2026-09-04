---
name: test-runner
description: Universal testing skill. Applies to any backend or AI-integrated project. Covers test organization, unit and integration testing principles, mocking rules, and coverage standards.
license: MIT
---

# Skill: Test Runner

## Purpose
Write and maintain a test suite that gives the team genuine confidence in the system. Tests are not a formality - they are the primary mechanism for catching regressions, verifying behavior, and enabling safe refactoring. A test suite that passes but provides no real confidence is worse than no tests at all.

---

## Core Principles

**Test behavior, not implementation.** A test should verify what the code does, not how it does it internally. Tests tied to implementation details break on every refactor, even when behavior is unchanged.

**One assertion per logical concern.** Tests are easier to diagnose when each test has a clear, focused purpose. Multiple assertions are fine when they collectively verify a single behavior.

**Every test must be deterministic.** A test that sometimes passes and sometimes fails is not a test - it is noise. If a test is flaky, fix it before merging.

**Mock at the boundary.** Mock external dependencies (databases, APIs, LLMs, file systems) in unit tests. Integration tests may use real dependencies in a controlled environment. Never call real external services in automated test runs.

**Tests are part of the codebase.** Test code deserves the same care as production code: clear naming, no duplication, and structured fixtures.

---

## Test Organization

Structure tests to mirror the source code:

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/                # Fast, isolated; one file per module or class
└── integration/         # Slower; tests components working together
```

- Unit tests should run in seconds - keep them fast
- Integration tests may be slower but must still be deterministic
- Separate unit and integration test runs in CI to get fast feedback early

---

## Unit Tests

Unit tests verify a single function or class in isolation.

**What to cover for every function:**
- Normal/happy path - correct input produces correct output
- Edge cases - empty collections, zero values, boundary values, maximum values
- Error cases - what happens when invalid input is provided
- Any code branch that handles an exceptional or optional condition

**Mocking rules:**
- Mock all I/O: database queries, HTTP calls, file reads, LLM calls
- Mock at the interface level, not deep inside an implementation
- Verify that mocks are called with the expected arguments when interaction matters

---

## Integration Tests

Integration tests verify that components work correctly together.

**What to cover:**
- The full happy-path flow from input to output through multiple layers
- The behavior of the system when a dependency is unavailable or returns an error
- Authorization and access control - ensure users can only access what they are permitted to
- Data isolation - where applicable, ensure one user or tenant cannot access another's data

**Environment:**
- Use a dedicated test database or an in-memory equivalent
- Reset state between tests - do not let tests share or depend on each other's data
- Never use production credentials or real external services

---

## What Every Module Needs

For every new module or feature, write tests that cover at minimum:
- The primary success path
- At least one failure or error path
- Any access control or authorization logic
- Any data isolation boundary (multi-tenant, multi-user, etc.)

---

## Coverage

Coverage is a signal, not a goal. Aim for meaningful coverage, not metric gaming.

| Guideline | Target |
|---|---|
| Core business logic | ≥ 85% |
| Application layer (routes, handlers) | ≥ 75% |
| Utility / helper modules | ≥ 80% |
| Overall project | ≥ 80% |

Coverage below these thresholds is a flag for review, not an automatic block. Uncovered code must be explained and tracked.

---

## CI Gates

Before merging any branch:
- All unit tests pass
- All integration tests pass
- Coverage meets the project threshold
- No tests were skipped without documented justification
- No real external services were called during the test run

---

## Common Mistakes to Avoid

- Writing tests that only verify the happy path
- Mocking so many things that the test no longer verifies real behavior
- Testing private methods or internal implementation details directly
- Leaving flaky tests in the suite without fixing them
- Writing integration tests that depend on external service availability
- Asserting on exact log message strings (fragile and change-prone)
