# SPEC - Suspicious Photo Detection (SPD) - v1

**Suspicious Photo Detection in Outlet Verification Images.**

- **Version:** 1.0.0
- **Status:** Draft (approved for planning)
- **Type:** Technical Specification (blueprint for developers)
- **Author:** Tech Lead
- **Source of truth:** `project_docs/Suspicious_Photo_Detection_PRD.pdf`. This SPEC MUST NOT contradict the PRD. Where the PRD and this SPEC differ, the PRD wins unless this SPEC explicitly records an Engineering Decision approved by the Tech Lead.
- **Companion documents:** `docs/PLANNING.md` (delivery plan), `docs/ARCHITECTURE.md` (system design record), `docs/ENGINEERING_DECISIONS.md` (decision log & best-practice record), `.agents/skills/coding-rules/` (mandatory engineering standards), `.agents/personal-workflow/` (personal recurring instructions).

---

## 0. How to Read This Document

- Normative requirement keywords use **RFC 2119**: **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**.
- Every **Functional Requirement (FR)** derived from the PRD is mapped to a specification section. See **§24 Traceability Matrix** for the complete PRD → section mapping and the verification checklist.
- Engineering decisions beyond the PRD text are recorded as **Engineering Decisions (ED-xx)** in §9 and must be read together with the PRD.
- This project is a **batch ML pipeline**, not a web service. There is no HTTP API, no relational database, and no request path. "Interfaces" in this SPEC mean the Python ports and the CLI contract (§7), not REST endpoints.

---

## 1. Product Overview

Field agents photograph mobile-recharge outlets to prove each outlet is real, active, and compliant. Over thousands of outlets and months of repeat visits, this produces a sprawling photo archive - and a handful of agents game it by dropping in a photo of a random storefront, an old picture, or something unrelated, just to mark the visit "done." These fakes are impossible to catch by hand at scale.

SPD is a batch pipeline that, given one outlet's accumulated photo history (a folder of images, **no timestamps or visit order**), flags the images that are visually inconsistent with that outlet's overall appearance - without a human looking at most of them.

### 1.1 Problem Statement

> Given a dataset of outlet folders, where each folder contains multiple images captured across different visits for a single outlet (with no date/time metadata provided), build a system that identifies which image(s) in each folder are visually inconsistent with the outlet's overall photo history and should be flagged as suspicious.

### 1.2 Goals

1. For each outlet, compute a per-image **suspicion score ∈ [0,1]** reflecting how anomalous that image is relative to the outlet's own photo history.
2. Flag the small number of genuine outliers per outlet (unrelated scenes, wrong locations, mismatched content) while tolerating **gradual, explainable change** (new signage, repaint, changed counter).
3. Emit a **structured, per-outlet result** following the PRD's output schema - never just raw scores.
4. Make the method **reproducible**: a re-run on the same dataset MUST produce the same flags.
5. Deliver working, runnable pipeline code plus the required justifications and a one-page write-up (PRD "Deliverables").

### 1.3 Dataset (PRD "Dataset" / "Data Structure")

- **Layout:** `dataset/outlet_XXXX/image_NNNN.jpg` - one folder per outlet, many images.
- **Ground truth in this repo:** `data/dataset/` - **159 outlets / 2,042 JPEG images**, resolution **960×1280** (portrait), image counts per outlet range from **5 to 40** (median = 12). The images are street-level photos of retail agent outlets (Bengali mobile-financial-service agent shops, e.g., bKash storefronts): storefront and shutter, branded signage banners, counters/racks, and surrounding street context - consistent with the PRD's "mobile-recharge shop" framing.
- **No metadata:** no capture date, timestamp, or visit order is available; no EXIF is assumed. The method is purely visual/statistical (ED-backed, §10-§11).

### 1.4 Deliverables (PRD "Deliverables")

| # | Deliverable | Spec section |
|---|---|---|
| 1 | Working, runnable pipeline code | §5, §7, FR1, FR2, FR10 |
| 2 | Similarity/scoring method used, with justification | §10, FR3 |
| 3 | Outlier detection rule used, with justification | §11, FR4 |
| 4 | Final results file (JSON/CSV) for the full dataset, per the output schema | §6, FR6 |
| 5 | Short write-up (1 page max): rationale, trade-offs, scalability, limitations | §16, FR9 |

---

## 2. Scope

### 2.1 In Scope (v1)

