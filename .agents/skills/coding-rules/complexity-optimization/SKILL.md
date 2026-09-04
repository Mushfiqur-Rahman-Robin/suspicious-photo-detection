---
name: complexity-optimization
description: Universal skill for time and space complexity analysis and optimization. Provides decision criteria for when to optimize, common anti-patterns, async-specific pitfalls, and a measurement-first approach applicable to any Python service or application.
license: MIT
---

# Skill: Complexity Optimization

## Purpose

Premature optimization is the root of much evil - but ignoring complexity guarantees degradation at scale. This skill establishes **when** to measure, **how** to analyze, and **how** to reduce algorithmic cost, without sacrificing readability or correctness.

The cardinal rule is: **measure before you optimize, and justify every optimization with data.**

---

## The Decision Framework: When to Optimize

Optimize when any of the following is true: a profiler shows that a specific function consumes a disproportionate share of total execution time under representative production traffic; the function's input size grows proportionally with real-world domain data such as users, records, messages, or events, making the problem unbounded; a database query or in-memory aggregation runs inside a request handler with super-linear complexity over a collection that scales with the domain; an endpoint's tail latency consistently exceeds the defined service level objective; or a background job's runtime grows faster than linearly as the data set grows.

Do not optimize when the input is provably small and bounded - for example, a fixed list of three providers, a lookup table with ten entries, or a set of status codes. Do not optimize when doing so would make the code significantly harder to read and maintain without a documented benchmark justifying the trade-off. Do not optimize before confirming the bottleneck through actual measurement.

---

## Time Complexity

### Common Anti-Patterns and Their Fixes

| Anti-Pattern | Typical Cost | Preferred Fix |
|---|---|---|
| Nested iteration over the same collection | Quadratic | Precompute a hash map or set for constant-time lookup |
| Linear scan of a list to find a unique key | Linear per call | Use a dictionary keyed by that identifier |
| Re-fetching the same database rows inside a loop | One query per iteration | Batch-fetch with a single query using an `IN` clause |
| Sorting inside a loop | Super-linear | Sort once outside the loop; slice or filter the sorted result |
| Repeated string concatenation inside a loop | Quadratic in characters | Accumulate parts in a list; join once at the end |
| Compiling a regular expression pattern inside a hot path | Compile overhead per call | Pre-compile the pattern once at module level |
| Repeated serialization of the same object | Redundant encoding work | Cache the serialized form |
| Repeated traversal of a long attribute chain inside a loop | Call overhead per step | Alias the nested attribute in a local variable before the loop |

### General Rules

Never perform operations with linear or worse complexity inside a loop unless the inner collection is provably small and fixed in size. Use hash maps and sets for membership tests and key lookups, which provide average constant-time access rather than the linear time of a list scan. Use lazy iterators and generator expressions instead of materializing entire collections when only the first result or a subset is needed. Sort once and slice or filter the result rather than re-sorting. When processing a batch of domain objects, fetch all related data in a single query rather than issuing a query for each object in a loop - this is described in detail in `.agents/skills/coding-rules/database-query-optimization/SKILL.md`.

### Async-Specific Rules

When multiple async operations are independent of one another, do not await them sequentially inside a loop. Use the language's concurrent gather mechanism to run them all at the same time and wait for the slowest, rather than waiting for each one in turn before starting the next. The difference in execution time is the sum of all durations versus the duration of the slowest single operation.

Never block an async event loop with CPU-intensive work. Computationally heavy operations - including cryptography, image or document processing, large payload serialization, and long regex execution - must be offloaded to a thread pool executor so the event loop remains free to handle other requests. Keep await expressions out of property getters, `__repr__` methods, and serialization validators, which the framework expects to be synchronous.

When fanning out many concurrent async operations, use a semaphore or equivalent concurrency limiter to prevent overwhelming downstream systems that cannot absorb an unbounded number of simultaneous requests.

---

## Space Complexity

Never load an unbounded result set entirely into memory. Use cursor-based pagination or an async streaming iterator for large database result sets or large file reads. Processing data as a stream rather than a batch means that memory usage stays constant regardless of how large the underlying data set grows.

For high-frequency, long-lived objects with a fixed set of known attributes, the language may offer a mechanism to reduce per-instance memory overhead (in Python this is `__slots__`). For large output payloads such as CSV exports or JSON dumps, use streaming serialization and write to the output incrementally rather than constructing the entire payload in memory before sending it.

Cache aggressively, but always impose explicit bounds. An unbounded in-process cache is a memory leak. Every cache must have a maximum entry count, a time-to-live, or both. Do not accumulate items in module-level collections without a corresponding eviction mechanism. Do not retain references to processed request or response objects beyond their necessary lifetime, as this prevents the garbage collector from reclaiming them.

---

## Measuring Before and After

Every optimization claim must be backed by a benchmark or profiler output. This is non-negotiable. An intuition that something is slow is not sufficient justification for a change that sacrifices readability.

The appropriate profiling tool depends on the nature of the bottleneck. For CPU time breakdown by function, use a sampling or deterministic profiler appropriate to the language and runtime. For memory usage, use a line-level memory profiler or the runtime's built-in memory tracing facilities. For async applications, enable the runtime's slow-callback detection to find operations that block the event loop. For repeatable performance regression detection, integrate microbenchmarks into the test suite using a benchmarking library.

The process is always: establish a baseline with the current code, apply the optimization, measure again, and record both numbers. If the improvement is below the noise floor of the measurement, the optimization is not justified.

---

## Complexity Classification Reference

| Notation | Name | Acceptability |
|---|---|---|
| O(1) | Constant | Always acceptable |
| O(log n) | Logarithmic | Always acceptable |
| O(n) | Linear | Usually acceptable; avoid inside loops |
| O(n log n) | Linearithmic | Acceptable for sort and merge operations |
| O(n²) | Quadratic | Requires profiler-backed justification |
| O(2ⁿ) or O(n!) | Exponential or Factorial | Never acceptable in production hot paths |

---

## Review Checklist

- [ ] No quadratic or worse operations in hot paths without profiler-backed justification.
- [ ] No linear membership tests on collections that grow with domain data - hash maps or sets used instead.
- [ ] No sequential awaiting of independent async operations - concurrent gather used instead.
- [ ] No blocking CPU-intensive work on the async event loop - offloaded to a thread pool.
- [ ] All in-process caches have an explicit maximum size and/or time-to-live.
- [ ] Large result sets use pagination or streaming rather than full in-memory loads.
- [ ] Every claimed optimization is documented with before-and-after benchmark output.
- [ ] Concurrency limits are applied when downstream systems cannot absorb unbounded fan-out.
