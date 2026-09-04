---
name: database-query-optimization
description: Universal skill for writing and reviewing efficient database queries. Covers index strategy, query plan analysis, the N+1 problem, batch operations, aggregations, pagination, and ORM best practices. Applicable to any SQL-backed service using an ORM or raw SQL.
license: MIT
---

# Skill: Database Query Optimization

## Purpose

The database is the most common performance bottleneck and the hardest layer to scale horizontally. Every query must be intentional: fetching only the data it needs, using available indexes, and never executing inside a loop. Slow queries degrade every user of a shared database - not just the one triggering them.

This skill complements `.agents/skills/coding-rules/database-management/SKILL.md`, which covers schema migrations and connection management, with query-level optimization rules.

---

## Query Design Principles

Fetch only the columns that are actually needed for the operation. Fetching a full record when only two fields are used wastes database I/O, network bandwidth, serialization time, and in-process memory. Filter data at the database layer using query conditions, grouping, ordering, and aggregation - never by loading a large collection into application memory and filtering it with a loop or list comprehension. Identify the minimum number of round-trips required for each use case and enforce it with integration tests. Analyse the query execution plan before merging any new query on a table expected to hold more than a few thousand rows, and do this before the code reaches production, not after.

---

## Index Strategy

### When to Add an Index

Add an index on every foreign key column. Add an index on every column used in filter conditions on frequently called endpoints. Add an index on every column used to order the results of paginated queries. Add a composite index on pairs of columns that are frequently filtered together. Add an index on columns used in join conditions when those columns are not already foreign keys.

### When Not to Add an Index

Do not add an index on a column with very low cardinality - for example, a boolean flag with only two possible values - when that column is queried in isolation, because the database's query planner will often prefer a sequential scan for low-cardinality columns. Do not add indexes on columns that are never used in filter, join, or order conditions. Do not add indexes on small tables where sequential scans are already fast. Every index has a write cost: each insert, update, and delete must update every index on that table. Over-indexing degrades write throughput without improving read performance.

### Composite Index Column Order

The column order in a composite index determines which query patterns benefit from it. A composite index on columns A and B will accelerate queries filtering by A alone, and queries filtering by both A and B. It will not accelerate queries filtering by B alone. Match the composite index column order to the leftmost prefix of the most common filter pattern in the queries that are supposed to use it.

### Naming Convention

Use a predictable index naming convention so that any developer reading a migration can immediately understand what an index covers. A common pattern is a prefix (`ix` for regular indexes, `uq` for unique constraints) followed by the table name and column name or names, all separated by underscores.

---

## The N+1 Problem

The N+1 problem is the single most common and damaging database performance bug. It occurs when code fetches a collection of records and then issues one additional database query per record to fetch related data, resulting in one query for the collection plus one query per row rather than one or two queries total.

The fix is always to batch: identify all the related identifiers from the first query result, then fetch all the related records in a single query using an `IN` condition. The result is a constant number of queries regardless of collection size, rather than a count that scales linearly with the number of rows.

When using an ORM, the equivalent mechanism is eager loading. ORMs typically provide multiple eager loading strategies for different relationship patterns. A separate `IN`-clause query (called `selectinload` in SQLAlchemy) is generally preferred for loading a collection of child records because it avoids the row multiplication that a SQL `JOIN` produces when a parent has multiple children. A `JOIN`-based loader (called `joinedload` in SQLAlchemy) is preferable when loading a single related object - for example, the user associated with an order - where the join does not produce duplicate rows. Never load related records inside a loop, and never rely on ORM lazy loading in a web request handler, because lazy loading issues one query per accessed relationship and is invisible in the source code.

---

## Pagination

Never return an unbounded result set from a list endpoint or a background job that processes a collection. Always apply a row limit. There are two primary pagination strategies with different trade-offs.

Cursor-based pagination fetches the next page by filtering for records whose identifier or timestamp is greater than the last one seen in the previous page. This approach is stable under concurrent inserts - records do not shift between pages while the client is paginating - and it performs consistently regardless of how far into the result set the client has advanced. It is the preferred approach for tables that grow continuously.

Offset-based pagination uses a skip-and-limit mechanism that discards a fixed number of rows before returning the next page. It is simpler to implement and works well for small, relatively static tables. However, its performance degrades as the offset grows, because the database must scan and discard all the skipped rows. For tables that are expected to grow to hundreds of thousands of rows or more, cursor-based pagination is strongly preferred.

---

## Aggregations