- Discovery + loading of the outlet/image dataset (no metadata assumptions).
- Image decoding/preprocessing + L2-normalized embedding extraction (model-agnostic).
- Per-outlet similarity scoring and outlier detection with an explainable suspicion score.
- Adaptive, per-outlet flagging with human-readable reasons.
- Structured JSON + CSV output for **every** outlet, schema-validated.
- Optional ranking of all images per outlet (most → least suspicious).
- Reproducibility: fixed seed, deterministic execution, content-addressed embedding cache, pinned dependencies.
- A CLI (`spd`) exposing `run`, `embed`, `detect`, and `report` subcommands.
- The engineering standards in this SPEC (§18-§21).

### 2.2 Non-Goals (v1)

- **MUST NOT** assume timestamps, visit order, or EXIF metadata (PRD "Data Structure").
- **MUST NOT** flag *every* appearance change - only images that stand apart from the outlet's own distribution (gradual change is legitimate).
- **MUST NOT** require labels/supervision - the method is **unsupervised** (no labeled "fake" examples are provided).
- **MUST NOT** depend on a global "outlet template"; consistency is judged **per outlet**, never against a universal prototype.
- **MUST NOT** be a web service, REST API, or long-running daemon. It is a batch CLI pipeline (ED-8).
- **MUST NOT** train or fine-tune a model on the dataset (pretrained features only).

### 2.3 Future Phases (context only, not in scope)

- Incremental/streaming re-scoring as new visit photos arrive (the embedding cache already makes re-runs cheap).
- Active-learning loop that ingests human confirmations of flagged images to tune thresholds.
- A lightweight review UI or exported "needs review" queue for triage teams.
- Multi-GPU / distributed embedding extraction for very large archives.

---

## 3. High-Level Pipeline (PRD "Problem Statement" → "Deliverables")

```
1. Load   → discover outlets + images under the dataset root
2. Embed  → decode + preprocess → L2-normalized embedding per image (cached)
3. Score  → per-outlet pairwise cosine similarity → suspicion signals
4. Detect → fuse signals → suspicion_score ∈ [0,1] → adaptive flag threshold
5. Report → schema-validated OutletResult per outlet → JSON + CSV → write-up
```

The pipeline is **stage-isolated** (ARCHITECTURE §4): each stage reads typed inputs and writes typed outputs; a stage can be re-run independently thanks to the embedding cache (§13).

---

## 4. Functional Requirements

| # | Requirement | Priority | Spec section |
|---|---|---|---|
| FR1 | Discover + load the outlet/image dataset (no metadata assumptions) | Must | §5.1 |
| FR2 | Decode, preprocess, and extract L2-normalized embeddings (model-agnostic) | Must | §5.2, §10 |
| FR3 | Compute per-outlet similarity + suspicion signals (scoring method + justification) | Must | §5.3, §10 |
| FR4 | Apply the outlier detection rule and flag suspicious images (rule + justification) | Must | §5.4, §11 |
| FR5 | Emit a human-readable `reason` per flagged image | Must | §5.5, §11.4 |
| FR6 | Emit the structured per-outlet result for the full dataset (JSON + CSV, every outlet) | Must | §5.6, §6 |
| FR7 | Provide optional `ranking` (all images, most → least suspicious) | Should | §5.7, §6 |
| FR8 | Reproducibility: seeded, deterministic, cached embeddings, pinned deps | Must | §5.8, §13 |
| FR9 | One-page write-up: rationale, trade-offs, scalability, limitations | Must | §5.9, §16 |
| FR10 | Runnable CLI (`spd`) with `run`/`embed`/`detect`/`report` subcommands | Must | §5.10, §7 |

Detailed behavior for each FR lives in the sections referenced above. Acceptance is verified through the Phase Gates and Release Checklist in `docs/PLANNING.md` (§3-§4, §8) and the Definition of Done (§23); test practice follows `.agents/skills/coding-rules/test-runner/SKILL.md`.

---

## 5. System Behavior Specifications (FR details)

### 5.1 Dataset Discovery & Loading (FR1)

