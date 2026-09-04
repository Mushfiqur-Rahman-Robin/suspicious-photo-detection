# ARCHITECTURE - Suspicious Photo Detection (SPD) - v1

**Suspicious Photo Detection in Outlet Verification Images.**

- **Version:** 1.0.0
- **Status:** Authoritative record of system design
- **Read before writing any code that touches a module boundary, data flow, external dependency, or the output schema** (see §9 for the review checklist).
- **Companion docs:** `docs/SPEC.md` (behavioral contracts), `docs/PLANNING.md` (delivery plan), `docs/ENGINEERING_DECISIONS.md` (decision log & best-practice record), `project_docs/AI_Engineer_Assignment_Suspicious_Photo_Detection_PRD.pdf` (product source of truth).

---

## 1. System Overview

SPD is a **batch ML pipeline** that flags visually inconsistent images in outlet verification photo archives. For each outlet folder it decodes the images, extracts L2-normalized embeddings through a model-agnostic embedder, computes per-image suspicion scores from three complementary signals (centroid distance, kNN consensus, Isolation Forest), applies an adaptive per-outlet flag threshold, and emits a schema-validated JSON + CSV result plus a one-page write-up.

It is **not** a web service: there is no API server, no database, and no long-running process. It is a deterministic, cache-backed CLI (`spd`) composed of strictly bounded, single-responsibility stages (§4) - so each stage can be reasoned about, tested, and re-run independently.

---

## 2. Component Map

```
                         ┌──────────────────────────────────────────────┐
                         │              CLI (typer) - `spd`             │
                         │   run · embed · detect · report              │
                         │   arg parsing → Settings (config)            │
                         └──────────────────────┬───────────────────────┘
                                                │
                         ┌──────────────────────▼───────────────────────┐
                         │        PipelineRunner (pipeline)             │
                         │   orchestrates load → embed → score →        │
                         │   detect → report; per-stage timing/summary  │
                         └──┬──────────┬──────────┬──────────┬──────────┘
                            │          │          │          │
              ┌─────────────▼──┐ ┌─────▼─────┐ ┌──▼────────┐ ┌▼─────────────┐
              │   io (Dataset  │ │ embedding │ │ scoring  │ │  detection   │
              │  Loader, cache,│ │ Embedder  │ │ cosine,  │ │  centroid /  │
              │  ResultWriter) │ │ (DINOv2/  │ │ centroid,│ │  kNN / IF +  │
              │                │ │  CLIP)    │ │ kNN      │ │  threshold   │
              └────────┬───────┘ └─────┬─────┘ └────┬─────┘ └──────┬──────┘
                       │               │            │              │
                       └───────────────┴────────────┴──────────────┘
                            typed entities + ports (core)

   Cross-cutting: Config (settings.py + .env), Observability (structlog + timing),
                  Reproducibility (seed + content-addressed embedding cache)
```

### Responsibilities

| Component | Responsible for | NOT responsible for |
|---|---|---|
| CLI | Arg parsing, building `Settings`, wiring subcommands, exit codes | Any ML or scoring logic |
| PipelineRunner | Staging orchestration, per-stage timing, run summary | Image decoding, scoring math |
| io | Dataset discovery, image decoding, embedding cache, JSON/CSV writing | Computing scores or detecting outliers |
| embedding | `Embedder` adapters (DINOv2/CLIP), preprocessing, L2-normalization | Outlier decisions |
| scoring | Cosine similarity, robust centroid, kNN statistics, signal fusion | Loading images or writing files |
| detection | Outlier rules (centroid/kNN/IF), adaptive threshold, reason templates | Embedding extraction |
| core | Entities, ports/interfaces, exceptions, output-schema validation | Heavy deps (torch/numpy/sklearn) |
| observability | structlog factory, timing, run-summary emission | Business logic |

---

## 3. Key Design Decisions

> **Decision: Model-agnostic embedding layer behind an `Embedder` port (ED-1).**
> **Reason:** Embedding models evolve faster than the pipeline; DINOv2 vs CLIP vs a future model must be a config change, not a rewrite.
> **Consequence:** Feature code never imports a model's weights; each model is one adapter + a config entry.