Use the database's native aggregate functions rather than loading records into application memory to perform the aggregation in code. Counting, summing, averaging, and finding minimum or maximum values are operations the database performs efficiently using index statistics and optimised execution paths. Loading thousands of records into a Python list to call `len()` on it, or to sum a column with a list comprehension, produces unnecessary data transfer, deserialization overhead, and memory pressure.

---

## Batch Writes

Group multiple insert or update operations into a single database statement wherever possible. Most databases and ORMs support a bulk insert operation that sends multiple rows in one round-trip. Per-row inserts inside a loop - each with its own commit - multiply the round-trip count and the transaction overhead by the number of rows being written. For bulk updates, a single `UPDATE ... WHERE id IN (...)` statement is far more efficient than updating one row at a time.

---

## Column Selection

Never fetch more columns than are needed for the operation. In ORM terms, this means using column-level queries that return only the specified fields rather than loading full model instances. In raw SQL terms, this means listing the required columns explicitly rather than using `SELECT *`. The two most common violations to watch for are: fetching full records when only one column is needed (for example, loading entire user records to display a list of usernames), and loading records to count them (for example, fetching all rows to call `len()`) rather than using the database's `COUNT` function.

---

## Raw SQL vs ORM

Prefer the ORM for standard create, read, update, and delete operations. It provides type safety, composable query expressions, and migration compatibility. Use the ORM's query builder (the Core layer in SQLAlchemy) for complex queries that the ORM's relationship layer cannot express cleanly. Use raw SQL only as a last resort - for example, when using a database-specific feature such as full-text search, lateral joins, or window functions - and document the reason clearly with a comment. Never interpolate user input directly into a raw SQL string; always use the driver's bound parameter mechanism, which separates the query structure from the data values and prevents SQL injection.

---

## Transactions

Keep database transactions short. Opening a transaction and then making a network call - for example, an HTTP request to a third-party API or a call to a language model - while holding the transaction open exhausts database connection pool slots and holds row locks unnecessarily. Complete the network call first, then open the transaction and perform the database writes. Wrap all database mutations that span multiple tables in a single transaction so that a failure in one step causes all the steps in that unit of work to roll back atomically. Read-only operations do not require explicit transaction blocks unless a consistent snapshot across multiple queries is needed.

---

## Query Plan Analysis

Before merging any new query on a table expected to hold more than a few thousand rows, generate and review the query execution plan. Every major database provides a command for this - `EXPLAIN ANALYZE` in PostgreSQL, `EXPLAIN FORMAT=JSON` in MySQL, and `EXPLAIN QUERY PLAN` in SQLite. The execution plan shows which access methods the database has chosen: whether it will use an index or perform a full sequential scan, how many rows it estimates it will process, and where the most time will be spent.

The most important red flag is a sequential scan on a large table, which indicates a missing index. When a sequential scan is found, add the appropriate index in a migration, then regenerate the execution plan to confirm that the planner now uses the index. In PostgreSQL, large production indexes should be built using the `CONCURRENTLY` option to avoid locking the table during index construction. Record the before and after query plan snippets in the pull request description so that reviewers can confirm the improvement.

---

## Database-Specific Notes

PostgreSQL supports building indexes without locking the table through its `CONCURRENTLY` option. It also supports a `RETURNING` clause on insert and update statements, which eliminates the need for a second `SELECT` to retrieve the result. Partial indexes allow creating an index on a subset of rows - for example, only the pending records in a status column - which can dramatically reduce index size and write overhead.

MySQL and MariaDB require the `utf8mb4` character set for full Unicode support - earlier character sets do not support characters outside the Basic Multilingual Plane. Use a high-precision timestamp type for any column that requires sub-second accuracy.

SQLite is suitable for development environments and single-process deployments. For production environments where multiple processes access the database concurrently, enable write-ahead logging mode at connection time. Foreign key constraint enforcement is disabled by default in SQLite and must be explicitly enabled at each connection.

---

## Review Checklist

- [ ] No queries inside loops - the N+1 problem is eliminated, with all related data fetched via batching or eager loading.
- [ ] No fetching of full records or all columns when only a subset of fields is needed.
- [ ] Aggregations performed in the database using aggregate functions, not loaded into memory.
- [ ] All list-returning endpoints and collection processors apply an explicit row limit and use pagination.
- [ ] New filter and sort columns on large tables have corresponding index migrations.
- [ ] Query execution plan reviewed; no full sequential scans on large tables.
- [ ] Bulk operations use batch insert or update statements, not per-row commits.
- [ ] No raw SQL string interpolation - bound parameters used throughout.
- [ ] Database transactions do not span network I/O such as HTTP requests or external API calls.
- [ ] ORM eager loading strategies chosen appropriately for the relationship type.
