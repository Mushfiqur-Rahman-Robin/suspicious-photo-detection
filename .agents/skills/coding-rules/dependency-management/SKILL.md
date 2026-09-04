---
name: dependency-management
description: Universal skill for managing third-party dependencies. Covers selection criteria, version pinning, security scanning, and update practices.
license: MIT
---

# Skill: Dependency Management

## Purpose
Every dependency is a risk - it can introduce vulnerabilities, break on upgrade, go unmaintained, or pull in transitive dependencies that conflict. Managing dependencies carefully is not over-engineering; it is basic risk management for production software.

---

## Before Adding a Dependency

Ask these questions before adding any new third-party package:

- **Is it necessary?** Can this be accomplished with a standard library or a modest amount of first-party code?
- **Is it maintained?** When was the last release? Does it have active maintainers? Are issues being addressed?
- **Is it widely used?** A well-adopted package is more likely to have security issues caught quickly and fixed reliably.
- **What does it bring in?** Check its transitive dependencies - a single package can pull in dozens of others.
- **What is the license?** Ensure it is compatible with the project's license and usage.
- **Does it have known vulnerabilities?** Check before adding, not after.

If a dependency adds significant capability, document the decision briefly in `ARCHITECTURE.md` or an ADR (Architecture Decision Record).

---

## Version Pinning

- **Pin exact versions in production applications.** Floating versions (`>=1.0`) will silently install a newer version that may break behavior.
- **Use a lock file** (e.g., `requirements.lock`, `package-lock.json`, `poetry.lock`) and commit it - this ensures every developer and CI environment uses exactly the same versions.
- **Separate direct from transitive dependencies.** Know which packages you are explicitly depending on vs. which are pulled in indirectly.
- **Document why a version is pinned to a specific version** if it is pinned lower than current (e.g., a known breaking change in a newer version).

---

## Dependency Hygiene

- Keep a clear separation between production dependencies and development/test dependencies. They must not be mixed.
- Remove unused dependencies - they add attack surface without value.
- Prefer fewer, well-scoped dependencies over many small ones.
- If two packages provide similar functionality, standardize on one across the project.

---

## Security Scanning

- Run a dependency vulnerability scan as part of every CI pipeline (e.g., `pip-audit`, `npm audit`, `trivy`, `snyk`)
- **Critical or high severity vulnerabilities must be resolved before merging.** A known CVE in a dependency is an accepted risk that must be consciously documented or eliminated.
- Scan transitive dependencies, not only direct ones.
- Configure the scanner to fail the build on findings above a defined severity threshold.

---

## Update Practices

- Update dependencies regularly - waiting until something breaks means updates arrive in crisis mode
- Update one dependency at a time in a dedicated branch so any regression can be isolated quickly
- Run the full test suite after every dependency update before merging
- Review the changelog of any package being updated - especially for major version bumps
- Treat major version bumps as potentially breaking - test thoroughly and update CHANGELOG.md if behavior changes
- Pin the previously working version explicitly when a dependency update causes a regression, and open a tracking issue

---

## Lock File Policy

- The lock file is always committed to version control
- The lock file is updated intentionally - not as a side effect of other work
- Lock file changes with no corresponding `dependencies` or `changed` entry in CHANGELOG.md should be questioned in review
- In CI, dependencies are installed from the lock file - never resolved fresh

---

## Common Mistakes

- Adding a dependency for one small utility function that could be implemented in 10 lines
- Not checking the license of a dependency used in a commercial product
- Committing `node_modules/`, `.venv/`, or equivalent - commit the lock file, not the installed packages
- Updating all dependencies at once - makes regressions impossible to isolate
- Ignoring vulnerability scan output until a security incident occurs
- Using a package that has not had a commit in over two years without explicitly evaluating and accepting the maintenance risk
