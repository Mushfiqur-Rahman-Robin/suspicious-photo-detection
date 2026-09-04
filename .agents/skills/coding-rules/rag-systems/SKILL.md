---
name: rag-systems
description: Best practices for building Retrieval-Augmented Generation systems - chunking, embedding, hybrid retrieval, reranking, indexing, caching, evaluation, observability - plus a catalog of RAG patterns and when each applies.
license: MIT
---

# Skill: RAG Systems

## Purpose

Retrieval-Augmented Generation quality is bounded by the weakest stage of the pipeline: parse → chunk → embed → index → retrieve → rerank → augment → generate. A perfect LLM cannot compensate for chunks that split the answer in two, embeddings that never match the query, or a ranker that surfaces noise.

This document is a set of **guidelines, not rules**. Each recommendation is a well-tested default with the reasoning behind it - but the right answer for your corpus, latency budget, and domain may differ. Where a guideline conflicts with your measured reality, **measure first, deviate deliberately, and document the deviation**. The LLM and embedding layers should stay model-agnostic (see `.agents/skills/coding-rules/llm-development/SKILL.md`); KPIs from `.agents/skills/coding-rules/llm-performance-kpis/SKILL.md` apply to every RAG path.

---

## Referenced Documents

- `.agents/skills/coding-rules/llm-development/SKILL.md` - model-agnostic LLM layer, guardrails, prefix + semantic caching, token usage/cost persistence.
- `.agents/skills/coding-rules/llm-performance-kpis/SKILL.md` - retrieval quality, latency, TTFT, throughput, tokens/sec.
- `.agents/skills/coding-rules/design-patterns/SKILL.md` - structure the retrieval pipeline and cache layers with these patterns.

---

## Architecture: Two Pipelines

Prefer separating indexing from querying - two workflows that share only the index:

1. **Offline indexing pipeline** (batch): parse → clean → chunk → embed → write to vector + keyword index.
2. **Online query pipeline** (real-time): query rewrite → hybrid retrieve → fuse → rerank → assemble context → generate.

This keeps ingestion spikes from starving query traffic and lets each evolve independently. A single script is fine to start; refactor to two pipelines before scaling.

---

## RAG Patterns at a Glance

The default pipeline is hybrid retrieval + rerank; the patterns below modify or replace stages of it. Treat them as a **menu, not a ladder** - pick the lightest pattern that works on your evals, and re-measure any quoted number on your own corpus.

| Pattern | What it does | Reach for it when | Cost |
|---|---|---|---|
| Naive single-shot | retrieve → assemble → generate | Simple factoid Q&A | Low |
| Hybrid + rerank (default) | vector + BM25, RRF fusion, cross-encoder rerank | Most production systems | Med |
| Query rewrite / decomposition | rewrite, split, or HyDE-expand the query | Ambiguous queries; recall gaps | Low |
| RAG-Fusion | generate several sub-queries and fuse their ranks | Ambiguous, hard queries | Med |
| Multi-vector / ColBERT | token-level late interaction (MaxSim) | Long docs, entity-heavy, out-of-domain | High |
| Contextual retrieval | LLM writes a context blurb per chunk before embedding | Small, accuracy-critical corpus | High |
| Parent-document | retrieve small chunks, generate on larger parents | Precision + context both matter | Med |
| Hierarchical / RAPTOR | cluster + summarize into a tree; retrieve at multiple levels | Long docs, thematic questions | High |
| GraphRAG | entity/relation graph traversal | Multi-hop reasoning across documents | Very high |
| Self-RAG / CRAG | judge + correct retrieval before answering | Low-trust or noisy corpora | High |
| Adaptive retrieval (FLARE, DRAGIN) | retrieve only when the model signals uncertainty | Long generations, cost-sensitive | High |
| Agentic / tool-use RAG | plan → multi-step retrieve/refine → answer | Multi-hop, multi-source corpora | High |
| Context compression (FiD, LongRAG, FILCO) | densify or filter context before generation | Context-window pressure | Med |

### Guidance by family

**Query-side (cheapest first).** Rewrite the query before touching the pipeline - usually the best value-per-complexity. Decompose into ≤6 independently retrievable sub-queries, keep the tree flat, run independent ones in parallel. HyDE embeds a hypothetical answer (good when query and document vocabulary differ); step-back asks a broader question first. RAG-Fusion fuses ranks from several query variants.

