---
name: llm-development
description: Universal skill for building LLM applications in a model-agnostic way so providers (OpenAI, Gemini, Anthropic) can be swapped easily. Covers reasoning levels, guardrails, prefix and semantic caching, prompt versioning, and observability. Mandatory reading for any LLM project.
license: MIT
---

# Skill: LLM Development

## Purpose
Every LLM project in this repository must be built to outlive any single model or provider. Model cards, pricing, and capabilities change faster than application code, so all LLM integration must be **model-agnostic**: an abstraction layer that lets the team switch between OpenAI, Google Gemini, and Anthropic (or self-hosted backends) by changing configuration - not by rewriting feature code. This rule defines the mandatory patterns: provider abstraction, reasoning levels, guardrails, prefix caching, semantic caching, prompt versioning, and observability. It also requires the KPIs from `.agents/skills/coding-rules/llm-performance-kpis/SKILL.md` to be present in every request path.

---

## Mandatory Documents

- `.agents/skills/coding-rules/llm-performance-kpis/SKILL.md` - every LLM call path MUST emit TTFT, tokens/second, latency, throughput, and retrieval quality metrics.
- `.agents/skills/coding-rules/design-patterns/SKILL.md` - use when structuring the provider abstraction and cache layers.
- `.agents/skills/coding-rules/logging-and-tracing/SKILL.md` and `.agents/skills/coding-rules/error-handling/SKILL.md` - apply to all LLM calls.

---

## Model-Agnostic Architecture

### Provider Abstraction (Required)

All LLM integration goes through one internal interface. Feature code must never import a provider SDK directly.