- Discover outlet folders as immediate children of the dataset root; an image is any file with a supported extension (`.jpg`, `.jpeg`, `.png`).
- The outlet identifier is the **folder name** (`outlet_id`); image identity is the **file name** (`file_name`).
- No ordering is imposed; no timestamp/EXIF is read. Image order in any list MUST NOT affect results (sorting is deterministic by file name for reproducibility only).
- Unreadable/corrupt images MUST be reported with a clear error (outlet, file, cause) and MUST NOT silently bias the result; the default policy is to **fail the run** unless `IGNORE_CORRUPT_IMAGES` is set (config, §22).
- An outlet with **fewer than `MIN_IMAGES_PER_OUTLET`** images (default 2) has no reference distribution to compare against; it MUST be returned with an empty `flagged_images` and a `total_images` reflecting what was evaluated (§6).

### 5.2 Embedding Extraction (FR2)

- Decode each image, resize to the model's canonical input size (letterboxing/padding per adapter), and normalize pixel values per the adapter's preprocessing contract.
- Extract an embedding via the **`Embedder` port** (Strategy, ED-1); default adapter is **DINOv2 ViT-S/14** (384-dim), CLIP is an alternate adapter. Feature code never imports a model's weights directly.
- Every embedding is **L2-normalized** so cosine similarity is a dot product (ED-2).
- Embeddings are **content-addressed**: keyed by a hash of the decoded image bytes + model + model version (ED-6, §13). A re-run reuses cached vectors.

### 5.3 Similarity & Scoring (FR3)

See §10 (specification) and §12 (edge cases). Produces, per outlet with N images:
- an `N × N` cosine-similarity matrix `S`,
- three per-image suspicion signals: **centroid distance**, **kNN consensus**, **isolation-forest anomaly score** (ED-4).

### 5.4 Outlier Detection & Flagging (FR4)

See §11. Fuses the three signals into a single `suspicion_score ∈ [0,1]`, then applies an **adaptive per-outlet threshold** (`median + k·MAD` with an absolute floor, ED-5). Images exceeding the threshold become `flagged_images`.

### 5.5 Reason Generation (FR5)

Each flagged image carries a short, human-readable `reason` derived from **which signal fired** and **why** (templated, deterministic). Examples: `"Low similarity to cluster centroid"`, `"Distinct background/signage compared to the rest of the series"`, `"Few nearby neighbours in feature space"`, `"Isolated in feature space (Isolation Forest)"`. See §11.4.

### 5.6 Structured Output (FR6)

See §6. Emits one `OutletResult` per outlet for **every** outlet in the dataset, written as both JSON and CSV. Outlets with no flagged images are returned with an **empty** `flagged_images` list - never omitted.

### 5.7 Ranking (FR7)

When enabled, `ranking` lists all of the outlet's `file_name`s ordered **most → least suspicious** (ties broken deterministically by file name). Always includes every image, independent of whether it was flagged.

### 5.8 Reproducibility (FR8)

- Fixed global seed (`RANDOM_SEED`, default 42) for every stochastic component (Isolation Forest).
- Deterministic ordering everywhere (sorted file traversal, stable ties).
- Content-addressed embedding cache (§13) so identical images yield identical vectors.
- Dependencies pinned; same dataset + same config ⇒ byte-identical results.

### 5.9 Write-up (FR9)

A one-page (max) markdown report under `results/` covering: chosen similarity/scoring method + justification, chosen outlier rule + justification, scalability analysis, and known limitations. See §16.

### 5.10 CLI (FR10)

`spd` subcommands (all config-driven, §22):

- `spd run` - full pipeline (load → embed → score → detect → report).
- `spd embed` - extract + cache embeddings only.
- `spd detect` - score + detect from cached embeddings only.
- `spd report` - regenerate JSON/CSV + write-up from cached results.

---

## 6. Data & Output Schema

### 6.1 Output schema (PRD "Expected Output Format" - hard contract)

Validated at the boundary by strict Pydantic models (`extra="forbid"`); any out-of-contract value fails the run rather than being silently emitted (ED-7).

**Per-outlet record:**

| Field | Type | Description |
|---|---|---|
| `outlet_id` | string | Identifier of the outlet folder |
| `total_images` | integer | Number of images evaluated in the folder |
| `flagged_images` | list | One entry per suspicious image (**empty if none**) |
| `ranking` (optional) | list | All images ordered most → least suspicious |

**Each `flagged_images` entry:**

| Field | Type | Description |
|---|---|---|
| `file_name` | string | Name of the flagged image |
| `suspicion_score` | float | Normalized anomaly score ∈ [0,1]; higher = more anomalous |
| `reason` | string | Short human-readable explanation of the flag |

