---
name: logging-and-tracing
description: Universal skill for structured logging and distributed tracing in Python services. Covers the stdlib logging module, structlog, and Logfire (OpenTelemetry-native). Defines log levels, mandatory context fields, sensitive data redaction, trace instrumentation, and environment configuration. Applicable to any Python web service or backend.
license: MIT
---

# Skill: Logging and Tracing

## Purpose

Logs tell you **what happened and why**. Traces tell you **where time was spent across a request lifecycle**. Neither is useful without consistent structure, correct log levels, proper context propagation, and strict redaction of sensitive data. This skill governs both.

---

## Library Stack

| Layer | Library | Role |
|---|---|---|
| Structured logging | `structlog` | Consistent, context-bound, machine-readable JSON log output |
| Standard library | `logging` | Root logger; routes third-party library logs into the structlog pipeline |
| Distributed tracing | `logfire` (Pydantic) | OpenTelemetry-native spans, automatic framework instrumentation |

### When to Use Each

Use `structlog` for all application-level log events - operational events, warnings, errors, and audit records. Use the standard library `logging` module only to configure the root logger and to bridge third-party libraries into the structlog pipeline; do not use it for application log statements. Use `logfire` for request lifecycle spans, inter-service traces, and latency tracking of external calls. Logfire provides automatic instrumentation for common frameworks and clients with zero manual code in most cases. The two libraries are complementary: structlog produces granular event logs that stream to any log aggregator, while logfire provides high-level span visibility in a dedicated trace analysis UI.

---

## Obtaining a Logger

Every project must establish a single logger factory function in its central logging module - for example, a `get_logger` function in the core or infrastructure layer. All application and infrastructure code must call this factory to obtain a logger. No code outside the central logging module should call the logging library's configuration functions or the structlog global configuration directly. This constraint ensures that the log pipeline is configured once at startup and that all log output is consistent.

---

## Log Levels

| Level | When to Use |
|---|---|
| `DEBUG` | Developer-only detail: raw request and response bodies, generated SQL queries, intermediate computation steps. Must be disabled in production by default. |
| `INFO` | Normal operational events: service started, request processed, record created, job completed. |
| `WARNING` | Recoverable abnormal conditions: a retry was triggered, a fallback was activated, a threshold is being approached, a deprecated code path was invoked. |
| `ERROR` | Failures that break a specific operation but not the entire service: an external API call failed after exhausting retries, validation rejected a request, a database write failed. Always capture exception details alongside the log entry. |
| `CRITICAL` | Service-threatening conditions: startup configuration is invalid, the connection pool is exhausted, a data integrity violation has been detected. |

The production default must be `INFO`, controlled by an environment variable. Temporarily enabling `DEBUG` in staging or development is acceptable; enabling it in production is not. When logging at `ERROR` level, always capture the full exception context alongside the message so that the stack trace appears in the log entry.

---

## Context Injection

Every log entry emitted during a request or background job must carry the identifiers that make it possible to find all related entries and correlate them with traces. These fields should be injected into the logging context at the entry point of each request - in middleware or the outermost handler - so that they are automatically present on every log statement emitted downstream without requiring the logger to be passed through every function.

The minimum required context fields are a unique request identifier that correlates all logs from a single API call or job execution, a trace identifier from the OpenTelemetry span context that connects logs to traces in the observability UI, a user or actor identifier expressed as a non-sensitive internal identifier rather than PII such as an email address, and a tenant or account identifier for multi-tenant services. A static service name field set once at startup helps filter logs by service in aggregated environments.

Using `structlog`'s context variable support - specifically the `merge_contextvars` processor - is the recommended mechanism for this in Python, as it automatically merges context bound at the request entry point into every subsequent log event without explicit passing.

---

## Sensitive Data - Never Log

The following must never appear in any log entry at any level, under any circumstances.

Passwords, secrets, API keys, cryptographic tokens, session tokens, OAuth access and refresh tokens, and any value classified as a credential must never be logged. Log only a non-sensitive derivative such as a token fingerprint, a masked identifier, or the user ID extracted from the token - never the token string itself.

Personally Identifiable Information that is not strictly required for operational diagnosis must not appear in logs. This includes full names combined with contact details, government identifiers, payment card numbers, health and medical data, and similar sensitive personal attributes.

