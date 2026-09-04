# PLANNING - Suspicious Photo Detection (SPD) - v1

**Suspicious Photo Detection in Outlet Verification Images.**

- **Version:** 1.0.0
- **Status:** Approved for execution
- **Related docs:** `docs/SPEC.md` (what we build), `docs/ARCHITECTURE.md` (how it fits together), `project_docs/Suspicious_Photo_Detection_PRD.pdf` (source of truth). All engineering standards in `.agents/skills/coding-rules/` apply.

---

## 1. Delivery Overview

- **Target:** ~2 days of focused work, delivered in six phases with quality gates. Day 1 covers Phases 0-2 (foundations, embedding, scoring); Day 2 covers Phases 3-5 (detection, pipeline/CLI/output, validation/hardening). See §5.
- **Goal:** deliver the v1 suspicious-photo-detection pipeline per `docs/SPEC.md`, fully covered by tests, plus the five PRD deliverables (code, scoring justification, outlier-rule justification, full results file, one-page write-up).
- **Working principle:** ship early, ship often; quality gates are non-negotiable - this submission is the hiring artifact.
- **Scope guard:** this plan builds the **pipeline only**. No web service, no database, no labeled-data fine-tuning (SPEC §2.2).
- **Non-negotiable constraints (from Tech Lead):**
  - Docstrings and WHY-comments on all code - every public module/class/function (SPEC §20).
  - Model-agnostic embedding layer (DINOv2 default; CLIP switchable via config).
  - Ensemble outlier detection (centroid + kNN + Isolation Forest) behind a Strategy port.
  - Adaptive, per-outlet, distribution-free flag threshold.
  - Reproducibility: fixed seed + content-addressed embedding cache + pinned deps.
  - Config from `settings.py`, secrets from `.env`.
  - All coding-rules gates green before merge.

---

## 2. Team & Roles

| Role | Responsibility |
|---|---|
| Tech Lead / Sr. AI Engineer | Spec/architecture authority, design decisions (ED-xx), implementation, final alignment gate |
| Reviewer | Independent code review + alignment/verify gates before merge (SPEC §20) |

*(Single-engineer effort; the Reviewer role is exercised as a self-review pass plus the `alignment-checker` / `verify-alignment` skill gates.)*

---

## 3. Milestones & Phase Gates

Each phase ends with a **Phase Gate** (Definition of Done per `docs/SPEC.md` §23). No phase is complete without lint, type-check, tests, and coverage gates passing.

### Phase 0 - Foundations (repo, config, docs, CI)
- Finalize `docs/` (SPEC, ARCHITECTURE, SYSTEM_DESIGN, PLANNING, TASKS, ENGINEERING_DECISIONS, MUST_DO_CHECKS, CHANGELOG), diagrams rendered in `docs/assets/`.
- `pyproject.toml` (metadata + dependency groups), `settings.py` (Pydantic Settings), `.env`/`.env.example`.
- CI pipeline (lint, type-check, tests, dead-code, security, docs), pre-commit, Dockerfile, docker-compose.
- CLI skeleton (`spd`) + module scaffold under `src/`.

**Gate 0:** docs build clean (`mkdocs build --strict`); CI skeleton green; `spd --help` works.

---

## 4. Phase-by-Phase Plan

### PHASE 1 - Embedding layer (model-agnostic)

**Goal:** decode + preprocess images and extract L2-normalized embeddings through a swappable `Embedder` port.

**Deliverables**
- `core/ports.py` (`Embedder`, `SimilarityScorer`, `OutlierDetector`, `ResultWriter`) + entities + output-schema models (Pydantic).
- `io/dataset_loader.py` (discovery + decode, corrupt-image policy), `io/embedding_cache.py` (content-addressed).
- `embedding/dino_v2_embedder.py` (default), `embedding/clip_embedder.py` (alternate), preprocessing + L2-normalization, batched inference, `create_embedder` factory.

**Tests:** loader discovery/order-independence/corrupt handling; cache key derivation + hit/miss/transparency; embedder contract (normalized, right dim, deterministic); factory dispatch.

**Gate 1:** embeddings for a sample outlet are L2-normalized, 384-dim, and deterministic across two runs; cache cold vs warm identical.

---

### PHASE 2 - Scoring (similarity + signals)

**Goal:** per-outlet cosine similarity and the three suspicion signals.

**Deliverables**
- `scoring/similarity.py` (cosine matrix), `scoring/centroid.py` (coordinate-wise median, re-normalized), `scoring/knn.py` (top-k mean similarity), `scoring/fusion.py` (weighted fusion, clamping).
- Config for `k_neighbors`, fusion weights.

**Tests:** cosine symmetry/range; centroid robustness (median vs mean under injected outliers); kNN on synthetic clusters; fusion weights + `[0,1]` clamp.

**Gate 2:** all signals computed correctly on synthetic fixtures; fusion bounded in `[0,1]`.

---

### PHASE 3 - Detection (ensemble + threshold + reasons)

**Goal:** flag outliers with an adaptive threshold and human-readable reasons.

**Deliverables**
- `detection/ensemble_detector.py` (centroid/kNN/IF fusion, ED-4), `detection/isolation_forest.py` (seeded, deterministic), `detection/threshold.py` (MAD + floor, ED-5), `detection/reasons.py` (templates), `create_detector` factory.
- Config for `mad_k`, `score_floor`, `min_images_per_outlet`.

**Tests:** threshold math (MAD + floor); small-outlet (N<2) empty flags; uniform-outlet no-flag; injected single-fake flagged with correct reason; multi-cluster non-flag; determinism with seed.

