---
name: refactoring
description: Guidelines and best practices for refactoring code safely, maintaining readability, and improving system design without altering external behavior.
license: MIT
---

# Skill: Code Refactoring

## Purpose
Refactoring is the process of restructuring existing computer code-changing the factoring-without changing its external behavior. Refactoring is intended to improve the design, structure, and/or implementation of the software, making it more readable, less complex, and easier to maintain. Follow these standards to ensure refactoring is safe and effective.

---

## General Principles

- **Refactor, then add features**: Do not mix refactoring with adding new features or fixing bugs in the same commit. Keep them as separate, atomic changes.
- **Test-Driven Refactoring**: Ensure that the codebase has adequate test coverage before refactoring. Tests are the safety net that ensures behavior hasn't changed.
- **Boy Scout Rule**: Always leave the code behind in a better state than you found it. If you see a mess, clean it up.
- **Small Steps**: Refactor in small, incremental steps. This makes it easier to catch mistakes, revert if necessary, and review changes.
- **YAGNI (You Aren't Gonna Need It)**: Do not over-engineer or add abstractions for future use cases that may never happen.

---

## Code Smells and Targets for Refactoring

- **Duplicated Code**: Extract duplicate logic into reused methods or classes following the DRY (Don't Repeat Yourself) principle.
- **Long Methods**: Break down long functions into smaller, single-purpose functions. Aim for functions that do exactly one thing well.
- **Large Classes**: Split large classes that have too many responsibilities into smaller, focused classes (Single Responsibility Principle).
- **Long Parameter Lists**: Group related parameters into cohesive data structures, objects, or structs.
- **Magic Numbers/Strings**: Replace hardcoded primitives with named constants or enums to improve readability and centralize control.
- **Deep Nesting**: Reduce nested conditions by using early returns (guard clauses) to handle edge cases immediately.

---

## Safe Refactoring Techniques

- **Extract Method/Function**: Move a cohesive block of code from a larger function into its own descriptively named function.
- **Inline Method/Function**: If a method's body is as clear as its name and only used in one place, consider removing the method and replacing calls with the body itself.
- **Rename Variable/Method**: Give variables and methods clear, expressive names that reflect their intent and context. Avoid cryptic abbreviations.
- **Introduce Explaining Variable**: Put the result of a complex, difficult-to-read expression into a temporary variable with a clear, descriptive name.
- **Replace Conditional with Polymorphism**: Instead of long `switch/case` or `if/else` chains checking types or states, use polymorphic dispatch or a strategy design pattern.
- **Encapsulate Field**: Make public fields private and provide accessors (getters/setters) to control access and modification if needed.

---

## Review and Validation

- **Run the Test Suite**: Before and after any refactoring step, run all relevant tests to verify that absolutely no functionality was broken.
- **Code Review Focus**: When reviewing a refactoring Pull Request, ensure that the focus is on structure, readability, and the strict absence of behavior changes.
- **Performance Checks**: Refactoring for readability should not introduce significant performance regressions. Profile if necessary in performance-critical execution paths.
- **Documentation**: Update any inline comments, docstrings, or external documentation that refers to the refactored code. Rely on expressive code, but keep documentation synced.

---

## Common Mistakes

- **Changing Behavior**: Accidentally altering what the code does while trying to clean up how it looks. This introduces bugs.
- **Over-abstracting**: Creating too many layers of abstraction, making the execution flow harder to follow than the original straightforward code.
- **Refactoring without Tests**: Refactoring code with low or missing test coverage is extremely risky. This is often rewriting, not refactoring.
- **Giant Pull Requests**: Combining too many varied refactoring steps into a single massive PR, making it impossible to review effectively and difficult to test.
- **"Just One More Thing"**: Getting distracted by other un-related code smells and falling down a rabbit hole of endless changes. Stick to the scope of your current refactor.