> **Decision: Detection as an ensemble of three complementary signals (ED-4).**
> **Reason:** No single metric catches every fake: centroid distance is confused by multi-cluster outlets, kNN misses tight fake cliques, Isolation Forest is unstable at low N. Fusing three independent signals maximizes precision without labels.
> **Consequence:** Each signal is a separable, unit-testable component; the fusion weights are config.

> **Decision: Adaptive, per-outlet, distribution-free threshold (ED-5).**
> **Reason:** Outlet appearance variance differs wildly across outlets; a global threshold is provably wrong.
> **Consequence:** Threshold is `median + k·MAD` with an absolute floor; no per-outlet tuning, no labels required.

> **Decision: Batch CLI pipeline, no server/database/cache-service (ED-8).**
> **Reason:** The problem is a one-shot (or resumable) batch job over 159 outlets; a web service, Postgres, or Redis would be pure overhead.
> **Consequence:** Typed in-memory entities + a file-based embedding cache are the only persistence; the pipeline runs on a laptop or in CI.

> **Decision: Content-addressed embedding cache (ED-6).**
> **Reason:** Embedding is the expensive step; caching by image content hash + model makes re-runs and stage re-runs essentially free and guarantees reproducibility.
> **Consequence:** The cache is transparent (cold vs warm yields identical results); changing model/weights changes the cache key namespace.

> **Decision: Robust centroid = coordinate-wise median (ED-3).**
> **Reason:** A single fake image must not drag the outlet's reference appearance toward itself (mean is not breakdown-resistant).
> **Consequence:** The centroid signal stays meaningful even with a few outliers present.

---

## 4. Module Boundaries

```
src/
├── config/          settings.py (Pydantic Settings), model registry, feature config.
│                    The ONLY module allowed to read env/config.
├── core/            entities (Outlet, ImageRecord, Embedding, SuspicionProfile,
│                    OutletResult, FlaggedImage), exceptions, output-schema models,
│                    ports (Embedder, SimilarityScorer, OutlierDetector, ResultWriter).
│                    Pure Python; NO torch/numpy/sklearn imports.
├── embedding/       Embedder adapters (DinoV2Embedder, ClipEmbedder), preprocessing,
│                    L2-normalization, batched inference.
├── scoring/         cosine similarity, robust centroid, kNN statistics, signal fusion.
│                    Pure numpy/scipy; no image I/O, no model loading.
├── detection/       OutlierDetector implementations (centroid/kNN/IF fusion),
│                    adaptive MAD threshold, reason templates.
├── pipeline/        PipelineRunner + stage orchestration + run summary.
├── io/              DatasetLoader (discovery/decoding), EmbeddingCache (parquet/npy),
│                    ResultWriter (JSON + CSV).
├── reporting/       write-up generation + summary metrics.
├── cli/             typer app (`spd`), subcommands, exit codes.
└── observability/   structlog factory, timing context, run-summary emission.
```

The source tree is **flat**: each module is a top-level package directly under `src/` (no nested `suspicious_photo_detection/` package; the distribution name remains `suspicious-photo-detection`). Imports are top-level, e.g. `from scoring import ...`, `from embedding import ...`.

Boundary rules:
- `core` **must not** import `embedding`, `scoring`, `detection`, `io`, `cli`, or framework SDKs (depends on ports/interfaces only).
- `embedding` implements the `Embedder` port; named `<Model>Embedder` (`DinoV2Embedder`, `ClipEmbedder`).
- `scoring` is pure math on embeddings; never loads images or models.
- `detection` consumes scoring signals and emits `FlaggedImage`s; never decodes images.
- `io` handles filesystem; never computes scores or detects outliers.
- `pipeline` orchestrates via ports only; contains no ML or I/O internals.
- Configuration reads happen **only** inside `config/`.

---