**Gate 3:** synthetic golden set - a single unrelated image injected into a consistent outlet is flagged with the correct reason and a high score; a legitimate second cluster is not flagged.

---

### PHASE 4 - Pipeline + CLI + output

**Goal:** runnable end-to-end pipeline producing schema-validated JSON + CSV for every outlet.

**Deliverables**
- `pipeline/runner.py` (orchestration + timing + run summary), `pipeline/stage.py` (Template Method stage lifecycle).
- `io/result_writer.py` (JSON + CSV), `reporting/write_up.py` (one-page report), `reporting/summary.py` (run_summary.json).
- `cli/app.py` (`spd run|embed|detect|report`), exit codes, `--config/--model/--device/--seed`.

**Tests:** end-to-end fixture run (JSON/CSV round-trip, ranking completeness, empty-flag outlet present, every outlet exactly once); subcommand independence; schema forbid-extra.

**Gate 4:** `spd run` on the full dataset produces `results.json` + `results.csv` with 159 outlets, `suspicion_score` in `[0,1]`, and valid reasons.

---

### PHASE 5 - Validation, write-up, hardening

**Goal:** prove quality, reproducibility, and ship the write-up.

**Deliverables**
- Synthetic-golden evaluation (precision/recall/F1) + a `results/evaluation.md`.
- Determinism + cache-transparency regression tests.
- One-page write-up (`results/write_up.md`): rationale, trade-offs, scalability, limitations.
- Full-dataset run + a short qualitative review of sampled flags.
- Dockerfile/docker-compose polish; final alignment + verify gates.

**Gate 5 (release):** all FRs demonstrable; all CI + coverage + security gates green; write-up and full results produced; reproducibility proven (two identical runs).

---

## 5. Workstream Timeline (Gantt-style)

| Activity | P0 | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|---|
| Foundations (docs/config/CI/CLI) | ██ | | | | | |
| Embedding layer + cache | | ██ | | | | |
| Scoring (cosine/centroid/kNN) | | | ██ | | | |
| Detection (ensemble/threshold/reasons) | | | | ██ | | |
| Pipeline + CLI + output | | | | | ██ | |
| Validation + write-up + hardening | | | | | | ██ |
| **Phase gates** | G0 | G1 | G2 | G3 | G4 | G5 |

**2-day delivery schedule:** Day 1 = Phases 0-2 (gates G0-G2); Day 2 = Phases 3-5 (gates G3-G5). Gates are lightweight checkpoints at the end of each phase: a gate is only "open" if lint, type-check, tests, and coverage pass for that phase's deliverables; otherwise the phase's fixes are the next task. Defect fixes interleave continuously from Phase 1.

---

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| False positives on legitimate multi-cluster outlets (front vs interior) | Low precision, low trust | kNN local-density signal (ED-10); synthetic multi-cluster tests; qualitative review |
| False negatives on a tight clique of fakes | Missed fraud | Isolation Forest + centroid signals catch cliques; ensemble over single metric |
| Small-outlet instability (N≈2-5) | Noisy scores | `min_images_per_outlet` guard; absolute score floor; Isolation Forest de-emphasized at low N |
| Over-flagging near-uniform outlets | Noise-level flags | Absolute `score_floor`; MAD robustness |
| Model/weight drift breaking reproducibility | Non-deterministic output | Content-addressed cache keyed by model+version; pinned deps; determinism tests |
| Slow cold run (no GPU) | Wall-clock | Batched CPU inference; cache makes re-runs free; small model (ViT-S/14) |
| Compressed 2-day timeline | Phase slippage compounds | Fixed day split (§5): Day 1 must close G0-G2 before Day 2 starts; any unfinished Phase 0-2 work is descoped, not deferred (see §7); CI gates run per commit, so a red gate is caught within minutes, not at phase end |

---

## 7. Delivery Approach Notes

- **Stage isolation (ARCHITECTURE §4):** each stage is independently testable and re-runnable; the embedding cache makes `detect`/`report` re-runs near-instant.
- **Reproducibility is a feature, not an afterthought:** seed, sort, and cache are designed in from Phase 1, not bolted on.
- **The write-up is a first-class deliverable (FR9):** it is generated from the run summary + a fixed rationale template, and its content is grounded in the measured evaluation, never hand-waved.
- **Day checkpoints:** at the close of Day 1 (after G2) and Day 2 (after G4), verify reproducibility (two identical runs, cold vs warm cache) and schema validity before proceeding; a checkpoint failure stops new work until fixed. Release (G5) is only declared after the full release checklist (§8).

---

## 8. Definition of Done - Release Checklist

- [ ] All FR1-FR10 implemented and verified (traceability matrix, SPEC §24).
- [ ] Unit/integration/property tests green; coverage ≥ 85% core / ≥ 80% overall.
- [ ] Lint, type-check, dead-code, dependency/container scans green.
- [ ] Output validated against the SPEC §6.1 schema for all 159 outlets.
- [ ] Reproducibility proven (two identical runs; cold vs warm cache identical).
- [ ] Synthetic-golden precision/recall/F1 recorded in `results/evaluation.md`.
- [ ] One-page write-up produced (`results/write_up.md`).
- [ ] `docs/CHANGELOG.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md` current.
- [ ] Alignment + verify gates (`.agents/skills/coding-rules/verify-alignment/SKILL.md`) passed.

---

## 9. Out of Scope for This Plan

- Web service / REST API / database / background daemon (SPEC §2.2, ED-8).
- Model training or fine-tuning (pretrained features only).
- Timestamp/EXIF-based logic (explicitly excluded by the PRD).
- Active-learning / human-in-the-loop review queue (future phase, SPEC §2.3).
