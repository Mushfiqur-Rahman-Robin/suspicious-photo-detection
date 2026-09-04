---
name: error-handling
description: Universal skill for error handling, structured logging, and observability. Covers exception design, error propagation, logging standards, and graceful degradation.
license: MIT
---

# Skill: Error Handling

## Purpose
Errors are not edge cases - they are a fundamental part of a system's behavior. How a system fails is as important as how it succeeds. Good error handling means errors are caught intentionally, logged with sufficient context, communicated safely to callers, and escalated or degraded gracefully.

---

## Core Principles

**Errors are expected.** Design error handling proactively - do not add it as an afterthought. Every function that calls external code (database, API, file system, LLM) can fail.

**Fail clearly or degrade gracefully.** A system should either fail with a clear, diagnosable error or degrade to a reduced-functionality state. Silent partial failure is the most dangerous outcome.

**Catch exceptions intentionally.** Catch the specific exception you expect and know how to handle. Catching all exceptions at every level hides bugs. Let unexpected exceptions propagate.

**Never swallow exceptions silently.** If an exception is caught and not re-raised, it must be logged. An exception that disappears leaves no trace for diagnosis.

**Separate operational errors from programming errors.** An operational error (database unreachable, API timeout) is expected and should be handled gracefully. A programming error (null reference, type mismatch) is a bug and should surface - not be caught and hidden.

---

## Exception Design

Use custom exception classes to communicate intent and domain context.

Guidelines for custom exceptions:
- Name exceptions after what went wrong, not where it happened: `PaymentNotFound` not `DatabaseError`
- Group related exceptions under a base exception class for the module
- Carry enough context in the exception to diagnose the problem: include relevant IDs, states, and descriptions
- Do not use exceptions for normal control flow (e.g., using an exception to signal "not found" when that is an expected result of a lookup)

---

## Error Propagation

At each layer of the application, decide: handle, wrap, or propagate.

- **Handle** - if this layer can fully resolve the error and continue correctly
- **Wrap** - if this layer has context to add (e.g., which entity was involved), catch and re-raise as a richer exception
- **Propagate** - if this layer cannot meaningfully handle the error, let it propagate to the layer that can

At the outermost layer (API handler, task runner, CLI), catch all errors and produce a safe, structured response. Internal error details must never reach external consumers.

---

## Structured Logging

Use structured logging - not plain string concatenation. Structured logs are machine-parseable and searchable, making diagnostics orders of magnitude faster.

**Every log entry should include:**
- Timestamp (UTC)
- Log level
- Module or component name
- A concise message describing the event
- Relevant structured fields (entity IDs, operation names, durations, status codes)

**Log levels - use them consistently:**
| Level | Use |
|---|---|
| `DEBUG` | Detailed diagnostic information for development; never in production by default |
| `INFO` | Normal, significant application events (request received, task started, operation completed) |
| `WARNING` | Something unexpected but recoverable; the system continues operating |
| `ERROR` | An operation failed; investigation is warranted |
| `CRITICAL` | A serious failure; immediate attention required |

**Rules:**
- Use `ERROR` when an operation fails and the caller or user is affected
- Use `WARNING` for degraded modes, retries, and non-fatal anomalies
- Do not log at `INFO` level for every function call - logs should be meaningful, not noisy
- Never use `print` in production code - use the logging framework
- Never log secret values, credentials, PII, or API keys - log IDs and references instead

---

## What to Log at Error Level

When logging an error, include:
- What operation was being performed
- Which entity or resource was involved (by ID - not raw data)
- What the error was (exception type and message, sanitized)
- Any contextual state that would help diagnose the issue

What not to include:
- Stack traces in consumer-facing responses (only in server-side logs)
- Sensitive data fields, even for debugging
- Internal service names or infrastructure details that could aid an attacker

---

## API Error Responses

At the API boundary, all errors must be mapped to structured, safe responses:
- Use the appropriate HTTP status code (see `.agents/skills/coding-rules/api-design/SKILL.md`)
- Return a machine-readable error code constant and a human-safe message
- Do not include stack traces, SQL error text, or internal service names in the response body
- Log the full internal error server-side for diagnosis

---

## Graceful Degradation

When a non-critical external dependency fails, the system should continue operating at reduced capability rather than failing entirely.

Design degradation policies explicitly:
- Define what the fallback behavior is for each external dependency failure
- Implement and test the fallback path - not just the happy path
- Surface the degraded state visibly (log it, optionally signal it in the response)
- Apply timeouts and retries with backoff - never block indefinitely on an external call
- Apply circuit breakers for high-volume external calls to prevent cascading failure

---

## Common Mistakes

- Catching `Exception` or the base exception class everywhere - hides real bugs
- Logging an error and then swallowing it - introduces confusion about whether the error was handled
- Relying on error responses to show internal messages to users
- Using magic return values (`None`, `-1`, `""`) to signal errors instead of raising exceptions - callers miss them
- No timeout configured on external calls - a slow dependency hangs the entire request
- Retrying without backoff or a cap - amplifies load on a struggling dependency
