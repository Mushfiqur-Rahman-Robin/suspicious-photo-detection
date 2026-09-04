# ENGINEERING DECISIONS - Suspicious Photo Detection (SPD) - v1

**Suspicious Photo Detection in Outlet Verification Images.**

- **Status:** Authoritative decision log (ADR-style) + best-practice record.
- **Source of truth:** `project_docs/AI_Engineer_Assignment_Suspicious_Photo_Detection_PRD.pdf`. PRD wins over this document and `docs/SPEC.md` unless an Engineering Decision (ED-xx) is recorded here and registered in SPEC §9.
- **Companion docs:** `docs/SPEC.md` (§9 is the normative ED-xx registry), `docs/ARCHITECTURE.md`, `docs/PLANNING.md`, `docs/SYSTEM_DESIGN.md`.
- **Convention:** decisions use RFC 2119 (MUST/SHOULD/MAY); each entry records Context → Decision → Rationale → Consequences. ED-xx IDs here are identical to those in SPEC §9.

---

## 1. Purpose & Scope

This document records (a) the engineering decisions that shape the system and (b) the best practices maintained to keep `docs/SPEC.md` and the wider document set aligned with the PRD. It is the narrative companion to the normative ED-xx registry in SPEC §9. Where this document and SPEC §9 disagree, **SPEC §9 wins**.

## 2. Governance Model

- **Product source of truth:** `project_docs/AI_Engineer_Assignment_Suspicious_Photo_Detection_PRD.pdf`. The PRD wins over every other artifact unless an approved ED-xx extends it.
- **Normative technical spec:** `docs/SPEC.md`. Every decision MUST be registered in SPEC §9 (ED-xx) before it is acted on in code or diagrams.
- **This document:** rationale, best practices, and consequences behind each ED-xx.
- **Traceability:** each decision references the PRD deliverable it addresses and the SPEC section it affects; SPEC §24 is the coverage matrix.

## 3. Best-Practice Guardrails (non-negotiable)

| ID | Best practice | Enforced by |
|---|---|---|
| BP-1 | Single source of truth (PRD); no artifact may contradict it | SPEC §0, §24 |
| BP-2 | Decisions are normative and registered (never implicit) | SPEC §9, this doc |
| BP-3 | Output schema is a hard, validated contract | SPEC §6, ED-7 |
| BP-4 | Reproducibility is a designed-in invariant | SPEC §13, ED-6 |
| BP-5 | Model-agnostic embedding layer; no model weights in feature code | SPEC §10.1, ARCH §3, ED-1 |
| BP-6 | Non-secret config in `settings.py`; secrets only in `.env` | SPEC §18 |
| BP-7 | Diagrams regenerated from committed `.mmd` sources | SYSTEM_DESIGN §0 |
| BP-8 | Method is unsupervised and per-outlet (no global template, no labels) | SPEC §2.2, §12, ED-4/ED-5 |
| BP-9 | One canonical stage order across every artifact | SPEC §3, ARCH §6, SYSTEM_DESIGN §3 |
| BP-10 | No stale cross-references; cite the current artifact | SYSTEM_DESIGN §1.1 |

## 4. Decision Log (ADR)

### ED-1 - Embedding model: DINOv2 default, model-agnostic

- **Status:** Accepted.
- **Context:** PRD asks for a "similarity/scoring method" without prescribing one.
- **Decision:** A model-agnostic `Embedder` port (Strategy). Default **DINOv2 ViT-S/14** (384-dim, `torchvision`); **CLIP** (`open_clip_torch`) as alternate. Feature code never imports weights.
- **Rationale (BP-5):** DINOv2 is self-supervised and produces highly discriminative instance/scene features - well suited to "same outlet vs different outlet" matching, robust to illumination/angle change, and small/fast (CPU-friendly). Keeping the layer swappable future-proofs the method as better backbones appear.
- **Consequences:** `embedding/` owns all model access; switching models is a config change.

### ED-2 - Similarity metric: cosine on L2-normalized embeddings

- **Status:** Accepted.
- **Context:** Choose a similarity that is robust to capture variation.
- **Decision:** L2-normalize every embedding and use cosine similarity (dot product).
- **Rationale:** Scale/illumination invariance for high-dim visual features; standard and cheap (vectorized dot products).
- **Consequences:** all signals in §10.3 are defined on cosine distances.

### ED-3 - Robust centroid: coordinate-wise median

- **Status:** Accepted.
- **Context:** The outlet's "reference appearance" must not be dragged toward an outlier.
- **Decision:** Reference prototype = coordinate-wise median of L2-normalized embeddings, re-normalized.
- **Rationale:** The mean is not breakdown-resistant - a single fake shifts it; the median tolerates outlier contamination, keeping the reference faithful to the true outlet.
- **Consequences:** centroid distance signal stays meaningful even with a few outliers present.