**Retrieval architecture.** Naive single-shot is the baseline. Hybrid dense + BM25 with RRF is the default. Rerank with a cross-encoder over the candidate pool - the highest-leverage precision fix. ColBERT late interaction stores per-token vectors and scores with MaxSim: storage is ~30× a single-vector index raw (compression brings it to ~4×); don't threshold raw MaxSim (unnormalized - use rank fusion or normalize by length); watch `doc_maxlen` silent truncation and length bias; best for out-of-domain or entity-heavy corpora.

**Structured.** GraphRAG traverses a knowledge graph for multi-hop, cross-document questions - keep vector RAG as the default and route graph-shaped queries to it. Entity resolution is the hard part (layer hash → embedding → LLM merging; below ~80% relation precision the graph hop *hurts*). Prefer an ontology in regulated domains; community summarization serves only global questions and inflates prompts. Plan updates (incremental vs. full re-index) and evaluate graph / retrieval / answer separately. RAPTOR builds a cluster-summary tree for long-doc thematic queries.

**Self-correcting.** Self-RAG fine-tunes the model to decide when to retrieve and to check its own support. CRAG adds a cheap evaluator that triggers corrective search - lighter than Self-RAG. Adaptive retrieval (FLARE, DRAGIN) retrieves only on low-confidence spans.

**Agentic.** Retrieval becomes a tool the agent calls on demand. Bound the loop (iteration cap 3-7, token budget, timeout, confidence threshold) or it eats the budget. The planner emits a schema-validated plan; a separate validator returns named verdicts. Route most traffic to classic RAG, and build strong per-source retrievers first. Expect 2-5× latency; cache the shared prefix across iterations.

**Context and modality.** Parent-document retrieves small and generates large. Contextual retrieval prepends an LLM-written blurb per chunk (strong accuracy, LLM-per-chunk ingest cost). FiD/LongRAG/FILCO compress context under window pressure. For tables, generate an executable query (SQL or a graph query) rather than vectorizing rows; index image embeddings for multimodal; embed in the native language for multilingual.

---

## Document Parsing and Cleaning

Garbage in, garbage out - parsing errors are a common hidden retrieval killer.

- Parse by document type: PDFs (extraction with OCR fallback), HTML/Markdown (strip chrome), tables and code blocks (preserve structure), scanned docs (OCR first).
- Clean before chunking: remove boilerplate, fix encodings, deduplicate near-duplicates.
- Redact PII before embedding, not after.
- Preserve useful metadata per chunk: `doc_id`, `source_url`, `title`, `heading_trail`, `page`, `timestamp`, `permissions`/`tenant`, `embedding_model` + version, prompt/ingest version.
- Design the metadata schema (especially access-control fields: owner, roles, sensitivity) before indexing - retrofitting a filter field forces a full re-index.

---

## Ingestion Freshness

Stale content silently poisons answers.

- Give every source a refresh cadence and alert when ingestion falls behind.
- Hash-diff instead of full reprocessing: embed only new/changed chunks, upsert by `doc_id`, delete chunks whose hash disappeared.
- Cascade deletes and de-permissioning: removing a source removes its chunks, embeddings, and any cached answers; audit for orphans.
- Tie freshness to versioning: store ingest + document version per chunk for atomic, traceable re-index cutovers.

---

## Chunking: Which Strategy, When

Chunking sets the unit your embedder represents as one vector and the unit the LLM reasons over. Match it to the document type and validate on your eval set.

| Strategy | Cost | Best for | Avoid when |
|---|---|---|---|
| Recursive / fixed-size (~256-512 tokens, 10-20% overlap) | Cheap | Default for most corpora | Documents with critical structure |
| Structure-aware (headers/HTML/Markdown) | Cheap | Well-structured docs | Scanned/loose text |
| Semantic (split at similarity dips) | Expensive | Poorly structured, multi-topic docs | Homogeneous corpora; tight budget |
| Page-level | Cheap | Paginated/financial PDFs | Arbitrary pagination |
| Parent-document (small child for search, large parent for generation) | 2× storage | Long, cross-referenced docs | Short self-contained docs |
| Late chunking (embed whole doc, pool token vectors) | Moderate | Long reference corpora | Short docs |
| Contextual retrieval (LLM blurb per chunk) | Expensive | Bounded, accuracy-critical corpus | Churning corpus |

- Start with recursive ~512-token / 10-20% overlap; tune on your queries (factoid 256-512, multi-hop 512-1,024).
- If using semantic chunking, enforce a minimum chunk size (merge fragments to 200-400 tokens) - tiny slivers starve the LLM.
- Treat semantic chunking as "measure, then adopt" - it costs 2-4× ingest embeddings; adopt only on a clear, measured win.
- Prefer document-aware selection over one global default for heterogeneous corpora; keep tables, lists, and code blocks intact.
- Record chunking strategy + parameters + ingest version in metadata.