Database connection strings that embed credentials must never appear in logs. Encryption keys and signing secrets must never appear in logs. If a third-party library emits sensitive data through the standard logging system, suppress or redact it at the handler level using a custom log filter rather than allowing it to propagate.

When in doubt, log a reference or identifier rather than the value itself.

---

## Logfire Setup and Configuration

Logfire is Pydantic's OpenTelemetry-native observability platform. It provides automatic instrumentation for FastAPI, httpx, SQLAlchemy, and LLM provider SDKs such as Anthropic and OpenAI, producing span data that appears in a hosted trace analysis UI. It also bridges the standard library logging system so that third-party library log output appears alongside application spans.

The configuration call should appear once, in the application's startup sequence, inside the central logging or application factory module. At minimum, configuration should provide the project's write token (treated as a secret), the deployment environment name, the service name, and a boolean flag controlling whether spans are actually sent to the Logfire backend. In development environments, this flag should default to disabled so that spans are emitted locally or to a console exporter without requiring an active Logfire account.

For operations that are not covered by automatic instrumentation - any significant operation lasting more than roughly 50 milliseconds - wrap the operation in a manual span using `logfire.span()`. Provide meaningful attribute names and values that would help a developer understand the context of the span when investigating a latency issue.

If using a self-hosted OpenTelemetry collector such as Jaeger or Grafana Tempo instead of the Logfire cloud backend, configure the OTLP exporter endpoint through the environment and disable the cloud backend send flag.

---

## Environment Variable Configuration

All logging and tracing configuration must be read from environment variables through the project's central settings module. None of these values may be hardcoded in source files. The following variables are standard across any project adopting this skill.

The application log level controls the minimum severity of events that appear in the log stream. The Logfire write token grants write access to the observability backend and must be treated as a secret - stored in a secrets manager for production deployments, never committed to version control. The flag controlling whether spans are sent to the Logfire cloud backend should default to disabled in development. An optional OTLP exporter endpoint variable allows directing spans to a self-hosted collector. Service name and version variables are injected into every span as resource attributes and should be set from the deployment configuration.

Each of these variables must be documented in the project's environment variable example file with a description, accepted values, and a note indicating whether a given variable is required in production.

---

## Structured Log Event Naming

Log event names - the primary identifier passed as the first argument to each log call - must use `snake_case`, describe the event in past-tense or noun-phrase form, and be specific enough to be useful as a search term in a log aggregator. Examples of good event names: `user_registered`, `payment_failed`, `cache_miss`, `report_generated`, `rate_limit_exceeded`. Examples of unacceptable event names: `error`, `event`, `message`, `log`. A generic event name makes it impossible to filter for a specific condition in production and indicates that the developer did not think carefully about what the log entry represents.

---

## Audit Logging

For systems that require a tamper-evident audit trail - such as those handling financial transactions, permission changes, data deletions, or access to sensitive records - audit records must be kept separate from operational logs. They must be written to a dedicated, append-only sink such as a separate log file, a dedicated database table, or an immutable log stream. They must follow a fixed schema that includes at minimum the timestamp, the actor identifier, the action performed, the type and identifier of the affected resource, the outcome, and any relevant metadata. Audit records must never be filtered out by the application log level setting; they are always written regardless of whether the general log level is set to `WARNING` or `ERROR`. For high-assurance systems, consider chaining records using a cryptographic MAC so that any tampering with the log file can be detected.

---

## Review Checklist

- [ ] Logger obtained via the project's central logger factory - not directly from the logging library.
- [ ] Correct log level chosen for each statement - not everything at `INFO`.
- [ ] Request identifier, trace identifier, and relevant actor or tenant identifiers are bound to the logging context at the request entry point.
- [ ] No secrets, tokens, passwords, PII, or connection strings appear in any log statement.
- [ ] Operations requiring an audit trail use the project's audit record emitter, not a plain log statement.
- [ ] Logfire spans wrap significant non-auto-instrumented operations.
- [ ] Logfire token and log level are documented in the environment variable example file.
- [ ] Logfire cloud sending is disabled by default in development.
- [ ] No debug output statements (`print`, `pprint`, or equivalent) in committed code.
- [ ] Third-party library log noise is suppressed or filtered at the handler level if it contains sensitive data.