## 5. Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.13 | team stack; PyTorch ecosystem |
| Embedding | DINOv2 ViT-S/14 (`torchvision`), CLIP (`open_clip_torch`) | model-agnostic per ED-1 |
| Array/math | numpy + scipy | vectorized similarity, MAD, distances |
| Outlier ML | scikit-learn (Isolation Forest, pairwise distances) | robust, well-tested, deterministic with fixed seed |
| Image I/O | Pillow | JPEG/PNG decode, preprocessing |
| Validation/config | Pydantic v2 + pydantic-settings | strict boundaries, parse-don't-validate |
| CLI | typer | typed, self-documenting CLI |
| Observability | structlog | structured logs + timing |
| Cache | Parquet/`.npy` files on disk | dependency-free, content-addressed |
| Container | Docker (multi-stage) | hardening per `dockerfile-optimization` skill |
| CI/CD | GitHub Actions + pre-commit | all SPEC §20 gates |

---

## 6. Data Flow

### 6.1 Full run (`spd run`)

```
CLI → Settings (config) → PipelineRunner
  → DatasetLoader.discover_outlets()                 [io]
  → for each outlet (batched):
        Embedder.embed(images)                       [embedding ↔ EmbeddingCache]
        SimilarityScorer.score(embeddings)           [scoring]
        OutlierDetector.detect(signals)              [detection]
        assemble OutletResult (schema-validated)     [core]
  → ResultWriter.write(results)                      [io → results.json + results.csv]
  → Reporting.write_up + run summary                 [reporting]
```

- Each stage logs its timing; the runner aggregates a `run_summary.json`.
- No stage mutates another stage's inputs; stages communicate through typed entities and ports.

### 6.2 Embedding cache flow

```
Embedder.embed(image)
  → key = sha256(image_bytes) + model + model_version
  → EmbeddingCache.get(key) ── hit ──► return stored vector
  │                          └ miss ▼
  → encode (torch, no_grad, eval) → L2-normalize
  → EmbeddingCache.put(key, vector) → return vector
```

### 6.3 Detection flow

```
embeddings (N×d) → cosine matrix S → centroid distance + kNN consensus + IF score
  → fuse → suspicion_score ∈ [0,1] → threshold = max(median + k·MAD, floor)
  → flag where score > threshold → FlaggedImage(file_name, score, reason)
  → ranking = argsort(score, desc)
```

---

## 7. External Dependencies

| Dependency | Purpose | Failure handling |
|---|---|---|
| DINOv2 / CLIP weights (torchvision / open_clip) | embeddings | deterministic inference; weights pinned by library version; no runtime network |
| scikit-learn | Isolation Forest, pairwise distances | pinned version; deterministic with fixed seed |
| Pillow | image decode | corrupt files rejected with clear error (§SPEC 5.1) |

Isolation notes: all model access goes through `embedding/` adapters; no network access at runtime; the dataset is untrusted input handled at the `io` boundary.

---

## 8. Non-Goals

This system deliberately does NOT:
- Assume timestamps, visit order, or EXIF metadata.
- Train or fine-tune any model (pretrained features only).
- Flag every appearance change (gradual change is legitimate).
- Use a global "outlet template" (comparison is strictly per outlet).
- Provide a web service, REST API, database, or background daemon.
- Require labeled training data (unsupervised method).

---

## 9. How to Follow / Update This Document

- **Before writing code:** read this document + `docs/SPEC.md`; verify the change fits within a module's responsibility, respects data-flow direction, adds no unapproved dependency, and does not implement a Non-Goal.
- **Update it in the same PR as the change** when: a module/component is added, data flow changes meaningfully, a key decision is made/reversed, an external dependency is added, boundaries are redefined, or a Non-Goal is promoted. Note what changed and why; preserve past decisions.
- Record the rationale for new or reversed decisions in `docs/ENGINEERING_DECISIONS.md` (ADR-style) and keep the ED-xx registry in `docs/SPEC.md` §9 as the normative table.
- Do NOT update for implementation details, bug fixes, or behavior-preserving refactors.

### Architecture Review Checklist
- [ ] ARCHITECTURE.md read before implementation began
- [ ] Change respects all module boundaries (§4)
- [ ] Data flow follows §6 direction
- [ ] New external dependency consistent with §7 approach and justified in this doc
- [ ] Key design decisions (§3) documented with rationale
- [ ] No Non-Goal implemented
- [ ] ARCHITECTURE.md updated in the same PR if structure changed

---

## 10. Decision Log (append as decisions change)

| Date | Decision | Change note |
|---|---|---|
| v1.0 | Initial architecture published | Baseline |
