---
name: llm-performance-kpis
description: "Mandatory instrumentation for LLM projects: time to first token, tokens per second, latency, throughput, and retrieval quality must always be measured."
license: MIT
---

# Skill: LLM Performance KPIs

## Purpose
LLM applications degrade silently. Response quality and latency shift with model versions, prompt changes, context growth, embedding drift, and load. If the project does not measure its core metrics, nobody can tell whether a change improved or regressed the system. For any project that calls an LLM, performs retrieval, or streams tokens, these five KPIs are mandatory and must be part of the code itself - not bolted on later.

The five mandatory KPIs:

1. **Time to First Token (TTFT)** - latency from request start to the first token emitted (streaming).
2. **Tokens per Second (T/s)** - throughput of token generation during streaming (generation speed).
3. **Latency** - end-to-end time for a complete request/response cycle (TTFT + generation + retrieval + post-processing).
4. **Throughput** - requests or tokens processed per unit of time, typically under sustained load.
5. **Retrieval Quality** - how well retrieval finds the information the answer depends on (e.g., recall, precision, hit rate, nDCG).

---

## General Principles

- **Measure in production, not just in tests**: Real prompts, real context sizes, and real load. Synthetic benchmarks complement but never replace production telemetry.
- **Instrument in the request path**: Metrics must be captured by the serving code itself, with zero manual steps.
- **Log the KPI alongside the request context**: Store prompt size, context/token count, model name, model version, and any sampling parameters that apply to the model (e.g. temperature or reasoning effort, where supported) with every metric so regressions are explainable.
- **Tag every metric**: At minimum tag `model`, `endpoint`/`feature`, and `environment`. Without tags, a mean latency is meaningless.
- **Report both mean and percentiles**: For latency and TTFT, p50/p95/p99 tell a different story than the average. Always record a distribution.
- **Fail loudly on missing instrumentation**: A code review that finds an un-instrumented LLM path must be blocked. KPIs are a correctness requirement, not a nice-to-have.
- **Keep metrics cost-aware**: Use histograms and sampling so that instrumenting does not itself become the bottleneck or a privacy risk (never log raw prompts by default).

---

## Time to First Token (TTFT)

**What it measures:** The perceived start of a response. High TTFT feels like the app is broken.

**How to measure:**
- Start the timer before the LLM call (including any pre-request work that blocks streaming: auth, RAG retrieval, tool setup).
- Stop at the first chunk/token delivered to the caller.
- Record separately as `llm_ttft_ms` and, where pre-request work is significant, `total_ttft_ms` (pre-work + LLM TTFT) and `pre_work_ms`.

**Code requirements:**
- Streaming responses must emit the first-token timestamp as the very first observability event.
- Alert when p95 TTFT exceeds the product budget (e.g., > 2s), and when TTFT grows with context size.

---

## Tokens per Second (T/s)

**What it measures:** Generation speed of the model. It is the user-visible pacing of a stream.

**How to measure:**
- Count tokens received between first token and completion, divide by elapsed generation time.
- Use the provider's token accounting or a consistent tokenizer; do not mix tokenizer definitions across comparisons.
- Record at completion of each stream as `llm_tokens_per_second`.

**Code requirements:**
- Compute and log T/s at the end of every streamed completion, not just on sampled requests.
- Track input vs output token counts (`prompt_tokens`, `completion_tokens`) alongside T/s; output T/s is the meaningful number.

---

## Latency

**What it measures:** End-to-end request time from caller to full response. Includes everything the LLM path touches.

**How to measure:**
- Time from request arrival to the moment the final response is returned (full completion, not just first token).
- Break it down into the contributing stages so regressions are attributable: retrieval, pre-processing, `llm_latency_ms`, post-processing, and streaming transfer time.
- Record `request_latency_ms` (full end-to-end) and `llm_latency_ms` (just the model call).

**Code requirements:**
- Instrument every LLM call site, including batch/offline jobs, not only the online API.
- Log the latency budget consumed so failures and timeouts are visible against the SLA.
- Report p50/p95/p99, never only the mean.

---

## Throughput

**What it measures:** How many requests or tokens the system sustains under load. Determines capacity planning, concurrency limits, and cost per request.

**How to measure:**
- Requests per second (`rps`) and tokens per second aggregated across the service (`tps`).
- Measure under sustained, realistic load (concurrency, context sizes, rate limits), not single-request timings.
- Track provider rate-limit and quota errors; they cap real throughput and must be visible.

**Code requirements:**
- Emit aggregate counters (`requests_total`, `tokens_total`) and a rolling throughput gauge at the service boundary.
- Record queue depth and time-in-queue when requests can be queued (retries, semaphores, batching).
- Capture retry and backoff events as their own metric so throttling is visible as a cause of throughput loss.

---

## Retrieval Quality

**What it measures:** Whether the RAG/retrieval stage actually finds the evidence the answer depends on. Bad retrieval yields confident but wrong answers, and it is invisible without this KPI.

**How to measure (choose based on what ground truth is available):**
- **Hit rate / Recall@k**: Did the retrieved documents contain the needed answer (evaluation sets with known-good documents).
- **Precision@k**: How many of the retrieved items were relevant.
- **nDCG / MRR**: Rank-sensitive quality of the returned order.
- **Context utilization**: Fraction of retrieved tokens actually used/cited in the final answer - a strong, always-available proxy.

**Code requirements:**
- Always log retrieval metadata per request: query embedding time, retrieval `k`, number of documents retrieved, source count, and score distribution of returned chunks.
- Where ground truth exists, compute retrieval quality offline in an evaluation harness and gate model/reindex changes on it.
- Track the degradation signals online: fallback-to-no-results rate, low top-score rate, and answer-not-grounded rate.

---

## Metric Catalog (reference)

| KPI | Metric name (example) | Type | Tags |
|-----|------------------------|------|------|
| TTFT | `llm_ttft_ms`, `total_ttft_ms` | histogram (p50/p95/p99) | model, endpoint, env |
| T/s | `llm_tokens_per_second` | gauge/histogram | model, endpoint, env |
| Latency | `request_latency_ms`, `llm_latency_ms` | histogram (p50/p95/p99) | model, endpoint, env, stage |
| Throughput | `requests_total`, `tokens_total`, `rps`, `tps` | counter/gauge | endpoint, env, model |
| Retrieval | `retrieval_hit_rate`, `retrieval_k`, `retrieval_top_score`, `context_utilization` | gauge/counter | collection, embedder, endpoint |

---

## Review Checklist

- [ ] Every LLM call site logs TTFT, T/s, and end-to-end latency
- [ ] Every retrieval path logs query time, `k`, result count, and score distribution
- [ ] Metrics are tagged with model, endpoint/feature, and environment
- [ ] Histograms/percentiles (p50/p95/p99) are used, not just averages
- [ ] Streaming paths emit first-token timing and compute T/s on completion
- [ ] Provider errors (rate limits, timeouts, retries) are counted as metrics
- [ ] Latency is broken down by stage (retrieval / LLM / post-processing)
- [ ] Retrieval quality has an offline evaluation path where ground truth exists
- [ ] No raw prompt content is logged unless explicitly designed for it
- [ ] The change includes a smoke test or integration check that confirms the metrics are emitted
