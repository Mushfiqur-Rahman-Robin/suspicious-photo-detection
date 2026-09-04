---
name: observability
description: Universal skill for system observability. Distinguishes between logs, metrics, and traces, and defines standards for monitoring and alerting.
license: MIT
---

# Skill: Observability

## Purpose
Error handling focuses on the code level; observability focuses on the fleet level. A system is observable if you can answer "why is this broken?" and "is this slow?" without having to deploy new logging code.

---

## The Three Pillars

### 1. Logs (Events)
Logs tell you **what happened and why**.
- Covered in `.agents/skills/coding-rules/error-handling/SKILL.md` (structured logging, proper log levels).
- A log is useless without context. Always inject request IDs and, where applicable, tenant IDs or user IDs into the log context.

### 2. Metrics (Aggregations)
Metrics tell you **how the system is doing as a whole**.
- Do not use logs for counting occurrences - use metrics.
- Track the RED metrics for every service and endpoint:
  - **Rate:** Requests per second.
  - **Errors:** Error rate (HTTP 5xx).
  - **Duration:** Request latency (e.g., P50, P90, P99).
- Track business metrics as well (e.g., "AI insights generated", "signals processed").

### 3. Traces (Lifecycles)
Traces tell you **where the time went across services**.
- Use Distributed Tracing (e.g., OpenTelemetry).
- Every incoming HTTP request or background job must generate a `trace_id`.
- The `trace_id` must be passed downstream to any other services, database queries, and external API calls (e.g., LLM calls).
- The `trace_id` must be injected into all log entries for that request.

---

## Alerting & SLOs

- **Alert on symptoms, not causes.** Alert when the error rate spikes or latency goes beyond the SLA. Do not alert because CPU hit 80% if response times are still fine.
- **Service Level Objectives (SLOs):** Define what "healthy" means. (e.g., "99.9% of API requests return < 200ms").
- If an alert fires and requires no human action, it is not an alert - it is noise. Convert it to a metric or dashboard panel.

---

## Implementation Rules
- Add a timing decorator or middleware to all API endpoints and background tasks to emit duration metrics.
- Expose a `/health` and `/metrics` endpoint.
- Do not put high-cardinality data (like `user_id` or `email`) into a Metric tag/label, as it will break the time-series database. High-cardinality data goes into Logs and Traces.