---

## Embedding

- Pick the embedder by quality-per-cost on your domain (leaderboards are a starting point, not a verdict); use cosine similarity consistently.
- Use the same model for query and index embedding - mismatched spaces silently destroy retrieval.
- Prefer Matryoshka-representation models (store full vector, truncate at query time); 768-1,024 dims is a practical sweet spot.
- Use task/instruction prefixes if the model supports them - a free boost.
- Version the embedding model; changing it means a full re-index in a new index, then swap traffic atomically (blue-green).
- Cache embeddings by content hash so unchanged chunks cost zero on re-index.

---

## Indexing

- Vector index: HNSW is a strong default; IVF for large scale. Tune `ef_construction`, `ef_search`, `M` for the latency/recall tradeoff.
- Pair the vector store with a keyword/BM25 (or full-text search) index - hybrid retrieval depends on it.
- Make metadata filterable (tenant, permissions, source, date, doc_type) and apply filters before similarity search where possible.
- Keep an `index_version` (embedding model + chunker + prompt) for A/B testing and rollback.
- Ingest incrementally (checksums, upsert by `doc_id`, delete missing hashes); use push/webhooks for frequently-updated sources.
- Audit the index periodically; delete stale/removed documents.

---

## Retrieval

- Hybrid search is the strong default: dense vector + BM25 in parallel (semantics + exact identifiers/error codes/jargon).
- Fuse with Reciprocal Rank Fusion (RRF) - no score calibration needed. Tune weights empirically if you have a reason.
- Over-retrieve a little: 20-50 candidates even if 3-5 reach the LLM - the reranker benefits from a diverse pool.
- Query-side improvements often beat chunking changes: rewriting, decomposition, or HyDE.
- Apply metadata filtering early (access control, doc type, date range); if zero-result queries rise, add a relaxation fallback.

---

## Reranking

- Reranking is often the highest-leverage precision fix: retrieve broad, rerank focused (retrieve 20-50 → rerank → top 3-5).
- Cross-encoders score query+chunk jointly and are far more accurate than bi-encoders; use a hosted or open cross-encoder reranker, ColBERT for high throughput.
- Use rerank scores for ordering, not absolute thresholds - they are relative; set thresholds empirically.
- Skip reranking under strict latency (<300ms), very long queries, or when the top hit already dominates.
- Justify with evals: a reranker moving faithfulness 0.72→0.78 is worth it; 0.88→0.89 probably isn't.

---

## Context Assembly and Generation

- Consider parent-document expansion: retrieve small chunks, expand to parent/neighbors for the prompt.
- Encourage citations (`[S1]`, `[S2]` with heading trail + `doc_id`); post-process to URLs and flag unsourced claims.
- Order chunks best-first (models attend to the start); add an explicit "say if it isn't in the sources" clause.
- Prefer a clear refusal (`NO_ANSWER` / "I don't know") over fake confidence when sources lack the answer; track refusal quality as an eval signal.
- Respect the context budget - 20 chunks when 5 suffice costs more and can degrade quality (middle-of-context attention drop).
- Guardrails apply to RAG: retrieval rails can reject irrelevant chunks before the prompt; output rails catch unsupported claims (see `.agents/skills/coding-rules/llm-development/SKILL.md`).

---

## Security

A RAG pipeline is a prompt-injection surface (retrieved content joins the prompt), an access-control surface, and a data-leak surface. Follow OWASP's RAG Security guidance. Fail closed (deny) on safety-critical paths - the one place not to fail open - and enforce access control at retrieval time, not as a post-filter.

- **Access control at retrieval.** Attach permission metadata per chunk at ingestion and filter BEFORE similarity search; enforce at the chunk level and re-evaluate at query time (permissions change).
- **Tenant isolation.** Separate namespaces/collections per tenant; assert isolation with cross-tenant test queries in CI.
- **PII detection at ingestion.** Detect before embedding (query-time filters are too late); redact, tag, or exclude, and keep an audit log.
- **Prompt-injection resistance.** Run an adversarial/injection test suite in CI on every ingestion-schema or prompt change.
- **Data-poisoning safeguards.** Content hashing, embedding anomaly detection, and an approval/quarantine workflow for untrusted sources.
- **Query-abuse protection.** Normalize/inspect queries, rate-limit per identity, monitor for corpus-probing patterns.
- **Output validation.** Redact PII/secrets, prefer schema-validated structured outputs, reject tool arguments outside an allowlist.
- **Auditability.** Log the full pipeline per request as replayable traces; keep a deletion/retention log (e.g. GDPR erasure).

