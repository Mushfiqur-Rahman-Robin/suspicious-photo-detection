---
name: architecture
description: Universal skill for reading, following, and maintaining ARCHITECTURE.md. Ensures every code change respects the agreed system design.
license: MIT
---

# Skill: Architecture

## Purpose
ARCHITECTURE.md is the authoritative record of how the system is designed and why. Every developer and AI agent working on the project must read it before making structural decisions. Every structural change must be reflected back into it. Architecture that lives only in someone's head is architecture that will be violated.

---

## Before Writing Any Code

Read `ARCHITECTURE.md` in full before implementing any feature that:
- Adds a new module, service, or component
- Changes how data flows between components
- Introduces a new external dependency
- Modifies how the application is deployed or configured
- Changes an API contract or data model that other modules depend on

If `ARCHITECTURE.md` does not exist for the project yet, create it before proceeding with significant implementation work.

---

## What ARCHITECTURE.md Must Contain

A well-maintained `ARCHITECTURE.md` includes:

### System Overview
A one-paragraph description of what the system does and the core problem it solves. Written for someone with no prior context.

### Component Map
A description (and optionally a diagram) of the major components, what each one is responsible for, and how they relate to each other. Include data flow direction.

### Key Design Decisions
The most important architectural choices made and the reasoning behind them. This is the most valuable section - it prevents future developers from unknowingly reversing a decision that was made deliberately.

Example format:
> **Decision:** Detection logic uses predefined data contracts, not dynamic query generation.
> **Reason:** Ensures auditability, prevents injection risk, and guarantees deterministic behavior.
> **Consequence:** Every new data domain requires a new data contract class.

### Module Boundaries
What each module is responsible for and - equally important - what it is explicitly not responsible for. Clear boundaries prevent scope creep and entanglement.

### Technology Stack
Key technologies, frameworks, and infrastructure choices with brief rationale.

### Data Flow
How data moves through the system from input to output. Identify the key transformation and decision points.

### External Dependencies
Third-party services and APIs the system depends on, with notes on failure handling and isolation.

### Non-Goals
What this system deliberately does not do. This prevents well-intentioned additions that pull the system out of scope.

---

## How to Follow ARCHITECTURE.md

When implementing a feature, verify:
- Does the new code fit within an existing component's defined responsibility?
- Does it respect the data flow direction described in the architecture?
- Does it stay within the module boundaries - not reaching into another module's concerns?
- Is any new external dependency consistent with the stated approach to external integrations?
- Does it avoid adding capabilities that fall under Non-Goals?

If any of these cannot be satisfied, the architectural question must be discussed and resolved before implementation proceeds - not after.

---

## How to Update ARCHITECTURE.md

ARCHITECTURE.md must be updated in the same PR as the change it describes.

Update it when:
- A new module or significant new component is introduced
- Data flow changes in a way that is architecturally meaningful
- A key design decision is made, reversed, or revised
- A new external dependency is introduced
- Module boundaries are intentionally redefined
- A non-goal is promoted to an in-scope capability

Do not update it for:
- Implementation details within a component that don't change boundaries or flow
- Bug fixes that don't change the design
- Refactoring that preserves existing behavior and structure

When updating, add a brief note under the relevant section describing what changed and when. Preserve the record of past decisions - if a decision is reversed, note it and explain why rather than silently overwriting it.

---

## Architecture Review Checklist

Before merging any change that touches the system's structure, verify:

- [ ] ARCHITECTURE.md was read before implementation began
- [ ] The change respects all defined module boundaries
- [ ] The change follows the documented data flow
- [ ] Any new external dependency is consistent with the existing approach
- [ ] ARCHITECTURE.md has been updated if the design changed
- [ ] Any new key design decision is documented with its rationale
- [ ] The change does not implement a stated Non-Goal

---

## Common Mistakes

- Implementing a feature without reading ARCHITECTURE.md first - leading to design violations that are costly to reverse
- Treating ARCHITECTURE.md as a one-time artifact that never needs updating - it becomes stale and loses trust
- Writing architecture documentation at too high a level of abstraction - useful architecture docs are specific enough to constrain decisions
- Omitting the "why" behind decisions - future developers then cannot evaluate whether the decision still applies
- Using architecture diagrams without text - diagrams convey structure but not intent; both are needed