### ED-4 - Detection ensemble: centroid + kNN + Isolation Forest

- **Status:** Accepted.
- **Context:** Each single metric has a blind spot (centroid confused by multi-cluster outlets; kNN misses a tight clique of fakes; IF unstable at low N).
- **Decision:** Compute three signals and fuse them (weighted average, default equal weights) into one `suspicion_score ∈ [0,1]`.
- **Rationale (BP-8):** no labels exist, so precision must come from corroboration of independent signals, not from tuning a single metric on unlabeled data.
- **Consequences:** each signal is a separable, unit-testable component; fusion weights are config.

### ED-5 - Adaptive, per-outlet, distribution-free threshold

- **Status:** Accepted.
- **Context:** Outlet appearance variance differs across outlets; a global threshold is provably wrong.
- **Decision:** `τ = max(median(score) + k·MAD(score), SCORE_FLOOR)` with `k=3.0`, `SCORE_FLOOR=0.5`.
- **Rationale (BP-8):** MAD is distribution-free and outlier-resistant; no per-outlet tuning; the absolute floor stops over-flagging in near-uniform outlets.
- **Consequences:** flagging is fully automatic and consistent across outlets.

### ED-6 - Reproducibility: seed + content-addressed cache + pinned deps

- **Status:** Accepted.
- **Context:** A hiring artifact that changes flags between runs is untrustworthy.
- **Decision:** Fixed seed, deterministic ordering, content-addressed embedding cache (`sha256(bytes) + model + version`), pinned dependencies.
- **Rationale (BP-4):** reproducibility must be designed in, not asserted after the fact.
- **Consequences:** cold vs warm cache yields identical results; determinism is property-tested (SPEC §21).

### ED-7 - Output schema: strict Pydantic contract

- **Status:** Accepted.
- **Context:** PRD "Expected Output Format" is a hard contract.
- **Decision:** Strict Pydantic models (`extra="forbid"`, parse-don't-validate), score clamped to `[0,1]` and rounded; every outlet present exactly once.
- **Rationale (BP-3):** the result file is the deliverable reviewers read first; it must be machine-validatable and never best-effort.
- **Consequences:** invalid output fails the run rather than being silently emitted.

### ED-8 - Architecture: batch CLI pipeline, flat src layout, no DB

- **Status:** Accepted.
- **Context:** The problem is a batch job over 159 outlets.
- **Decision:** A deterministic CLI (`spd`) composed of bounded stages; typed in-memory entities + a file-based embedding cache; no database/Redis/API.
- **Rationale:** a server/database would be pure overhead; stage isolation + cache give resumability and testability for free.
- **Consequences:** persistence is limited to the cache and results files; modules are strictly bounded (ARCH §4).

### ED-9 - Detector swappability (Strategy port)

- **Status:** Accepted.
- **Context:** Different datasets may warrant different detectors.
- **Decision:** Detection rules behind an `OutlierDetector` Strategy port; individual signals and fusion weights config-swappable.
- **Rationale:** keeps the method adaptable without rewriting the pipeline.
- **Consequences:** `create_detector(name)` factory; alternate rules (e.g., LOF) can be added as new adapters.

### ED-10 - Multi-cluster robustness (kNN local density)

- **Status:** Accepted.
- **Context:** An outlet legitimately photographed from different angles (front, interior, signage) may form multiple true clusters; a single global centroid would mis-flag the smaller one.
- **Decision:** Include a kNN local-density signal so only true isolates are flagged, not members of a well-populated second cluster.
- **Rationale (BP-8):** distinguishes "different but legitimate" from "inconsistent."
- **Consequences:** the kNN signal is mandatory in the ensemble; tested with synthetic multi-cluster fixtures.

## 5. Alignment Pass Record (docs ↔ PRD/SPEC sync)

| Fix | Artifact(s) | Best practice |
|---|---|---|
| Derive FR1-FR10 from the PRD deliverables + output schema | SPEC §4, §24 | BP-1 |
| Pin the method (embedding/similarity/rule) as ED-1…ED-5 instead of leaving it open | SPEC §9-§11, this doc | BP-2 |
| Output schema as strict Pydantic (forbid-extra, score bounds) | SPEC §6, SYSTEM_DESIGN §1.1 | BP-3 |
| Reproducibility as a first-class invariant | SPEC §13, ARCH §3 | BP-4 |
| Stage order made canonical across SPEC/ARCH/SYSTEM_DESIGN | SPEC §3, ARCH §6, SYSTEM_DESIGN §3 | BP-9 |
| Diagram sources committed as `.mmd` alongside `.svg` | `docs/assets/*.mmd` | BP-7 |
| Create this log + wire into nav/reading order | this doc, `mkdocs.yml`, `index.md`, `README.md`, `AGENTS.md`, SPEC §0, ARCH §0 | BP-2 |
