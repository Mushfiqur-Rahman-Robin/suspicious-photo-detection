---
name: performance-and-scaling
description: Universal skill for performance, concurrency, and scaling. Covers background jobs, caching, rate limiting, and resource management.
license: MIT
---

# Skill: Performance and Scaling

## Purpose
Systems that work perfectly with 10 users often fail catastrophically with 10,000. These rules ensure that the application handles concurrency, limits resource footprint, and defers slow work appropriately.

---

## Background Processing

**Never block an API response on slow work.**
- Sending emails, making LLM calls, generating PDFs, or executing heavy aggregations should not happen synchronously in an API request (unless the user explicitly must wait for the data immediately).
- Use a background job queue (e.g., Celery, Redis Queue, Kafka).
- The API returns `202 Accepted` with a Job ID, and the client polls for completion (or connects via WebSockets).

**Rules for Background Jobs:**
- **Idempotency:** Jobs must be safe to retry. If a job fails halfway, retrying it must not cause duplicate emails, double charges, or corrupt data.
- **Timeouts:** Every job must have a hard timeout.
- **Dead Letter Queues:** Jobs that fail multiple times should be moved to a dead letter queue for manual inspection.

---

## Caching

- Use caching to protect the database from redundant, expensive queries.
- **Cache Invalidation is hard:** Use clear expiration TTLs (Time to Live). If absolute consistency is required, do not cache, or use a strict write-through cache.
- Do not cache user-specific data globally. Always namespace cache keys by `tenant_id` or `user_id` (e.g., `tenant:123:dashboard_stats`).

---

## Concurrency & Locking

- When modifying shared resources (e.g., updating a balance or consuming a limited quota), account for race conditions.
- Uses database transactions with appropriate isolation levels or distributed locks (e.g., Redis `SETNX`) to prevent concurrent modifications from overwriting each other.
- External API calls made by multiple workers should use connection pooling.

---

## Resource Protection

**Rate Limiting & Throttling:**
- All public or tenant-facing endpoints must have rate limits based on IP or Authentication Token.
- Distinguish between Burst limits and Sustained limits.

**Pagination:**
- Endpoints returning lists must be paginated. The database will crash if millions of rows are returned in one JSON payload.
- Use cursor-based pagination for massive datasets rather than offset-based pagination (which degrades as offset grows).

**Memory Footprint:**
- Process large files via streams/chunks (e.g., streaming CSV parsing). Do not read a 1GB file entirely into RAM.