```json
{
  "outlet_id": "outlet_0001",
  "total_images": 6,
  "flagged_images": [
    {
      "file_name": "img_04.jpg",
      "suspicion_score": 0.87,
      "reason": "Distinct background and signage compared to the rest of the series"
    }
  ],
  "ranking": ["img_04.jpg", "img_02.jpg", "img_01.jpg", "img_03.jpg", "img_05.jpg", "img_06.jpg"]
}
```

- `suspicion_score` is **always** clamped to `[0,1]` and rounded to a fixed number of decimal places (default 4) for stable output.
- `total_images` counts images **evaluated** (after any corrupt-image filtering), not raw file count.
- Every outlet in the dataset MUST appear exactly once in the results.

### 6.2 Core entities (typed, in-memory - no database)

- **Outlet** - `outlet_id`, collection of `ImageRecord`s.
- **ImageRecord** - `file_name`, `path`, `content_hash`, optional `Embedding`.
- **Embedding** - `vector` (numpy `ndarray`), `model`, `model_version`, `content_hash`, `dim`.
- **SuspicionProfile** - per-image signals: `centroid_distance`, `knn_consensus`, `isolation_forest`, `fused_score`.
- **OutletResult** - the §6.1 record (output schema).
- **FlaggedImage** - `file_name`, `suspicion_score`, `reason`.

These are the pipeline's **currency** (SYSTEM_DESIGN §1). There is no relational schema: persistence is limited to the embedding cache and the results files.

---

## 7. CLI Contract (FR10)

- `spd run --dataset <path> --output <dir>` - full pipeline.
- `spd embed --dataset <path>` - embeddings only.
- `spd detect --dataset <path>` - scoring + detection from cache.
- `spd report --output <dir>` - JSON/CSV + write-up from cached results.
- Global flags: `--config <path>`, `--model <name>`, `--device <cpu|cuda|mps|auto>`, `--seed <int>`, `--verbose`.
- Exit codes: `0` success; `2` invalid usage/config; `1` runtime failure. Errors are structured, single-line, and never leak secrets or absolute image paths beyond what is needed.

---

## 8. Non-Functional Requirements

| Area | Requirement |
|---|---|
| **Correctness** | Scores strictly ∈ [0,1]; ranking covers all images; flagged ⊆ evaluated; every outlet present (§6.1). |
| **Robustness** | Method must not mis-flag legitimate multi-cluster outlets (front vs interior shots) or gradual change (§12). |
| **Reproducibility** | Deterministic output; content-addressed cache; pinned deps (ED-6). |
| **Performance** | Full dataset (159 outlets / 2,042 images) runs comfortably on CPU in minutes; embeddings cached for incremental re-runs (§15). |
| **Scalability** | Linear in image count; embeddings computed once and reused; O(N²) pairwise work is bounded per outlet (§15). |
| **Observability** | Structured logs + per-stage timing + run summary (KPIs, §14). |
| **Config** | Single `settings.py` + `.env`; no magic numbers/paths in feature code (§18). |
| **Security** | No secrets in code/logs; dataset treated as untrusted input (§17). |

---

## 9. Engineering Decisions

The PRD leaves the method open ("Similarity/scoring method used" and "Outlier detection rule used" are deliverables, not prescriptions). This section records the Tech Lead's decisions. A narrative record of decisions and the best practices behind them lives in `docs/ENGINEERING_DECISIONS.md`; this table is the normative registry.

