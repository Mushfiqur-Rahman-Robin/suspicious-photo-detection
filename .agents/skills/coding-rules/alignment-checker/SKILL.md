---
name: alignment-checker
description: Universal alignment skill. Verifies that implemented features match agreed specifications, design decisions, and documented requirements.
license: MIT
---

# Skill: Alignment Checker

## Purpose
Verify that what was built matches what was agreed. Requirements drift is one of the most common sources of technical debt. The alignment checker ensures that specifications, design decisions, and client agreements remain the source of truth - not what felt easiest to implement.

---

## When to Use

- Before merging a feature to the main branch
- After any significant refactoring
- When a change touches a module that has documented design constraints
- Whenever there is ambiguity about whether an implementation matches the intent

---

## How to Use

1. Identify the specification or design document that governs the feature being reviewed
2. Work through the checklist below
3. Note any gaps, deviations, or partial implementations
4. Produce a clear verdict - aligned, partially aligned, or not aligned

---

## Checklist

### Requirements Coverage
- Does the implementation address all the stated requirements for this feature?
- Are there any requirements that are partially implemented or skipped?
- Is there any functionality implemented that was not requested (scope creep)?

### Design Adherence
- Does the implementation follow the agreed architectural patterns for the project?
- Are the module boundaries, data flow, and component responsibilities consistent with the design?
- Does it introduce any new dependencies or patterns that weren't part of the design?

### Data Contracts
- Do the input and output shapes match what was specified?
- Are all required fields present and correctly typed?
- Are optional fields handled correctly when absent?

### Behavior
- Does the system behave as specified under normal conditions?
- Does it behave correctly at edge cases and boundaries defined in the spec?
- Are error states handled in the way the spec prescribes?

### Non-Functional Requirements
- Are performance, scalability, or latency expectations addressed if specified?
- Are security requirements (authentication, authorization, isolation) implemented correctly?
- Are observability requirements (logging, audit trails) satisfied?

### Constraints and Non-Goals
- Are explicitly stated constraints respected in the implementation?
- Are non-goals (features intentionally excluded) absent from the implementation?

### Documentation
- Is the implemented behavior accurately documented in SPEC.md, README, or equivalent?
- Are any deviations from the original spec noted and explained?

---

## Verdict

- ✅ **Aligned** - implementation matches the specification in all relevant areas
- ⚠️ **Partially aligned** - minor gaps exist; documented and tracked for resolution
- ❌ **Not aligned** - one or more significant deviations from the specification; must be resolved before merge