---

## Caching

- Semantic cache on the query path: embed the query, match similar past queries, return the cached answer without re-running retrieval or the LLM.
- Include answer-affecting dimensions in the key: `(normalized query, filters, prompt version, model, chunk IDs)`.
- Invalidate via TTL (per-feature volatility), event-driven deletes on source changes, and version bumps on model/prompt/embedder/chunker changes.
- Cache only grounded, complete, non-personalized answers that passed output guardrails; avoid truncated or time-sensitive responses.
- Fail open with a hard timeout (~200ms) - a slow cache should never break the request path.
- Track effectiveness with the cache hit/miss table from `.agents/skills/coding-rules/llm-development/SKILL.md` (`estimated_cost_saved` per tier).
- Keep ingestion and query caches separate (content-hash embedding cache vs. retrieval/answer cache).

---

## Evaluation

RAGAS is a common harness for measuring RAG pipeline quality (an equivalent harness works). Gate chunking/embedding/retrieval/prompt changes on it.

- Build a gold eval set early: 30-100+ real domain questions with the correct source passage (and reference answers where possible); version and re-run it on every change.
- Core RAGAS metrics: `context_precision` (noise in retrieval), `context_recall` (missed info), `faithfulness` (grounded in context), `answer_relevance`.
- Run it on real (question, contexts, answer) triples from your pipeline, not synthetic ones.
- Supplement with retrieval-only metrics: recall@k, precision@k, MRR, nDCG@k.
- Online metrics (from `.agents/skills/coding-rules/llm-performance-kpis/SKILL.md`): hit rate, low top-score rate, no-results rate, context utilization, latency, TTFT, throughput.
- Watch for regression and embedding drift (model-version changes, data shift); pin versions and monitor.
- Segment evals by doc type / tenant / query intent - a good average can hide a broken segment.

---

## Observability, Logging, Chat History

- One trace per query with spans per stage (rewrite → retrieval → fusion → rerank → assembly → LLM → guardrails → cache), tagged with `chunker_version`, `embedding_version`, `prompt_version`, `retrieval_k`, `rerank_top_n`, `cache_tier`.
- Log retrieval metadata: embedding time, `k`, per-result scores, rerank scores, chunk sizes, context token count, citation success rate.
- Per-stage latency (retrieval, rerank, LLM, total); a ~500ms p95 retrieval target is a reasonable start - measure yours.
- Cost per query (embedding + vector store + rerank + LLM tokens incl. reasoning); derive from persisted usage rows, not logs.
- Persist token usage and cost for every LLM/embedding/rerank call (see `.agents/skills/coding-rules/llm-development/SKILL.md` → "Token Usage and Cost Persistence").
- Chat history: keep the conversation for follow-ups but retrieve fresh per turn; assemble in cache-friendly order (static prefix → history → current question last).

---

## Review Checklist

A sanity pass - "did we consider this?", not "did we obey this?"

- [ ] Indexing and query pipelines separated (or planned before scaling)
- [ ] Documents parsed/cleaned; PII redacted before embedding
- [ ] Metadata schema (incl. ACL) designed before indexing; stored per chunk
- [ ] Ingestion freshness: cadence, hash-diff, cascading deletes, orphan audit
- [ ] Chunking strategy chosen deliberately and recorded; recursive ~512/10-20% the default; semantic chunking has a min-size floor
- [ ] Embedder chosen on domain evals; query and index use the same model; version stored; blue-green re-index
- [ ] Hybrid search (vector + BM25) with RRF; metadata filters before search
- [ ] Reranker considered (20-50 → top 3-5), tradeoff justified by evals
- [ ] Citations encouraged; unsourced claims flagged; refusal when evidence is missing
- [ ] Access control at retrieval time (chunk-level, pre-filter); tenant isolation asserted in CI
- [ ] PII at ingestion; injection/adversarial tests in CI; poisoning safeguards
- [ ] Fail closed on safety paths; rate-limiting and abuse monitoring
- [ ] Semantic cache with key design, TTL + event-driven + version invalidation, fail-open timeout
- [ ] Cache hit/miss table (`estimated_cost_saved`) used to tune tiers
- [ ] Gold eval set + RAGAS metrics run on changes; refusal quality tracked
- [ ] Trace per query with per-stage latency; cost per query tracked
- [ ] Usage/cost persisted for every LLM/embedding/rerank call
- [ ] All `.agents/skills/coding-rules/llm-performance-kpis/SKILL.md` KPIs emitted; retrieval quality monitored