Example module layout (language-agnostic; adapt to your language's module conventions):

```
app/llm/
  client/        # internal interface: chat(), stream(), embed(), rerank()
  provider/      # one adapter per provider (openai, google, anthropic, self_hosted)
  routing/       # picks provider + model from config per request
  config/        # model registry + reasoning levels + fallbacks
```

Rules:
- **One interface, many adapters.** Expose `chat()`, `stream()`, `embed()`, `rerank()` behind a single internal contract. Each provider has its own adapter that maps the provider SDK onto that contract.
- **Models are configuration, not code.** All model names, base URLs, API keys, and capabilities live in config (e.g. a model registry / config file). Switching models (e.g. from one provider's flagship to another provider's flagship) is a config change, never a code change.
- **Normalize capabilities.** The registry records per model: whether it supports streaming, reasoning, tool calling, images, and caching. Feature code asks "can this model X?" - it never assumes.
- **Normalize the response.** Every adapter returns the same shape: `content`, `usage` (input/output tokens), `cached_tokens`, `finish_reason`, `model`, and per-KPI timing.
- **Errors are mapped.** Provider SDK errors (rate limit, timeout, 4xx/5xx) are translated to the project's own error types before reaching feature code.
- **Self-hosted is a provider.** vLLM/SGLang/TGI endpoints speak OpenAI-compatible APIs - implement them as just another adapter.

### Fallbacks and Failover

- Configure a **fallback chain** per capability: primary provider, then fallback provider, then a degraded path (e.g. serve a cached answer or a graceful "unavailable" message).
- Set per-provider timeouts and a small bounded retry budget with exponential backoff + jitter. Do not retry on 4xx (except 429 after respecting `Retry-After`).
- Fail open for cache lookups, fail closed only for safety-critical guardrails (see below).

---

## Reasoning Levels (high / medium / low / default)

All reasoning-capable models accept a "reasoning effort" control (e.g. OpenAI's `reasoning.effort`: `low`, `medium`, `high`, `xhigh`). This project standardizes on four levels, exposed in the internal interface and config:

| Level | Meaning | When to use |
|-------|---------|-------------|
| `high` | Maximum reasoning: deep planning, complex debugging, long-horizon work | High-value tasks where quality beats latency and cost |
| `medium` | Balanced quality/latency/cost. Default for reasoning models | General agentic work, research, complex Q&A |
| `low` | Fast, light reasoning: tool use, routing, drafting, chat | Latency- and cost-sensitive tasks that still need some planning |
| `default` | No reasoning effort is requested at all | Models WITHOUT reasoning ability (standard instruct/chat models) |

Implementation rules:
- **`default` must not break non-reasoning models.** The adapter sends the reasoning parameter ONLY when the configured model supports it (looked up in the model registry). A model with no reasoning support receives no reasoning field - never send it and catch an API error.
- **Map levels to provider values in the adapter.** `high`/`medium`/`low` map to each provider's native vocabulary; the adapter owns the translation, feature code only uses the four standard levels.
- **Reasoning tokens are usage tokens.** Count and log reasoning/thinking tokens separately in the usage object so cost and latency are attributable.
- **Caching interacts with reasoning.** Some providers' prefix caches behave differently for reasoning models - keep reasoning on the same model for cache stability; do not route reasoning tasks round-robin across providers unless the cache key/namespace accounts for it.

---

## Guardrails (NeMo Guardrails)

Use **NVIDIA NeMo Guardrails** (`nemoguardrails`, PyPI) as the guardrails layer for all LLM applications. It is a programmable open-source toolkit that sits between application code and the LLM and supports five rail types:

1. **Input rails** - validate/sanitize user input before it reaches the model.
2. **Retrieval rails** - reject/alter retrieved chunks before they enter the prompt (RAG).
3. **Dialog rails** - steer the conversation along allowed flows (Colang).
4. **Execution rails** - validate tool/action inputs and outputs.
5. **Output rails** - validate/sanitize model output before it reaches the user.

Rules:
- **Guardrails are mandatory** on any endpoint that accepts user text or exposes model output. At minimum: input rails (jailbreak/prompt-injection detection) and output rails (content safety, PII).
- **Use the built-in rails first**: self-check moderation, jailbreak/injection detection, PII detection, fact-checking for RAG, hallucination detection.
- **Model-agnostic placement:** NeMo Guardrails supports OpenAI, Azure OpenAI, Anthropic, Cohere, Google Vertex AI, and self-hosted backends. Configure it once in front of the internal `chat()`/`stream()` interface so every provider is covered.
- **Fail closed on safety.** If a guardrail cannot determine a verdict for a safety-critical check, reject/block rather than pass through. For non-safety checks, fail open (allow) to avoid availability loss.
- **Guardrail decisions must be logged** (rejected, altered, passed) as observability events and counted as metrics.

---

## Prompt Caching (Prefix Caching)

Provider prefix caching reuses the model's KV computation for an exact repeated prompt prefix, cutting input cost and time-to-first-token dramatically. **Whenever the active provider offers prefix caching, it MUST be enabled and exploited.**

Provider facts (verify current numbers in provider docs before shipping):
- **Anthropic:** explicit opt-in via `cache_control: { type: "ephemeral" }` on content blocks (up to 4 breakpoints). Cache reads ≈ 10% of input price; writes cost a surcharge. 5-minute default TTL, 1-hour option.
- **OpenAI:** automatic for prompts ≥ 1,024 tokens; cached input billed at a large discount. No code needed, but ordering/stability of the prefix decides hit rate. `cached_tokens` in usage confirms hits.
- **Google Gemini:** implicit caching on newer models; explicit "context caching" API (`cached_content` / `CachedContent`) with a TTL you control, billed storage per hour - best for very large contexts reused over hours.

Rules:
- **Stable content first, volatile content last.** Order every prompt: system prompt → tool definitions → instructions/examples → stable shared context → retrieved context → chat history → current user message. Any change before the cached boundary (a timestamp, request ID, per-user value) invalidates the cache from that point on.
- **Keep the prompt prefix byte-identical.** No injected dates, random IDs, or reordered tool lists in the cached region. Everything dynamic goes to the END of the prompt.
- **Verify hits.** Read the usage field (`cached_tokens` on OpenAI, `cache_read_input_tokens` on Anthropic, `cached_content_token_count` on Gemini) and log a cache-hit metric. If expected hits are 0, the prefix is drifting - fix the ordering.
- **Set breakpoints deliberately (Anthropic).** Place `cache_control` at layer boundaries (system, tools, history) so the most stable, reused prefix is cached and per-request content sits after the last breakpoint.
- **Explicit caches for large stable context (Gemini).** Create `CachedContent` for big shared corpora and reference the cache ID; set a TTL matched to reuse frequency.
- **Prefix caching and semantic caching are complementary.** Prefix caching makes the calls you keep cheaper; semantic caching eliminates repeat calls entirely. Use both.

---

## Semantic Caching (Redis Stack)

Use **Redis Stack** with RedisVL's `SemanticCache` for semantic caching of LLM responses. Semantic caching embeds each incoming prompt, searches for a semantically similar cached prompt, and returns the cached response without calling the model.

### Architecture
Implement a **layered cache**:
1. **Tier 1 - exact-match cache** (Redis, content-hash key). Zero false positives, single-digit ms. Misses fall through.
2. **Tier 2 - semantic cache** (Redis Stack vector search, cosine similarity). Catches paraphrased questions. 
3. **Tier 3 - the LLM** (after prefix caching discounts). On completion, write the response back to Tier 1 and Tier 2.

### Configuration
- **Similarity threshold:** start conservative (cosine ≈ 0.9-0.95); lower only after an eval loop shows false positives are within tolerance. Raise for high-stakes domains. Threshold is per-feature, not global.
- **TTL by data volatility:** stable knowledge 24h-90d; prices/inventory/status 5min-1h or excluded from caching entirely. Per-feature TTLs, not one global value.
- **Partition by tenant and feature.** Include `tenant_id` and `feature_id` in both the payload AND the search filter - forgetting the read-time filter is the classic cross-tenant leak bug.
- **Only cache safe responses.** Cache only complete, reusable responses: skip personalized answers, time-sensitive data (prices, "what happened today"), tool-driven/stateful turns, and responses that finished mid-generation (e.g. hit `max_tokens`, half-finished text). In short, only cache responses whose `finish_reason` indicates a naturally complete answer - map each provider's native finish reason to a normalized "complete" flag in the adapter rather than comparing raw strings.
- **Strip volatile inputs before embedding.** Remove timestamps, session IDs, and user-specific fields from the prompt used for the similarity key, or no two queries will ever match.
- **Cache invalidation is required - not optional:**
  - **TTL expiry** for all entries (tiered by feature volatility).
  - **Event-driven invalidation:** when source data changes, emit an event and delete affected cache entries (Redis `DEL` for exact keys + filtered delete over the semantic index) immediately - do not wait for TTL.
  - **Version-based invalidation:** include a `cache_version` in the Redis key prefix and vector payload. Bump it on any model upgrade, prompt change, or embedding-model change so old entries become unreachable instead of serving stale answers.
  - **Embedding-model changes invalidate thresholds too:** a new embedder shifts the similarity distribution - re-tune thresholds and re-evaluate before trusting the cache.
- **Fail open:** if Redis or the cache lookup fails or exceeds a hard timeout (~200 ms), treat as a cache miss and call the LLM. Never let the cache break the request path.
- **Prevent poisoning:** run output guardrails (NeMo output rails) BEFORE writing a response into the cache; a malicious/low-quality answer must not be served to every near-match user.
- **Monitor:** log cache tier hit rates, false-positive rate (sample + LLM-as-judge or human review), and hit latency per feature. Target healthy total hit rate 30-60%; watch per-segment false positives. Record every check in the **Cache Hit/Miss Table** (see "Token Usage and Cost Persistence") so each tier's `estimated_cost_saved` is tracked and thresholds are tuned on data.

---

## Prompt Versioning and Management

- **Every prompt is a versioned, named artifact** (config/prompt store, not string literals scattered in code). Store `name`, `version`, `template`, `model`, and `created_by`/`date`.
- **Never change a prompt in place.** Bump the version on any edit. Prompt changes invalidate caches and shift KPIs - versioning makes both traceable.
- **Pin prompts to deployments.** The prompt store is read from config so a deployment pins a specific prompt version (roll back = point at the previous version).
- **Include prompt version in cache keys and traces.** Every span and cache entry records the prompt version used.
- **Few-shot and tool definitions are part of the prompt.** Version them together; they sit in the cached prefix, so stability matters.
- **Log the prompt (or its hash + template ID) on every call.** Never log raw PII by default; log prompt id + version + a content hash, plus any templating inputs needed for debugging.

---

## Chat History

- **Keep the conversation state in the request path** as a first-class object: a bounded, ordered list of messages with role, content, tool calls, and metadata (tokens, timestamps, model).
- **Token budget management:** truncate history from the oldest turns first, but keep the system prompt, instructions, and tools intact (they are the cacheable prefix). Prefer summary-of-older-turns over hard truncation when context is precious.
- **Order history correctly for caching:** static prefix → tools → older history → current turn last.
- **Persist history** where needed (Redis Stack / your session store) so stateless app instances can rebuild context; scope by tenant/session and respect retention policies.
- **Never store raw conversation data that wasn't consented to or needed**; redact PII per policy.
- **History is one layer of the context window** - budget, order, compress, and compact it per the "Context Engineering" and "Context Compaction" sections below.

---

## Context Engineering

Context engineering is the discipline of curating what goes into the model's context window on every call - which information, in what order, within what token budget. It is the superset of prompt engineering: the prompt is one part of the context, alongside system instructions, retrieved documents, tool definitions, conversation history, and tool results. Treat the context window as a finite resource with diminishing marginal returns; a larger window is a ceiling, not a license to fill it. Quality tracks context quality more than wording.

### Token budgeting

- **Budget the window by component, not "fill it up."** Allocate explicit, per-route token budgets for: system instructions, tool definitions, retrieved context, few-shot examples, chat history, and a reserved headroom for the response. Enforce them in code and fail loudly when a component overshoots.
- **A reasonable starting allocation:** system instructions ~10-15%, tool definitions ~15-20%, retrieved context ~30-40%, recent conversation = remainder, plus output headroom. When one category grows, others must shrink.
- **Always reserve output budget** - if the response has no room, the model truncates.
- **Never trim the system prompt or the current user message** to make room; trim from the lowest-signal components first.

### Assembly ordering (lost-in-the-middle)

Models attend disproportionately to the start and end of the context and under-use the middle ("lost in the middle"). A production-tested ordering:

1. **System prompt** (role, constraints, format, cacheable prefix)
2. **Long-term retrieved memory** (user preferences, established facts)
3. **Task-relevant retrieved chunks** (highest relevance first)
4. **Episodic/session summary** (compact history recap)
5. **Recent conversation** (last N turns, verbatim)
6. **Current user message** (last)

This keeps the most important instructions and evidence at the anchoring positions, and keeps the stable prefix at the front for prefix caching.

### Compression before truncation

- **Compress before you truncate.** The default reflex when a thread or document won't fit is to drop the oldest turns - but compression (summarizing older turns into a rolling recap, extracting key facts) preserves the signal that truncation throws away.
- **Ladder of escalation:** (1) lossless representation-level reuse - prefix caching, KV reuse, tool-schema deduplication; (2) reversible compaction - offload tool output or old turns to an external store and keep a pointer, fetch back on demand; (3) fidelity-preserving selection - better retrieval, reranking, per-chunk relevance filtering; (4) lossy summarization - compact history into a summary; (5) truncation - last resort only.
- **Tool output is context waste by default.** Design tools to return the minimum actionable information (relevant sections, not full files; extracted fields, not raw payloads), and prune spent tool results from the window.
- **Log what compression did.** Compression is opaque by default; record each compression event (type, tokens before/after, what was dropped) so quality regressions are localizable.

### What must survive verbatim (pin, don't summarize)

Summarizers rewrite, and they reliably drop or distort specific content. The following are load-bearing and must be preserved verbatim or structured, never left to prose summarization:

- **Constraints with negations** ("never X", "do not proceed without Y") - pin to a section compression never touches.
- **Exact numbers and thresholds** - extract to a structured parameter store (`max_records: 100`, not "about a hundred").
- **Goal statements and their revisions** - keep the ordered chain of task definitions and refinements; the latest supersedes earlier ones.
- **Rejection records** - store as `(rejected_option, reason, turn)` so the agent doesn't re-propose discarded approaches.
- **Tool-output attribution** - which tool, what query, what timestamp; provenance must survive so the agent can trace observations to source.

### Just-in-time loading

- **Don't pre-load all potentially relevant data.** Keep lightweight identifiers (file paths, stored queries, doc pointers) and load full content into context on demand with a tool/retrieval call when actually needed. This mirrors human working memory and keeps the window small.
- **Prefer external memory for anything not needed this turn.** Structured note-taking (a persistent scratchpad the agent reads/writes, e.g. a NOTES/state file) provides persistent memory with minimal overhead versus carrying everything in-context.

### Testing context management

Context logic is business logic - test it deterministically, not just via the LLM:

- **Needle-in-a-haystack probes** - insert a known fact at varying depths and verify the model can still retrieve it.
- **Context rot probes** - measure quality degradation as the window grows.
- **Specificity-retention probes** - assert a fact stated at turn 1 is recoverable at turns 50/100/500.
- **Assembly tests** - "history is truncated oldest-first", "chunks ordered by relevance not insertion order", "current user message always last", "summary retains the key facts".
- **Gate on results** - a change to ordering, budgeting, or compression without an eval on a held-out set is a hypothesis, not a best practice.

---

## Context Compaction

Context compaction is the practice of taking a conversation near the context-window limit, condensing its contents, and continuing from the condensed form instead of the raw history. It is the first lever for long-horizon coherence, but it is lossy by construction - design it deliberately.

### Patterns (choose deliberately, don't default)

| Pattern | What it does | Good for | Known failure mode |
|---------|--------------|----------|--------------------|
| **Summarize-and-replace** | LLM summarizes older turns; raw turns replaced by summary | Long multi-turn dialogue with low-signal history | Specificity rot - drops exact identifiers, numbers, quotes |
| **Sliding window / tail retention** | Keep last N turns verbatim, drop the rest | Short-horizon loops, coding, quick Q&A | Episodic amnesia - the original goal scrolls off the window; pair with a preserved goal statement |
| **Hierarchical memory** | Working memory in-context verbatim + periodically refreshed session summary + on-demand long-term store | Multi-session work where recency AND history matter | Policy complexity - decide what gets promoted between tiers |
| **External store + retrieval** | Offload everything, retrieve task-relevant chunks on demand | Long-horizon tasks, tool-heavy runs | Retrieval fidelity becomes the ceiling - measure recall@k before trusting it |

- **Compaction is not free.** It is a full extra model call (read everything + write the summary). Treat it as an investment with a payback period - set the trigger threshold high and only compact on runs long enough to amortize the cost; track compaction passes as their own usage/cost entries.
- **Trigger on state, not just token count.** Compacting mid-derivation destroys the negative evidence (failed attempts and why) that stops the agent repeating mistakes. Compact at task boundaries - after a subtask closes, between phases, when the user moves to a new task - not merely at a size threshold. Keep recent turns (e.g. ~10% of budget) verbatim, and summarize what precedes them.
- **Combine compaction with external memory.** Write the important things down durably BEFORE the summarizer gets to them (a memory/notes tool), so lossy compaction doesn't destroy what must survive. Also use context editing (surgically removing spent tool results, keeping everything else verbatim) as a lighter lever before wholesale compaction.
- **Keep the cached prefix out of the blast radius** - system prompt and tool definitions stay byte-identical and cacheable across compactions.
- **Tune the summarization prompt on real traces** - maximize recall first (capture every relevant piece), then iterate to precision (remove superfluous content). Preserve key decisions, open questions, active constraints, and tool outcomes.

---

## Logging, Tracing, and KPIs

- **Apply `.agents/skills/coding-rules/logging-and-tracing/SKILL.md`** and the KPI rules from `.agents/skills/coding-rules/llm-performance-kpis/SKILL.md` to every LLM call. Mandatory per request: TTFT, tokens/sec, latency (by stage: retrieval / LLM / post-processing), throughput counters, and retrieval quality.
- **One trace per request**, spans per stage: cache check → guardrails (input) → retrieval → LLM → guardrails (output) → cache write. Tag with `model`, `provider`, `reasoning_level`, `prompt_version`, `cache_tier`, `tenant_id`.
- **Log provider usage always:** input tokens, output tokens, reasoning tokens, cached tokens, finish_reason, cost estimate.
- **Error taxonomy:** rate limit, timeout, context-length-exceeded, provider 5xx, guardrail block - each counted as its own metric with the mapped project error type.
- **Never log raw prompts or responses by default.** Log ids, hashes, sizes, and KPI values; enable full payload capture only on explicit, sampled debugging.

---

## Token Usage and Cost Persistence (Required)

Token usage and cost for EVERY LLM-related request (chat, streaming, embeddings, reranking) MUST be logged and persisted to the database - not just metrics in a dashboard.

### What to record per request

Persist one row/record per LLM call (or per request spanning multiple calls) containing at minimum:

- `request_id`, `trace_id`, `feature_id`, `tenant_id`, `user_id` (when available)
- `provider` (openai / google / anthropic / self_hosted) and `model` + `model_version`
- `reasoning_level` and `prompt_version` used
- **Token usage:** `prompt_tokens`, `completion_tokens`, `total_tokens`, `reasoning_tokens` (thinking), `cached_tokens` (prompt cache reads), and `cache_write_tokens` when the provider reports it
- **Price:** `input_unit_price`, `output_unit_price`, `cached_input_unit_price`, `input_cost`, `output_cost`, `cached_input_cost`, `total_cost` - computed from a pinned, versioned price table (see below)
- `finish_reason`, `cache_tier` (exact / semantic / prefix / miss), `cache_hit` (bool), and per-stage KPIs (TTFT, latency, tokens/sec, retrieval quality)
- `timestamp` and `error`/`status`

### Cache Hit/Miss Table

In addition to the per-request usage row, persist a dedicated cache hit/miss record per request (or per cache tier consulted) so cache effectiveness can be measured and optimized. At minimum record:

- `request_id`, `trace_id`, `feature_id`, `tenant_id`
- `provider`, `model`, `prompt_version`, `cache_version`
- `cache_tier` - which cache was consulted (`exact` / `semantic` / `prefix` / `none`)
- `cache_hit` (bool) and `cache_status` (`hit` / `miss` / `bypass` / `fail_open`)
- **Tokens and cost actually incurred:** `prompt_tokens`, `cached_tokens`, `completion_tokens`, `actual_cost`
- **Estimated cost without cache:** `estimated_cost_without_cache` - what the request would have cost if no cache had been used (i.e. full provider price for the prompt + completion)
- **`estimated_cost_saved`** - `estimated_cost_without_cache - actual_cost`, an estimate of the money avoided through caching (exact, semantic, and prefix tiers combined). Because this is an estimate (provider cache pricing varies), store it as `estimated` and never use it as the billing record - billing always uses `actual_cost`.
- `timestamp`, `ttl`, `distance_threshold` (for semantic hits, when available)

Semantics for the cost-saved calculation:

- **Exact / semantic cache hit:** no provider call → `actual_cost = 0`, `estimated_cost_saved` = full provider cost the call would have incurred. This is the true saving of semantic caching.
- **Prefix cache hit:** provider call happened with discounted cached input → `actual_cost` = discounted cost, `estimated_cost_saved` = (full-price prompt cost) - (discounted prompt cost) + any saved latency value you choose to model.
- **Miss:** `actual_cost` = full price, `estimated_cost_saved = 0`.
- **Fail-open / bypass:** record why (cache timeout, cache down, non-cacheable response) so you can measure how much savings are being left on the table.

Use this table for: cache hit-rate dashboards per tier and per feature, cost-saved reporting, threshold tuning (per-feature false-positive monitoring), and deciding when a semantic cache pays for itself on a given traffic pattern.

### Rules

- **Compute cost at request time, persist it, and never reconstruct it later.** Use a central price table keyed by `(provider, model, price_version, date)`. Store the prices actually used in the row so later price-table edits never rewrite history.
- **Do not rely on logs for billing.** Structured logs are for debugging; the database rows are the source of truth for cost reporting. Write both, from the same normalized usage object.
- **Persist asynchronously but durably** - write to the usage/cost table off the request hot path (queue + worker / batch insert) so adding persistence never adds request latency; handle write failures with retry and alerting.
- **Cache hits are still usage.** A semantic-cache hit avoids a provider call (record `provider_cost = 0`, `cache_tier = semantic`); a prefix-cache hit bills discounted `cached_tokens` - record it, because it is a real provider cost. Cost reporting must distinguish all three tiers.
- **Embeddings and rerankers are LLM requests too.** They consume tokens/units - persist them with the same schema (type-tagged) so total spend is complete.
- **Backfill and retention:** keep cost rows long enough for billing/audit (define per-policy retention), partition by month, and index on `(timestamp, tenant_id, model)` for reporting.

---

## Review Checklist

- [ ] Feature code calls only the internal `chat()`/`stream()`/`embed()`/`rerank()` interface - no provider SDK imports in feature code
- [ ] Provider and model selection is configuration-driven; switching providers requires no code change
- [ ] Reasoning is expressed as `high` / `medium` / `low` / `default`, and `default` never sends a reasoning parameter to non-reasoning models
- [ ] NeMo Guardrails configured with input rails (jailbreak/injection) and output rails (content safety/PII) on all user-facing endpoints
- [ ] Prompt ordered stable-first → volatile-last for prefix caching; provider prefix caching enabled where available
- [ ] `cached_tokens` / cache-read usage is logged and cache-hit rate is monitored
- [ ] Redis Stack semantic cache present with per-feature thresholds and TTLs
- [ ] Cache invalidation implemented: TTL + event-driven + version-bumped on model/prompt/embedder changes
- [ ] Cache partitioned by tenant/feature at both write and read time; fail-open with hard timeout
- [ ] Only complete, non-personalized responses are cached; guardrails run before cache writes
- [ ] Prompts are versioned artifacts; prompt version in cache keys and traces
- [ ] Chat history ordered for cacheability with token-budget management
- [ ] Context budgeted per component (system/tools/retrieval/history) with output headroom; never trim the system prompt or current user message
- [ ] Context assembled in the production ordering (system → memory → retrieved → summary → recent turns → current message), respecting lost-in-the-middle
- [ ] Compression before truncation; load-bearing content (constraints, exact numbers, goals, rejections, provenance) pinned or structured, never left to summarization
- [ ] Just-in-time loading used for large data; external memory/notes for what isn't needed this turn
- [ ] Needle-in-a-haystack, context-rot, and assembly tests cover context management logic
- [ ] Compaction pattern chosen deliberately; compaction triggered at task boundaries, not just token thresholds; compaction passes tracked in usage/cost
- [ ] All KPIs from `.agents/skills/coding-rules/llm-performance-kpis/SKILL.md` are emitted per request with tags (model, reasoning level, prompt version)
- [ ] Token usage and cost (input/output/reasoning/cached, with prices used) persisted to the database for every LLM, embedding, and rerank request
- [ ] Cache hit/miss table persisted with `estimated_cost_saved` per request (per tier), used for hit-rate and cost-savings reporting
- [ ] Cost computed from a versioned price table; async-but-durable persistence off the request path
- [ ] One OpenTelemetry trace per request with per-stage spans; provider usage + errors logged
