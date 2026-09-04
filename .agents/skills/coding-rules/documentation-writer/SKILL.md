---
name: documentation-writer
description: Universal documentation skill. Covers docstrings, README, CHANGELOG, ARCHITECTURE, API documentation, and technical specifications for any project.
license: MIT
---

# Skill: Documentation Writer

## Purpose
Write and maintain documentation that is accurate, minimal, and useful. Documentation has two audiences: developers who need to understand and modify the system, and future readers (including AI agents) who use it as a source of truth. Outdated documentation is worse than no documentation - it actively misleads.

---

## Documentation Principles

**Write for the reader, not the writer.** Documentation explains intent and behavior, not the author's implementation journey. Avoid "I decided to..." - write "This module handles...".

**Document why, not just what.** Code can show what it does. Documentation should explain why a decision was made - especially when the implementation is non-obvious or constrains future changes.

**Keep it current.** Documentation that drifts from the implementation erodes trust in the entire codebase. Update docs as part of the same PR that changes the behavior.

**Less is more.** A short, accurate document is more valuable than a long, comprehensive one that is never fully read. Remove content that no longer applies rather than leaving it as historical record.

---

## Document Inventory

| Document | Purpose |
|---|---|
| `README.md` | Entry point for anyone new to the project |
| `CHANGELOG.md` | Human-readable record of every meaningful change |
| `ARCHITECTURE.md` | Authoritative record of system design and key decisions |
| `SPEC.md` (or equivalent) | Behavioral and data contracts for a module or system |
| Docstrings in source | In-place documentation of functions and classes |
| API / OpenAPI descriptions | What each endpoint does, expects, and returns |

---

## Docstrings

Every public function, class, and method must have a docstring. Expected format:
- **First line:** a concise imperative summary ("Return the...", "Compute the...", "Validate that...")
- **Args / Parameters:** describe each parameter's purpose and any important constraints
- **Returns:** describe what is returned and its type (skip for void functions)
- **Raises:** list any exceptions the function explicitly raises and when

Private helpers benefit from at least a summary line. Skip docstrings only for trivially self-evident code.

---

## README.md

The README is the entry point for anyone new to the project. It must contain:
- What the project does (one paragraph maximum)
- How to set it up and run it locally
- How to run the tests
- Any key environment variables or configuration requirements
- Links to CHANGELOG.md, ARCHITECTURE.md, and SPEC.md

Keep the README scannable. Use headers and bullet points. Avoid prose paragraphs for setup steps.

---

## CHANGELOG.md

Maintain CHANGELOG.md following the Keep a Changelog format. Full conventions are in `.agents/skills/coding-rules/changelog-maintainer/SKILL.md`.

Key rules for documentation purposes:
- Update CHANGELOG.md in the same PR as the code change - never after the fact
- Write entries for humans, not for git log readers
- Mark breaking changes explicitly with **BREAKING:**
- The `[Unreleased]` section is always at the top and accumulates changes until a version is released

Update CHANGELOG.md whenever:
- A new feature or capability is added
- A bug is fixed
- A breaking change is introduced
- A security issue is resolved
- A configuration variable or API contract changes

---

## ARCHITECTURE.md

Maintain ARCHITECTURE.md as the authoritative record of system design. Full conventions in `.agents/skills/coding-rules/architecture/SKILL.md`.

Key rules for documentation purposes:
- Update ARCHITECTURE.md in the same PR as any structural change
- Document key design decisions with their rationale - not just what was decided, but why
- Keep the Non-Goals section current - it prevents well-intentioned scope creep
- Never silently overwrite a past decision; note what changed and why

Update ARCHITECTURE.md whenever:
- A new module or major component is introduced
- Data flow between components changes
- A new external dependency is introduced
- A key design decision is made, revised, or reversed
- Module responsibilities are intentionally redefined

---

## Specification Documents (SPEC.md or equivalent)

Specs are the source of truth for system behavior and design contracts. They should cover:
- Module purposes and responsibilities
- Data models with field names, types, and descriptions
- API surface (endpoints, request/response shapes)
- Rules and constraints that govern behavior
- Non-goals - what the system explicitly does not do

Update the spec version when behavior or contracts change. Remove descriptions of capabilities that no longer exist - do not leave them struck through.

---

## API Documentation

Every route or endpoint must be documented with:
- A clear summary of what it does
- Required authentication or authorization
- Request parameters or body schema
- Response schema for success and error cases
- Any notable behaviors (idempotency, caching, rate limits)

---

## Writing Style

- **Concise:** get to the point; expand only where necessary
- **Present tense for descriptions:** "Returns a list of..." not "Will return..."
- **Active voice:** "The module validates..." not "Validation is performed by..."
- **Use MUST, MUST NOT, SHOULD, MAY** (RFC 2119 conventions) for normative requirements in spec documents
- **Factual:** describe behavior as it is; avoid aspirational statements unless clearly labeled as roadmap

---

## When to Update Documentation

| Trigger | What to Update |
|---|---|
| New feature added | README (if setup changes), CHANGELOG, SPEC |
| Bug fixed | CHANGELOG |
| Breaking change | CHANGELOG (marked BREAKING), SPEC, README if behavior is user-visible |
| New API endpoint | SPEC, API docs, CHANGELOG |
| Structural design change | ARCHITECTURE.md |
| New configuration variable | README, deployment notes, CHANGELOG |
| Feature removed | CHANGELOG, remove from SPEC and README |
| Key design decision made | ARCHITECTURE.md |

---

## Common Mistakes

- Documenting intended future behavior as if it is already implemented
- Leaving TODO comments in public-facing documentation - open a tracked issue instead
- Copy-pasting documentation from one place to another without updating it
- Writing documentation after the fact from memory - introduces inaccuracies
- Using vague language like "handles errors appropriately" - be specific
- Updating ARCHITECTURE.md without explaining why a decision changed
- Forgetting to update CHANGELOG.md and only discovering the omission at release time