| ID | Topic | PRD source | Decision / Disposition |
|---|---|---|---|
| ED-1 | Embedding model | "Similarity/scoring method" | **Engineering decision:** a model-agnostic `Embedder` port (Strategy). Default **DINOv2 ViT-S/14** (self-supervised ViT, 384-dim) - strong instance/scene discriminability, illumination/angle robustness, small + fast. **CLIP** (semantic) as an alternate adapter. Switching is a config change, never a code change. |
| ED-2 | Similarity metric | "Similarity/scoring method" | **Cosine similarity on L2-normalized embeddings** - scale/illumination invariant, standard for high-dim visual features. |
| ED-3 | Reference prototype | "Outlier detection rule" | **Robust centroid = coordinate-wise median** of the outlet's L2-normalized embeddings (re-normalized) - resistant to outlier contamination, unlike the mean. |
| ED-4 | Detection ensemble | "Outlier detection rule" | **Three complementary signals fused** into one score: (a) centroid distance, (b) kNN consensus (local density - handles multi-cluster outlets), (c) Isolation Forest anomaly score. Each signal catches a different failure mode. |
| ED-5 | Flag threshold | "Outlier detection rule" | **Adaptive, per-outlet, distribution-free threshold** `τ = median(score) + k·MAD(score)` plus an absolute floor - no global threshold, robust to outlet-to-outlet variation. |
| ED-6 | Reproducibility | "Deliverable: working pipeline" | Fixed seed, deterministic ordering, **content-addressed embedding cache**, pinned deps. Re-run ⇒ identical flags. |
| ED-7 | Output schema | "Expected Output Format" | Strict Pydantic models (forbid extra, parse-don't-validate); schema is a hard contract, never best-effort JSON. |
| ED-8 | Architecture | "Deliverable: working pipeline" | **Batch CLI pipeline, not a web service.** No DB, no Redis, no API. Typed in-memory entities + file-based embedding cache. Flat `src/` layout (top-level packages under `src/`). |
| ED-9 | Detector swappability | "Outlier detection rule" | Detection rules behind an `OutlierDetector` Strategy port - individual signals and the fusion can be swapped/re-weighted via config (ED-4 default). |
| ED-10 | Multi-cluster robustness | "gradual, explainable change" | kNN local-density signal ensures legitimately different angle/visit photos (multiple true clusters) are not mis-flagged by a single global centroid. |

---

## 10. Similarity & Scoring Specification (FR3, deliverable #2)

### 10.1 Embedding

- Adapter: DINOv2 ViT-S/14 (default) via `torchvision`; CLIP via `open_clip_torch` (alternate). Selected by config (§22).
- Output: L2-normalized vector `e_i ∈ R^d` per image (`d = 384` for DINOv2-S).
- Deterministic: inference-only, `torch.no_grad()`, eval mode, fixed device/seed.

### 10.2 Pairwise similarity

- `S_ij = e_i · e_j` (cosine, since L2-normalized), `S ∈ [-1,1]^N×N`, diagonal excluded.

### 10.3 Suspicion signals

- **Centroid distance** (`s_centroid`): `1 - e_i · ĉ`, where `ĉ` is the re-normalized coordinate-wise median of the outlet's embeddings (ED-3). Captures "far from the outlet's typical appearance."
- **kNN consensus** (`s_knn`): `1 - mean_k( top-k S_ij )` with `k = min(5, N-1)` - the mean similarity to the k nearest neighbours. Captures local density; robust when an outlet has several true clusters (ED-10).
- **Isolation Forest** (`s_if`): fit per outlet on the raw (or PCA-reduced) embeddings; the anomaly score normalized to `[0,1]` via min-max over the outlet. Captures general multivariate isolation structure.

### 10.4 Fusion

`suspicion_score = w_c·s_centroid + w_k·s_knn + w_if·s_if`, weights configurable (default equal, `w = 1/3` each), clamped to `[0,1]`. For small outlets (`N < MIN_IMAGES_FOR_IF`, default 10) the Isolation Forest weight is reduced toward 0 (its scores are unstable at low `N`), so centroid + kNN dominate where they are most reliable.

---

## 11. Outlier Detection Specification (FR4, deliverable #3)

### 11.1 Rule

For each outlet, compute the fused `suspicion_score` for every image, then flag image `i` iff:

`suspicion_score(i) > max( median(scores) + k·MAD(scores), SCORE_FLOOR )`

where `MAD = median(|score - median(scores)|)` (scaled by `1.4826` for a normal-consistent estimator). Parameters `k` (default `3.0`) and `SCORE_FLOOR` (default `0.5`) are config (§22).

### 11.2 Justification (summary - full write-up in `docs/ENGINEERING_DECISIONS.md`)

- **Ensemble over single metric:** each signal alone has a blind spot - centroid distance is confused by multi-cluster outlets, kNN is insensitive to a small tight clique of fakes, Isolation Forest is unstable in low `N`. Fusing three complementary signals raises precision without labels.
- **Adaptive threshold:** outlet appearance variance differs wildly across outlets; a global threshold is wrong. A robust `median + k·MAD` threshold is distribution-free, outlier-resistant, and needs no tuning per outlet.
- **Absolute floor:** prevents degenerate over-flagging when an outlet is nearly uniform (all scores ≈ 0).

### 11.3 Edge cases

- **N < 2:** no comparison possible → empty `flagged_images`.
- **Perfectly uniform outlet (all images identical):** all scores ≈ 0; floor prevents flagging noise-level differences.
- **A tight clique of ≥ 3 fakes:** Isolation Forest + kNN flag the clique; centroid distance may miss it - hence the ensemble.
- **Single different-angle-but-legit cluster:** kNN consensus stays low only for true isolates; a well-populated second cluster is not flagged (ED-10).
- **Small outlet (N ≈ 3-5):** all signals are noisy; the Isolation Forest contribution is down-weighted (or disabled) below `MIN_IMAGES_FOR_IF`, and the MAD floor keeps flagging conservative.

### 11.4 Reason generation (FR5)

Deterministic templates chosen by the **dominant** signal(s), e.g.:
- centroid-dominant → `"Low similarity to cluster centroid"`
- kNN-dominant → `"Few nearby neighbours in feature space"`
- IF-dominant → `"Isolated in feature space (Isolation Forest)"`
- centroid + kNN → `"Distinct background/signage compared to the rest of the series"`

---

## 12. Scoring Semantics & Robustness Invariants

- **Score direction:** `0` = fully consistent with the outlet; `1` = maximally anomalous. `suspicion_score` MUST always be ∈ `[0,1]`.
- **Gradual change is legitimate:** scores track *relative* deviation within the outlet's own distribution, so a uniformly-shifted appearance (everyone changed together) produces low scores - only the odd image stands out.
- **No global template:** an outlet is compared to itself, never to a universal "outlet" prototype.
- **Order independence:** the result is invariant to file traversal order (deterministic sort).
- **Scale/illumination invariance:** inherited from L2 normalization + cosine similarity.

---

## 13. Embedding Cache & Reproducibility (FR8, ED-6)

- **Content-addressed cache:** key = `sha256(decoded image bytes) + model + model_version`. Values are the normalized embedding vectors, stored in a compact format (Parquet or `.npy` under `CACHE_DIR`).
- **Cache semantics:** a hit returns the stored vector without re-running the model; a miss computes, stores, and returns it. The cache is transparent - results are identical with a cold or warm cache.
- **Invalidation:** the model + version are part of the key; changing model or weights produces a distinct key namespace, so stale vectors are never mixed (ED-6).
- **Resumability:** `spd embed` can be interrupted and resumed; `spd detect` reads only from cache.
- **Determinism:** fixed seed, deterministic sort, `eval()` + `no_grad()` inference, stable float rounding on output.
- **Optional CLIP path:** the `clip` extra is not part of the locked core environment; a CLIP run MUST first compile its own lockfile (`uv pip compile --extra clip`) so the open_clip weights + torch pairing stay pinned (ED-6). See `pyproject.toml` `[project.optional-dependencies] clip`.

---

## 14. Observability, Logging & KPIs

Per `.agents/skills/coding-rules/logging-and-tracing/SKILL.md` and `.agents/skills/coding-rules/observability/SKILL.md`:

- **structlog** with a single `get_logger` factory; no ad-hoc `print` or per-module logging config.
- Context fields: `run_id`, `outlet_id`, `stage`, `image_count`, `device`, `model`, `model_version`.
- **Never log** image byte content or any secrets. Log hashes/counts instead.
- Per-stage timing and a run summary: total images, cache hits/misses, embeds/sec, outlets flagged, total flagged images, wall-clock per stage.
- A JSON run summary is written to `results/run_summary.json` for the write-up and for regression comparisons.

---

## 15. Performance & Scaling

- **Embedding:** batched (configurable `BATCH_SIZE`, default 32) on GPU when available, CPU otherwise; `torch.no_grad()` + `eval()`. Embeddings computed once, cached (§13).
- **Pairwise:** O(N²) cosine per outlet; `N ≤ ~40` in the provided dataset, so this is negligible. For very large outlets, an approximate-NN or chunked path MAY be added (documented as a future consideration).
- **Memory:** full dataset embeddings are ~2,042 × 384 floats ≈ 3.1 MB - trivially in memory. Cache is disk-backed.
- **Incremental re-runs:** a second run with the same dataset is essentially free (all embeddings cached); only scoring/detection recompute.

---

## 16. Evaluation, Validation & Write-up (FR9, deliverable #5)

- **Synthetic golden set:** generate synthetic outlets with known injected outliers (unrelated images inserted into a consistent outlet) to measure **precision/recall/F1** of flagging. This is the primary quality gate (no labeled real data exists).
- **Stability checks:** re-run twice → byte-identical results; cache cold vs warm → identical results.
- **Qualitative review:** inspect a sample of flagged images from the real dataset to sanity-check that flags are genuine inconsistencies (documented in the write-up).
- **Write-up (1 page max):** rationale for the chosen method + rule, trade-offs, scalability analysis, and known limitations (e.g., "cannot distinguish a legitimate remodel from a fake if it is a one-off, sharp change; multi-cluster handling relies on local density; Isolation Forest needs N ≥ some minimum").

---

## 17. Security & Data Handling

- The dataset is **untrusted input**: image files are decoded with bounds checks; corrupt/malformed files are rejected with a clear error (§5.1).
- No secrets, keys, or tokens are needed or stored; `.env` is gitignored, `.env.example` holds placeholders only.
- `data/dataset/` is gitignored (large binary assets); the pipeline reads from `data/dataset/` by default.
- Logs never emit image bytes or absolute filesystem paths beyond the outlet/file name needed for diagnosis.

---

## 18. Configuration Management (per `.agents/skills/coding-rules/config-management/SKILL.md`)

- **Single source of truth:** central `settings.py` (Pydantic Settings) merges committed non-secret tunables with `.env`-loaded values. No other module reads env directly.
- **Non-secret tunables (in `settings.py`, committed):** dataset path, output dir, cache dir, model name, `device`, `batch_size`, `random_seed`, `k_neighbors`, `mad_k`, `score_floor`, fusion weights, `min_images_per_outlet`, `ignore_corrupt_images`, rounding precision, write-up length cap.
- **Secrets (`.env`, never committed):** none required for v1. Reserved for optional future remote model hubs; placeholders documented in `.env.example`.

---

## 19. Design Patterns (per `.agents/skills/coding-rules/design-patterns/SKILL.md`)

| Pattern | Where used | Rationale |
|---|---|---|
| **Strategy** | `Embedder` (DINOv2/CLIP); `OutlierDetector` (centroid/kNN/IF fusion); scoring signals | Swappable algorithms selected by config |
| **Adapter** | Model backends → the `Embedder` port | Thin translation of torch/torchvision/open_clip |
| **Factory** | `create_embedder(name)`, `create_detector(name)` | Decouple callers from concrete adapters |
| **Template Method** | `PipelineStage.run()` skeleton with per-stage hooks (preprocess/execute/postprocess) | Shared stage lifecycle, uniform timing/logging |
| **Builder** | `OutletResult` assembly; write-up composition | Many optional parts, validate before terminal build |
| **Facade** | `PipelineRunner` facade over load/embed/score/detect/report | Simple entry point over the staged subsystem |

Patterns are applied only where they solve a present problem (YAGNI).

---

## 20. Coding Standards & Best Practices (from `.agents/skills/coding-rules/`)

Incorporated by reference - mandatory. Summary of the key rules:

| Area | Rule |
|---|---|
| **Docstrings** | Every public module/class/function/method/complex type has a PEP 257 docstring (WHAT + WHY); no comments on the obvious; no commented-out code. |
| **Naming** | `snake_case` modules/functions/vars, `PascalCase` classes, `UPPER_SNAKE_CASE` constants/enums, `is_/has_/can_/should_` booleans, no abbreviations/camelCase/single-letter vars. |
| **Type safety** | Pydantic strict schemas at every boundary (config, output schema, result parsing); `extra="forbid"`; enums for bounded sets. |
| **Error handling** | Custom exception classes; handle/wrap/propagate; never swallow; clear structured messages. |
| **Config** | §18. |
| **Dependencies** | Locked; prod vs dev separated; `pip-audit`/`trivy` in CI. |
| **Tests** | Unit + integration; deterministic; behavior not implementation; coverage ≥ 85% core / ≥ 80% overall. |
| **Complexity** | No quadratic hot paths beyond the bounded per-outlet O(N²); vectorized numpy/scipy. |
| **Git & PR** | Conventional Commits; `type/scope` branches; squash merge; update `docs/CHANGELOG.md` + `docs/ARCHITECTURE.md` in the same PR. |
| **Dead code** | `ruff`/`vulture` clean. |
| **Alignment** | `.agents/skills/coding-rules/alignment-checker/SKILL.md` + `verify-alignment/SKILL.md` before merge. |

**Mandatory tooling:** `ruff` (lint + format), `mypy`/`pyright`, `pytest` + coverage, `bandit`, `pip-audit`/`trivy`, `vulture`, pre-commit hooks, CI pipeline.

---

## 21. Testing Strategy

- **Unit tests:** scoring (cosine, centroid, kNN), fusion/clamping, MAD threshold + floor, reason templates, output-schema validation (forbid-extra, score bounds), config validation, cache key derivation.
- **Integration tests:** full pipeline on a tiny synthetic fixture (a consistent outlet + an injected unrelated image) → asserts the outlier is flagged with the right reason; JSON/CSV round-trip; ranking completeness; empty-flag case.
- **Determinism tests:** two runs → identical output; cold vs warm cache → identical output.
- **Property tests:** score ∈ [0,1]; ranking covers all images; flagged ⊆ evaluated; every outlet present exactly once.
- **Quality gate:** synthetic-golden precision/recall/F1 above configured thresholds (PLANNING §8).

---

## 22. Configuration Catalog (initial)

### 22.1 Model & embedding
- `EMBEDDING_MODEL` = `dino_v2_small` (default) | `clip`; `EMBEDDING_DIM` = 384; `DEVICE` = `auto`.

### 22.2 Scoring & detection
- `SIMILARITY_METRIC` = `cosine`; `K_NEIGHBORS` = 5; `MAD_K` = 3.0; `SCORE_FLOOR` = 0.5; fusion weights `(1/3, 1/3, 1/3)`; `MIN_IMAGES_FOR_IF` = 10.

### 22.3 Dataset & output
- `DATASET_DIR` = `data/dataset`; `OUTPUT_DIR` = `results`; `CACHE_DIR` = `cache/embeddings`; `MIN_IMAGES_PER_OUTLET` = 2; `IGNORE_CORRUPT_IMAGES` = false; `SCORE_DECIMALS` = 4.

All values live in `settings.py` (overridable by env where environment-specific) - never hardcoded in feature code.

---

## 23. Definition of Done (per feature)

1. Code implements the FR + acceptance criteria with full docstrings and WHY comments (§20).
2. Unit + integration tests written, deterministic, passing; coverage thresholds met.
3. Lint, type-check, dead-code, dependency-scan gates pass in CI.
4. Spec/architecture alignment verified (`alignment-checker`, `verify-alignment`).
5. Reproducibility verified (determinism + cache tests, §21).
6. Output validated against the §6.1 schema.
7. `docs/CHANGELOG.md` and, where structure changed, `docs/ARCHITECTURE.md` updated in the same PR.
8. Security review (untrusted-input handling, no secrets) passed.

---

## 24. Traceability Matrix & Coverage Verification

| PRD requirement | SPEC section(s) | Covered? |
|---|---|---|
| Context / problem narrative | §1 | ✅ |
| Problem Statement (flag visually inconsistent images, no metadata) | §1.1, §3 | ✅ |
| Data Structure (one folder = one outlet, no timestamps, gradual change, few outliers) | §1.3, §5.1, §12 | ✅ |
| Expected Output Format (per-outlet record + flagged_images fields) | §6.1 | ✅ |
| Every outlet returned, empty flagged_images when none | §5.6, §6.1 | ✅ |
| Deliverable 1 - working, runnable pipeline code | §5, §7, FR1/FR2/FR10 | ✅ |
| Deliverable 2 - similarity/scoring method + justification | §10, FR3 | ✅ |
| Deliverable 3 - outlier detection rule + justification | §11, FR4 | ✅ |
| Deliverable 4 - final results file (JSON/CSV), full dataset | §6, FR6 | ✅ |
| Deliverable 5 - 1-page write-up | §16, FR9 | ✅ |
| Tech Lead adds: model-agnostic embedder | §10.1, ED-1 | ✅ |
| Tech Lead adds: detector swappability | §9, ED-9 | ✅ |
| Tech Lead adds: reproducibility/cache | §13, ED-6 | ✅ |
| Tech Lead adds: batch CLI architecture | §7, ED-8 | ✅ |
| Tech Lead adds: docstrings/comments mandatory | §20 | ✅ |
| Tech Lead adds: coding rules incorporated | §20 | ✅ |

**Verification procedure:** before every release, run the matrix above; any gap = release blocker.
