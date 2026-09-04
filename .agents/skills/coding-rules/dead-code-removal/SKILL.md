---
name: dead-code-removal
description: "Universal skill for identifying and safely removing dead code: unused imports, unreachable branches, stale feature flags, commented-out blocks, and orphaned test helpers. Keeps any codebase lean, auditable, and honest."
license: MIT
---

# Skill: Dead Code Removal

## Purpose

Dead code silently increases cognitive load, misleads future developers, bloats build artifacts, slows import times, and hides real logic inside noise. Every unreachable branch is a liability: it cannot be meaningfully tested, so it cannot be trusted. Remove it.

---

## What Counts as Dead Code

| Category | Description |
|---|---|
| Unused imports | A module or symbol is imported at the top of a file but never referenced anywhere in that file. |
| Unused variables | A variable is assigned a value that is never read after the assignment. |
| Unreachable branches | Code that can never execute at runtime, such as a block following an unconditional `return` or `raise`, or a branch guarded by a constant that is always `True` or always `False`. |
| Commented-out code | Disabled code blocks left in the source under the assumption that they may be needed again. |
| Stale feature flags | Flags whose values are hard-coded constants with no environment-driven toggle mechanism, making the flag meaningless. |
| Orphaned functions and classes | Symbols with no call sites, no subclasses, and no test coverage - they are never invoked at runtime. |
| Orphaned modules | Entire source files that nothing in the codebase imports. |
| Stale test helpers | Fixtures and utility functions defined for tests but never referenced by any test function. |
| Shadowed assignments | A variable is assigned a value that is immediately overwritten before it is ever read, making the first assignment invisible. |
| Unacted-on TODO comments | A `TODO` comment older than one release cycle that has no associated tracking issue and no plan to implement it. |

---

## Detection Tools

The following tools should be run as part of every pre-push check. Adapt tool names to fit the project's existing linting configuration.

Most linters provide rules for unused imports and unused variables. For Python projects, `ruff` covers unused import detection and assigned-but-unused variable detection. Static type checkers such as `mypy` and `pyright` can surface unreachable code paths. Whole-project unused symbol scanners such as `vulture` perform a broader sweep across the codebase but produce false positives for symbols resolved dynamically through dependency injection, plugin registries, or framework magic. Treat `vulture` output as a lead, not a verdict - always confirm manually before deleting. The most reliable confirmation tool is a simple text search across the entire codebase, including test directories, to ensure a symbol is truly referenced nowhere.

---

## Rules by Category

### Imports

Remove all unused imports. Do not comment out an import as a safety measure - if it is not used today, delete it; version control preserves the history. Do not leave symbols in an explicit export list (such as `__all__` in Python) after they have been removed from the module, because this causes attribute errors for any consumer that imports from it. After editing a file, consolidate imports from the same module to avoid scattered single-name imports across multiple lines.

### Variables and Assignments

Delete variables that are assigned a value but never subsequently read. If a function must be called for its side effect but its return value is irrelevant to the caller, use the language's conventional throwaway variable (in Python this is `_`). Do not commit debugging output statements - use the project's structured logger for any diagnostic output that is genuinely needed.

### Functions and Methods

A function with no call sites and no test coverage is orphaned code. Delete it. The exception is any symbol that forms a public contract: API endpoints, CLI entry points, registered hooks, event handlers, and exported library functions are legitimately called by external consumers or the framework itself and must not be deleted based solely on an absence of internal callers. Private helpers - those marked with a leading underscore by convention - with no callers within the same class or module must be removed.

### Classes

A class with no instantiation sites, no subclasses, and no tests is orphaned. Before deleting it, search for references in type annotations, `isinstance` checks, and any export list, because these reference forms are invisible to simple call-site searches.

### Branches and Conditions

Do not commit branches guarded by constant `True` or `False` conditions. Resolve the condition by keeping only the live branch. Any code that appears after an unconditional exit point - such as a `return`, `raise`, `break`, or `continue` - is unreachable and must be removed. When an `else` block is made entirely unreachable by the preceding branch's exit point, remove the `else` keyword and de-indent the block.

### Commented-Out Code

Never commit commented-out code. Version control history is the mechanism for recovering deleted code; reference a specific commit identifier in a comment if necessary, then delete the block. Linter suppression comments (`noqa`, `fmt: off`, `type: ignore`) without a specific, documented justification in the same comment are not an acceptable alternative to fixing the underlying issue.

### Tests

Delete test functions that reference deleted production code. Orphaned tests that compile and pass but assert nothing meaningful are worse than no tests - they create false confidence in coverage metrics. Delete unused fixtures and utility functions from shared test configuration files.

### Feature Flags

A flag whose value is a hard-coded constant permanently set to enabled should have its flag infrastructure removed and the code path made permanent in a single clean commit. A flag whose value is a hard-coded constant permanently set to disabled should have the entire dead branch and the flag itself deleted. Live feature flags - those that are actively toggled - must be read from the project's configuration system (environment variables or a feature flag service), never from hard-coded literals.

---

## Safe Removal Workflow

Identify candidates using the project's detection tools. Confirm that the symbol is truly unreachable by searching the full codebase, including dynamic usage patterns such as string-based lookups, `getattr` calls, plugin manifests, and serialization schemas. Remove dead code in a dedicated commit that is separate from feature work or bug fixes, using a maintenance-type commit prefix such as `chore:`. Run the full test suite after removal to confirm that no accidental hidden dependency existed. If the deleted code was non-obvious in purpose, record the reason for deletion in the commit message rather than in a source comment.

---

## Code Review Stance

Reject the following without discussion in any pull request review. They are not style preferences; they are code quality gates.

- Commented-out code blocks added in the diff.
- Debug output statements (`print`, `pprint`, or equivalent).
- Variables assigned but never read.
- Branches guarded by constant `True` or `False`.
- Code appearing after an unconditional exit point.

---

## Review Checklist

- [ ] No unused import violations reported by the linter.
- [ ] No assigned-but-never-used variable violations reported by the linter.
- [ ] No commented-out code blocks in the diff.
- [ ] No debug output statements.
- [ ] No unreachable code after exit points.
- [ ] Removed functions have corresponding test cleanup.
- [ ] Removed classes have no lingering references in type annotations or export lists.
- [ ] Whole-project unused symbol scanner output reviewed and actionable items addressed.
- [ ] Feature flags that are permanently resolved are removed rather than left as constants.
