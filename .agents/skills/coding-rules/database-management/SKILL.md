---
name: database-management
description: Universal skill for database interactions and migrations. Covers schema evolution, backward compatibility (expand/contract), ORM pitfalls, and connection management.
license: MIT
---

# Skill: Database Management

## Purpose
The database is the hardest part of the system to scale and the hardest to roll back. Code can be reverted in seconds; a destructive database migration cannot. These rules ensure schema changes are safe, queries are performant, and data integrity is maintained.

---

## Schema Evolution & Migrations

**Zero-downtime migrations are required.** Do not write migrations that lock tables for a long time or break the currently running version of the application.

**The Expand and Contract Pattern:**
When renaming a column, changing a type, or moving data, use the expand/contract pattern across multiple deployments:
1. **Expand:** Add the new column/table. Update the application to write to both the old and new locations, but read from the old.
2. **Migrate:** Run a background script to backfill data from the old column to the new column.
3. **Transition:** Update the application to read from the new column.
4. **Contract:** Drop the old column in a subsequent release.

**Migration Rules:**
- Migrations must be forward-only in production. Do not use `--downgrade` on production data unless explicitly designed for it. Fix forward instead.
- Do not add `NOT NULL` columns without a default value to existing tables with data.
- Avoid building indexes simultaneously with data migrations in massive tables - build indexes `CONCURRENTLY` if supported (e.g., PostgreSQL).
- Never rename a table in a single deployment step.

---

## ORM Pitfalls

Object-Relational Mappers (ORMs) hide SQL, which is convenient but dangerous.

**The N+1 Query Problem:**
Never query related entities inside a loop.
*Bad:* Fetch 100 invoices, then loop through them and fetch the user for each (101 queries).
*Good:* Fetch 100 invoices and eager-load the users in the same query (1 or 2 queries).

**Data Fetching:**
- Do not `SELECT *` (or fetch the full model) if you only need one or two columns.
- Do not load thousands of records into memory just to count them - use SQL `COUNT()`.
- Do not execute database queries inside property getters or serialization logic.

---

## Transactions

- Wrap operations that modify multiple tables in a single transaction. If one fails, they all roll back.
- Keep transactions short. Do not make network calls (HTTP requests, LLM calls) inside an open database transaction. If the network is slow, your database connection pool will exhaust.
- Read-only operations generally do not need explicit transaction blocks unless you need a consistent snapshot across multiple queries.

---

## Indexing

- Index foreign keys, columns used in `WHERE` clauses frequently, and columns used for `ORDER BY`.
- Do not over-index. Every index slows down `INSERT`, `UPDATE`, and `DELETE` operations.
- Ensure composite indexes match the order of the query filter. An index on `(tenant_id, status)` helps queries filtering by `tenant_id` and queries filtering by both, but does not help queries filtering *only* by `status`.

---

## Connection Management

- Always use a connection pool in production.
- Configure appropriate timeouts (`statement_timeout`) at the database level so a bad query doesn't run forever and consume resources.

---

## Review Checklist for Database Changes

Whenever reviewing a PR with a migration or database query:
- [ ] Will this migration lock the table? (e.g., adding a constraint to a huge table)
- [ ] Is this migration backward-compatible with the currently running application?
- [ ] Does this query avoid the N+1 problem through eager loading / joins?
- [ ] Are network calls made outside of open transactions?
- [ ] Are the necessary indexes present for this query to scale?
